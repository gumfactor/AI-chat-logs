#!/usr/bin/env python3
"""
tools/capture.py — Capture a session transcript and create the standard folder structure.

Usage:
    # From a file
    python tools/capture.py --file /path/to/transcript.txt

    # From stdin (pipe or interactive paste + Ctrl-D)
    python tools/capture.py

    # With pre-filled metadata
    python tools/capture.py --agent claude --model claude-sonnet-4-6 \\
        --repo gumfactor/my-project \\
        --platform-url "https://claude.ai/chat/abc-123"

    # Auto-run the indexer after capture
    python tools/capture.py --file transcript.txt --index
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(REPO_ROOT, "sessions")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def today_str():
    """Return today's date as YYYY-MM-DD (local time)."""
    return datetime.now().strftime("%Y-%m-%d")


def today_compact():
    """Return today's date as YYYYMMDD for use in task IDs."""
    return datetime.now().strftime("%Y%m%d")


def today_year():
    """Return today's 4-digit year."""
    return datetime.now().strftime("%Y")


def next_task_id(date_compact: str) -> str:
    """
    Scan sessions/ for existing TASK-<date_compact>-NNNN folders and return
    the next available TASK-ID with NNNN incremented by one.

    If no sessions exist for today, returns TASK-<date_compact>-0001.
    """
    pattern = re.compile(r"^TASK-" + re.escape(date_compact) + r"-(\d{4})$")
    highest = 0

    year = date_compact[:4]
    date_dir_name = f"{year}-{date_compact[4:6]}-{date_compact[6:]}"
    candidate_dirs = [
        os.path.join(SESSIONS_DIR, year, date_dir_name),
    ]

    for base in candidate_dirs:
        if not os.path.isdir(base):
            continue
        for entry in os.listdir(base):
            m = pattern.match(entry)
            if m:
                n = int(m.group(1))
                if n > highest:
                    highest = n

    next_n = highest + 1
    return f"TASK-{date_compact}-{next_n:04d}"


def ensure_unique_task_id(task_id: str, session_folder: str) -> str:
    """
    If the session folder already exists (collision), keep incrementing
    the counter until we find one that doesn't exist.
    Solo-use guard — not expected to trigger in normal operation.
    """
    if not os.path.exists(session_folder):
        return task_id, session_folder

    # Parse out date_compact and current NNNN
    m = re.match(r"^(TASK-(\d{8})-)(\d{4})$", task_id)
    if not m:
        return task_id, session_folder  # can't parse — return as-is

    prefix = m.group(1)
    date_compact = m.group(2)
    n = int(m.group(3))
    year = date_compact[:4]
    date_dir_name = f"{year}-{date_compact[4:6]}-{date_compact[6:]}"
    date_session_dir = os.path.join(SESSIONS_DIR, year, date_dir_name)

    while True:
        n += 1
        task_id = f"{prefix}{n:04d}"
        session_folder = os.path.join(date_session_dir, task_id)
        if not os.path.exists(session_folder):
            return task_id, session_folder


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------

def yaml_str(val: str, fallback: str = "null") -> str:
    """
    Return a YAML-safe representation of a user-supplied string value.

    - Empty / None  → fallback (default "null")
    - Non-empty     → double-quoted string with internal double-quotes and
                      backslashes escaped.

    Quoting prevents two classes of silent corruption:
      1. Values containing colons (e.g. model names like "llama3:8b") which
         YAML would mis-parse as key–value separators.
      2. Reserved bare-word scalars (true, false, null, yes, no, on, off) that
         YAML would parse as the wrong type.
    """
    if not val:
        return fallback
    escaped = val.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_transcript(folder: str, task_id: str, agent: str, model: str,
                     date: str, repo: str, platform_url: str, content: str):
    """Write transcript.md into folder."""
    path = os.path.join(folder, "transcript.md")
    agent_display = agent if agent else ""
    model_display = model if model else ""
    repo_display = repo if repo else ""
    platform_display = platform_url if platform_url else ""

    header = f"""# Session: {task_id}

**Agent:** {agent_display}
**Model:** {model_display}
**Date:** {date}
**Repo:** {repo_display}
**Platform URL:** {platform_display}

---

## Transcript

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(content)
        f.write("\n")


def write_metadata(folder: str, task_id: str, agent: str, model: str,
                   date: str, repo: str, platform_url: str):
    """Write metadata.yaml into folder with known fields filled in."""
    path = os.path.join(folder, "metadata.yaml")

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Use yaml_str() for all user-supplied values so that colons, YAML
    # reserved words, and other special characters never corrupt the file.
    agent_val = yaml_str(agent)
    model_val = yaml_str(model)
    repo_val = yaml_str(repo)
    platform_val = yaml_str(platform_url)
    branch_val = f"agent/{task_id}-description"  # placeholder; user should update

    content = f"""session_id: {task_id}
platform_url: {platform_val}
timestamp_start: {now_iso}    # set at capture time; update with actual session start if known
timestamp_end: null            # fill in when session ends
repo: {repo_val}
branch: {branch_val}          # update with actual branch name
parent_session: null
forked_from: null
agent: {agent_val}
model: {model_val}
orchestrator: false
subagent_sessions: []
files_touched: []
commits: []
prs: []
issues: []
status: open
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_summary(folder: str, task_id: str):
    """Write a blank summary.md template."""
    path = os.path.join(folder, "summary.md")
    content = f"""# Summary: {task_id}

## What this session produced

<!-- Written after the session closes. What was accomplished, what remains open. -->

## What remains open

<!-- Open questions, deferred decisions, follow-up tasks. -->

## Status

<!-- open | returned | repair | merged | abandoned -->

---

## Self-Audit

**What did I change?**

**What did I not touch?**

**What could be wrong?**

**How did I test it?**

**What is unresolved?**
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Capture a session transcript and create the standard session folder structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/capture.py --file /path/to/transcript.txt
  python tools/capture.py --agent claude --model claude-sonnet-4-6 --repo gumfactor/proj
  echo "my transcript" | python tools/capture.py --agent claude
  python tools/capture.py --file transcript.txt --index
""",
    )
    parser.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Path to a file containing the transcript. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--agent",
        metavar="NAME",
        help="Agent name (e.g. claude, codex, gemini, chatgpt).",
    )
    parser.add_argument(
        "--model",
        metavar="MODEL",
        help="Model string (e.g. claude-sonnet-4-6, o4-mini).",
    )
    parser.add_argument(
        "--repo",
        metavar="ORG/REPO",
        help="Repository this session worked on (e.g. gumfactor/my-project).",
    )
    parser.add_argument(
        "--platform-url",
        metavar="URL",
        help="Canonical URL of the original chat (e.g. https://claude.ai/chat/abc-123).",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        default=False,
        help="Run the indexer (tools/index.py) automatically after capture.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Read transcript content
    # ------------------------------------------------------------------
    if args.file:
        file_path = args.file
        if not os.path.isfile(file_path):
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
        except OSError as e:
            print(f"Error: could not read file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("Paste your transcript below, then press Ctrl-D (or Ctrl-Z on Windows) when done:")
            print()
        try:
            raw_content = sys.stdin.read()
        except KeyboardInterrupt:
            print("\nAborted.", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Validate content
    # ------------------------------------------------------------------
    if not raw_content.strip():
        print("Error: transcript is empty. No session folder created.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Compute task ID and folder path
    # ------------------------------------------------------------------
    date_compact = today_compact()
    date_str = today_str()
    year = today_year()

    task_id = next_task_id(date_compact)

    date_dir = os.path.join(SESSIONS_DIR, year, date_str)
    session_folder = os.path.join(date_dir, task_id)

    # Collision guard (should not trigger in solo use)
    task_id, session_folder = ensure_unique_task_id(task_id, session_folder)

    # ------------------------------------------------------------------
    # 4. Create folder structure
    # ------------------------------------------------------------------
    os.makedirs(session_folder, exist_ok=True)

    # ------------------------------------------------------------------
    # 5. Write files
    # ------------------------------------------------------------------
    write_transcript(
        folder=session_folder,
        task_id=task_id,
        agent=args.agent or "",
        model=args.model or "",
        date=date_str,
        repo=args.repo or "",
        platform_url=args.platform_url or "",
        content=raw_content,
    )

    write_metadata(
        folder=session_folder,
        task_id=task_id,
        agent=args.agent or "",
        model=args.model or "",
        date=date_str,
        repo=args.repo or "",
        platform_url=args.platform_url or "",
    )

    write_summary(folder=session_folder, task_id=task_id)

    # ------------------------------------------------------------------
    # 6. Report
    # ------------------------------------------------------------------
    print(f"Session captured successfully.")
    print(f"  Task ID : {task_id}")
    print(f"  Folder  : {session_folder}")
    print()

    if not args.platform_url:
        print("  Note: --platform-url was not provided. Update metadata.yaml with the")
        print("        original chat URL when available.")
        print()

    print(f"  Files created:")
    print(f"    {os.path.join(session_folder, 'transcript.md')}")
    print(f"    {os.path.join(session_folder, 'metadata.yaml')}")
    print(f"    {os.path.join(session_folder, 'summary.md')}")

    # ------------------------------------------------------------------
    # 7. Optionally run indexer
    # ------------------------------------------------------------------
    if args.index:
        print()
        print("Running indexer...")
        indexer_path = os.path.join(REPO_ROOT, "tools", "index.py")
        result = subprocess.run(
            [sys.executable, indexer_path],
            capture_output=False,
        )
        if result.returncode != 0:
            print("Warning: indexer exited with a non-zero status.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
