# Hook Setup: Automatic Session Initialization

This guide wires `tools/session_init.py` into Claude Code and Codex so that
every new chat automatically receives a Task ID before the agent sees your
first message.

What the hook does:
- Assigns the next `TASK-YYYYMMDD-NNNN` for today
- Creates `sessions/YYYY/YYYY-MM-DD/TASK-ID/metadata.yaml` with a pre-filled stub
- Captures: platform session ID, start timestamp, model (when available in payload)
- Injects the Task ID into the agent's context via `hookSpecificOutput.additionalContext`

**Output format (both platforms):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Your Task ID for this session is TASK-20260620-0003. ..."
  }
}
```
`hookEventName` is `"UserPromptSubmit"` for Claude Code and `"SessionStart"` for Codex.
`additionalContext` is confirmed supported by both `UserPromptSubmit` and `SessionStart`
as of 2026-06. (`PreToolUse` and `Stop` do not support `additionalContext`.)

---

## Prerequisites

- Python 3.7+
- This repo cloned somewhere permanent on your machine (the hook script must be reachable at a fixed path)
- Note the absolute path to this repo — you'll paste it into config files below

---

## Claude Code

Claude Code hooks are configured in `~/.claude/settings.json`. The
`UserPromptSubmit` hook fires on every prompt; the script uses a temp-file
lock so initialization only runs once per session.

**Step 1 — Locate or create the file:**

```bash
mkdir -p ~/.claude
touch ~/.claude/settings.json
```

**Step 2 — Add the hook:**

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /ABSOLUTE/PATH/TO/AI-chat-logs/tools/session_init.py --agent claude"
          }
        ]
      }
    ]
  }
}
```

Replace `/ABSOLUTE/PATH/TO/AI-chat-logs` with the actual path on your machine.
If `settings.json` already has content, merge the `"hooks"` key — don't replace the whole file.

**Step 3 — Optionally pin your model:**

```
"command": "python3 /ABSOLUTE/PATH/TO/.../session_init.py --agent claude --model claude-sonnet-4-6"
```

If `--model` is omitted, the script reads from `$ANTHROPIC_MODEL` or `$CLAUDE_MODEL`
environment variables, then leaves `model` blank in the stub if neither is set.

**Step 4 — Test:**

Open a new Claude Code session, send any message, then check:

```bash
ls sessions/$(date +%Y)/$(date +%Y-%m-%d)/
cat sessions/$(date +%Y)/$(date +%Y-%m-%d)/TASK-*/metadata.yaml
```

You should see a `TASK-<today>-NNNN/` folder with `platform_session_id` and
`timestamp_start` already populated.

**Context compaction note:** Claude Code injects the Task ID via `additionalContext`
on the first prompt. If the conversation is later compacted (context summarised by
the platform), the injected text may not survive into the new context window. The
`metadata.yaml` stub is always written regardless, so the Task ID is durable — but
you may need to tell the agent its Task ID again after a compaction event (read it
from `sessions/YYYY/YYYY-MM-DD/TASK-*/metadata.yaml`). Codex's `SessionStart`
fires fresh on `compact` and `clear` events, so re-injection is automatic there.

---

## Codex (CLI and VS Code / Cursor / Windsurf extension)

Codex hooks are on by default. To disable them you would set `[features] hooks = false` — you don't need to enable them. (The old `codex_hooks = true` flag is a deprecated alias; ignore references to it.)

Hooks load from four locations in priority order:
1. `~/.codex/hooks.json` — user-level JSON
2. `~/.codex/config.toml` — user-level TOML
3. `<repo>/.codex/hooks.json` — project-level JSON (**requires project trust**)
4. `<repo>/.codex/config.toml` — project-level TOML (**requires project trust**)

**Use user-level config** (`~/.codex/`) for this hook. Project-level hooks require the project to be explicitly trusted and have a confirmed bug where they don't fire in interactive sessions ([openai/codex#17532](https://github.com/openai/codex/issues/17532)).

**Step 1 — Choose your config format:**

**Option A — `~/.codex/hooks.json` (JSON, mirrors Claude Code's shape):**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /ABSOLUTE/PATH/TO/AI-chat-logs/tools/session_init.py --agent codex",
            "statusMessage": "Initializing session..."
          }
        ]
      }
    ]
  }
}
```

**Option B — `~/.codex/config.toml` (TOML):**

```toml
[[hooks.SessionStart]]
matcher = "startup|resume|clear|compact"

[[hooks.SessionStart.hooks]]
type = "command"
command = "python3 /ABSOLUTE/PATH/TO/AI-chat-logs/tools/session_init.py --agent codex"
statusMessage = "Initializing session..."
```

Replace `/ABSOLUTE/PATH/TO/AI-chat-logs` with the actual path. To pin a model,
append ` --model o4-mini` to the `command` string.

**Step 2 — Test:**

Open a new Codex session and check `sessions/` as above.

**The `matcher` field for `SessionStart`:**

`matcher` is a pipe-separated string of `source` values from the hook payload:
- `"startup"` — fresh session (new `codex` invocation)
- `"resume"` — session resumed via `/resume` or `codex resume <id>`
- `"clear"` — conversation reset via `/clear` (same process, new thread; v0.120.0+)
- `"compact"` — session compacted (context summarised, thread continues)

`"startup|resume|clear|compact"` matches all four so a Task ID is always assigned.
The script's idempotency lock means that on `resume` or `compact`, if the session
was already initialized in this process's `/tmp` state, the call is a no-op and
returns the same Task ID.

---

## What gets written

`session_init.py` creates this at hook time:

```
sessions/YYYY/YYYY-MM-DD/TASK-ID/
└── metadata.yaml     ← stub with what's known at session start
```

Example stub (`metadata.yaml`):

```yaml
session_id: TASK-20260620-0003
platform_session_id: "00893aaf-19fa-41d2-8238-13269b9b3ca0"
platform_url: null            # fill in from browser address bar after session
timestamp_start: "2026-06-20T14:32:00Z"
timestamp_end: null
repo: null                    # fill in after session
branch: null                  # fill in after session
agent: "claude"
model: "claude-sonnet-4-6"
status: open
# ... remaining fields at null/empty defaults
```

**Platform session IDs:**

- **Codex**: the `session_id` in the hook payload IS Codex's own native session
  identifier — it's the same ID used internally to identify the session. Recorded
  as `platform_session_id` and useful for cross-referencing Codex's own logs.

- **Claude Code**: the `session_id` in the hook payload is an internal UUID
  (e.g. `00893aaf-19fa-41d2-8238-13269b9b3ca0`). This is NOT the token visible
  in the browser URL (`session_01HFdZEuQc2ckiY9GbSyqb6m`). The URL cannot be
  reconstructed from the payload — copy it from the browser and fill in
  `platform_url` in `metadata.yaml` after the session.

In both cases the hook captures whatever `session_id` the platform provides.
The `TASK-YYYYMMDD-NNNN` exists as a human-readable cross-platform reference
that works consistently regardless of what the underlying platform sends.

---

## Capturing the transcript after the session ends

Because the hook pre-created the metadata stub, pass `--task-id` to `capture.py`
so it reuses the same Task ID and does not overwrite the hook-written metadata:

```bash
python tools/capture.py \
  --task-id TASK-20260620-0003 \
  --file /path/to/transcript.txt \
  --repo gumfactor/my-project
```

The Task ID to pass is shown in the agent's first response (injected at session
start) and is also the folder name under today's date in `sessions/`.

---

## Manual test without a live session

```bash
# Claude Code simulation (UserPromptSubmit payload)
echo '{
  "session_id": "00893aaf-19fa-41d2-8238-13269b9b3ca0",
  "hook_event_name": "UserPromptSubmit",
  "transcript_path": "/Users/you/.claude/projects/.../00893aaf.jsonl",
  "cwd": "/Users/you/my-project",
  "prompt": "hello"
}' | python3 tools/session_init.py --agent claude --dry-run

# Codex simulation (SessionStart payload)
echo '{
  "session_id": "codex-session-abc123",
  "hook_event_name": "SessionStart",
  "source": "startup",
  "model": "o4-mini",
  "transcript_path": null,
  "cwd": "/Users/you/my-project"
}' | python3 tools/session_init.py --agent codex --dry-run
```

Both print the metadata that would be written and the JSON that would be output
to stdout, without touching the filesystem.

---

## Troubleshooting

**Hook fires but no session folder appears**
- Verify the absolute path in your config — a wrong path fails silently
- Run the dry-run test above to confirm the script is reachable

**Task ID does not appear in the agent's context**
- The metadata stub is created, but context injection requires the platform to
  honour the `hookSpecificOutput.additionalContext` field in the hook's stdout
- Verify your platform version supports this field (confirmed working in Claude
  Code and Codex as of 2026-06)
- As a fallback, read the Task ID from `metadata.yaml` and paste it to the agent

**Codex: hook fires on CLI but not in VS Code / Cursor / Windsurf**
- Confirm hooks are in `~/.codex/config.toml`, not a repo-local file
  (see the ⚠️ note above)

**Every session gets a new Task ID even after machine restart**
- State is tracked in `/tmp/ai-chat-logs-sessions/` and cleared on reboot
- If a session spans a reboot, read the Task ID from the session's `metadata.yaml`
  and pass it with `--task-id` when running `capture.py`

**Multiple concurrent sessions**
- Each gets its own `platform_session_id` → distinct Task IDs
- In solo use, simultaneous session starts are unlikely; the folder-create
  step acts as a natural collision guard

---

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_MODEL` | Model name for Claude sessions (e.g. `claude-sonnet-4-6`) |
| `CLAUDE_MODEL` | Alternative Claude model variable |
| `OPENAI_MODEL` | Model name for Codex sessions (e.g. `o4-mini`) |

Checked only when `--model` is not passed and the hook payload has no `model` field.
