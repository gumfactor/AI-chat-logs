#!/usr/bin/env python3
"""
tools/session_init.py — Session initialization hook for Claude Code and Codex.

Called by:
  Claude Code : UserPromptSubmit hook  (fires on every prompt; idempotent after first call)
  Codex       : session_start hook     (fires once per session)

On first invocation for a given platform session:
  1. Assigns the next TASK-YYYYMMDD-NNNN for today.
  2. Captures platform session ID, start timestamp, model (when available).
  3. Creates sessions/YYYY/YYYY-MM-DD/TASK-ID/metadata.yaml as a stub.
  4. Outputs JSON to inject the Task ID into the agent's system context.

On subsequent calls within the same session: no-op (state tracked in /tmp).

Hook payload arrives as JSON on stdin.

Claude Code UserPromptSubmit payload (known fields):
  session_id, transcript_path, cwd, hook_event_name, prompt

Codex session_start payload (known fields):
  session_id (or thread_id), model

Output JSON (stdout):
  Claude Code (UserPromptSubmit):
    {
      "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "Your Task ID for this session is TASK-..."
      }
    }

  Codex (SessionStart):
    {
      "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "Your Task ID for this session is TASK-..."
      }
    }

  The hookEventName is inferred from --agent (claude → UserPromptSubmit,
  codex → SessionStart). Override with --hook-event if needed.

  Confirmed working: additionalContext is supported by SessionStart and
  UserPromptSubmit in both platforms (as of 2026-06). PreToolUse and
  Stop do NOT support additionalContext.

Usage (in hook configuration):
  python3 /path/to/AI-chat-logs/tools/session_init.py --agent claude
  python3 /path/to/AI-chat-logs/tools/session_init.py --agent codex

Options:
  --agent NAME        Agent name to record: claude, codex, etc. (default: "")
  --model MODEL       Model override (e.g. claude-sonnet-4-6). Inferred from
                      payload or environment variables when not given.
  --hook-event NAME   Override the hookEventName in output JSON. Defaults to
                      "UserPromptSubmit" for claude, "SessionStart" for codex.
  --dry-run           Print what would happen without writing any files.

See docs/hooks-setup.md for full configuration instructions.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(REPO_ROOT, "sessions")

# Temp directory for session state (persists across prompts within a session)
STATE_DIR = os.path.join("/tmp", "ai-chat-logs-sessions")


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def today_compact():
    """YYYYMMDD for use in task IDs."""
    return datetime.now().strftime("%Y%m%d")


def today_str():
    """YYYY-MM-DD for folder names."""
    return datetime.now().strftime("%Y-%m-%d")


def today_year():
    return datetime.now().strftime("%Y")


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Task ID generation (mirrors capture.py logic)
# ---------------------------------------------------------------------------

def next_task_id(date_compact: str) -> str:
    """Scan sessions/ for existing TASK-<date>-NNNN folders and return the next one."""
    pattern = re.compile(r"^TASK-" + re.escape(date_compact) + r"-(\d{4})$")
    highest = 0
    year = date_compact[:4]
    date_dir = f"{year}-{date_compact[4:6]}-{date_compact[6:]}"
    base = os.path.join(SESSIONS_DIR, year, date_dir)
    if os.path.isdir(base):
        for entry in os.listdir(base):
            m = pattern.match(entry)
            if m:
                n = int(m.group(1))
                if n > highest:
                    highest = n
    return f"TASK-{date_compact}-{highest + 1:04d}"


# ---------------------------------------------------------------------------
# Session state tracking (idempotency)
# ---------------------------------------------------------------------------

def _safe_filename(platform_session_id: str) -> str:
    """Sanitize a session ID for use as a filename."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", platform_session_id)[:120]


def state_file_path(platform_session_id: str) -> str:
    os.makedirs(STATE_DIR, exist_ok=True)
    return os.path.join(STATE_DIR, f"{_safe_filename(platform_session_id)}.task")


def get_existing_task_id(platform_session_id: str):
    """Return the Task ID if this session was already initialized, else None."""
    p = state_file_path(platform_session_id)
    if os.path.exists(p):
        try:
            val = open(p, encoding="utf-8").read().strip()
            return val or None
        except OSError:
            return None
    return None


def record_task_id(platform_session_id: str, task_id: str):
    try:
        with open(state_file_path(platform_session_id), "w", encoding="utf-8") as f:
            f.write(task_id)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------

def yaml_str(val, fallback="null") -> str:
    if not val:
        return fallback
    escaped = str(val).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# ---------------------------------------------------------------------------
# Metadata stub
# ---------------------------------------------------------------------------

def build_platform_url(agent: str, platform_session_id: str) -> str:
    """
    Attempt to construct the canonical chat URL from the platform session ID.
    Returns empty string when the URL format is unknown.

    Claude Code remote sessions:  https://claude.ai/code/session_<id>
    Claude.ai web sessions:       https://claude.ai/chat/<uuid>
    Codex web sessions:           format not yet documented

    This is a best-effort heuristic. The user should verify and update
    metadata.yaml if the URL is incorrect.
    """
    if not platform_session_id:
        return ""
    if agent == "claude":
        # Remote session IDs typically start with "session_"
        if platform_session_id.startswith("session_"):
            return f"https://claude.ai/code/{platform_session_id}"
        # Short UUID-style: likely a Claude.ai web chat
        if re.match(r"^[0-9a-f]{8}-", platform_session_id):
            return f"https://claude.ai/chat/{platform_session_id}"
    # Codex or unknown: don't guess
    return ""


def write_metadata_stub(
    session_folder: str,
    task_id: str,
    platform_session_id: str,
    agent: str,
    model: str,
    timestamp_start: str,
    dry_run: bool = False,
):
    """Create sessions/YYYY/YYYY-MM-DD/TASK-ID/metadata.yaml with known fields."""
    platform_url = build_platform_url(agent, platform_session_id)

    content = f"""\
session_id: {task_id}
platform_session_id: {yaml_str(platform_session_id)}
platform_url: {yaml_str(platform_url)}         # verify and update if incorrect
timestamp_start: "{timestamp_start}"
timestamp_end: null
repo: null                                       # fill in: org/repo-name
branch: null                                     # fill in: agent/{task_id}-description
parent_session: null
forked_from: null
agent: {yaml_str(agent)}
model: {yaml_str(model)}                         # fill in if not captured automatically
orchestrator: false
subagent_sessions: []
files_touched: []
commits: []
prs: []
issues: []
status: open
"""

    if dry_run:
        print(f"[dry-run] Would create: {os.path.join(session_folder, 'metadata.yaml')}")
        print(content)
        return

    os.makedirs(session_folder, exist_ok=True)
    path = os.path.join(session_folder, "metadata.yaml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Injection output
# ---------------------------------------------------------------------------

def build_injection_text(task_id: str, timestamp: str) -> str:
    return (
        f"Your Task ID for this session is {task_id}.\n"
        f"Session started: {timestamp}.\n"
        f"Use {task_id} in:\n"
        f"  - Branch names: agent/{task_id}-short-description\n"
        f"  - Commit messages: [{task_id}] imperative description\n"
        f"  - PR title and body\n"
        f"  - metadata.yaml for this session\n"
        f"See AGENTS.md for the full convention."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Session initialization hook — assigns a Task ID and writes a metadata stub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--agent",
        default="",
        help="Agent name to record (e.g. claude, codex). Passed via hook config.",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Model override (e.g. claude-sonnet-4-6). Inferred from payload/env when omitted.",
    )
    parser.add_argument(
        "--hook-event",
        default="",
        help=(
            "Override the hookEventName in the output JSON. "
            "Defaults to 'UserPromptSubmit' for --agent claude, "
            "'SessionStart' for --agent codex."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing any files or state.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Read hook payload from stdin
    # ------------------------------------------------------------------
    payload: dict = {}
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                payload = json.loads(raw)
        except (json.JSONDecodeError, ValueError, OSError):
            pass

    # ------------------------------------------------------------------
    # 2. Extract platform session ID
    # Claude Code provides "session_id"; Codex may use "session_id" or "thread_id"
    # ------------------------------------------------------------------
    platform_session_id = (
        payload.get("session_id")
        or payload.get("thread_id")
        or payload.get("id")
        or ""
    ).strip()

    if not platform_session_id:
        # No session ID to key off — exit cleanly without creating anything.
        # This can happen if the hook fires outside a real session (e.g. in tests).
        sys.exit(0)

    # ------------------------------------------------------------------
    # 3. Idempotency: already initialized for this session?
    # ------------------------------------------------------------------
    if not args.dry_run:
        existing = get_existing_task_id(platform_session_id)
        if existing:
            # Silent no-op on subsequent prompts within the same session.
            sys.exit(0)

    # ------------------------------------------------------------------
    # 4. Resolve model
    # Priority: --model flag > payload > environment variables
    # ------------------------------------------------------------------
    model = args.model
    if not model:
        model = (
            payload.get("model")
            or os.environ.get("ANTHROPIC_MODEL", "")
            or os.environ.get("CLAUDE_MODEL", "")
            or os.environ.get("OPENAI_MODEL", "")
            or ""
        )

    agent = args.agent or payload.get("agent", "")
    timestamp_start = utc_now()
    date_compact = today_compact()
    date_str = today_str()
    year = today_year()

    # ------------------------------------------------------------------
    # 5. Generate Task ID
    # ------------------------------------------------------------------
    task_id = next_task_id(date_compact)
    session_folder = os.path.join(SESSIONS_DIR, year, date_str, task_id)

    # ------------------------------------------------------------------
    # 6. Write metadata stub
    # ------------------------------------------------------------------
    write_metadata_stub(
        session_folder=session_folder,
        task_id=task_id,
        platform_session_id=platform_session_id,
        agent=agent,
        model=model,
        timestamp_start=timestamp_start,
        dry_run=args.dry_run,
    )

    # ------------------------------------------------------------------
    # 7. Record state (prevents re-initialization on subsequent prompts)
    # ------------------------------------------------------------------
    if not args.dry_run:
        record_task_id(platform_session_id, task_id)

    # ------------------------------------------------------------------
    # 8. Output injection JSON
    # ------------------------------------------------------------------
    # Both Claude Code (UserPromptSubmit) and Codex (SessionStart) use the
    # same hookSpecificOutput.additionalContext structure.
    # Claude Code: hookEventName must be "UserPromptSubmit"
    # Codex:       hookEventName must be "SessionStart"
    if args.hook_event:
        hook_event_name = args.hook_event
    elif agent == "codex":
        hook_event_name = "SessionStart"
    else:
        hook_event_name = "UserPromptSubmit"

    injection_text = build_injection_text(task_id, timestamp_start)
    output = {
        "hookSpecificOutput": {
            "hookEventName": hook_event_name,
            "additionalContext": injection_text,
        }
    }
    print(json.dumps(output))

    if args.dry_run:
        print(f"\n[dry-run] Task ID would be: {task_id}", file=sys.stderr)
        print(f"[dry-run] Session folder: {session_folder}", file=sys.stderr)


if __name__ == "__main__":
    main()
