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

---

## Codex (CLI and VS Code / Cursor / Windsurf extension)

Codex hooks are configured in `~/.codex/config.toml`. The VS Code, Cursor,
and Windsurf extensions all read the same file.

**⚠️ Important:** Configure hooks in `~/.codex/config.toml` (user-level), not in
a repo-local `.codex/config.toml`. A confirmed bug in Codex causes repo-local
hook configuration to be loaded for general project settings but **not** trigger
hook execution in interactive sessions.
([openai/codex#17532](https://github.com/openai/codex/issues/17532))

**Step 1 — Locate or create the file:**

```bash
mkdir -p ~/.codex
touch ~/.codex/config.toml
```

**Step 2 — Add the `SessionStart` hook:**

```toml
[[hooks.SessionStart]]
matcher = "*"

[[hooks.SessionStart.hooks]]
type = "command"
command = ["python3", "/ABSOLUTE/PATH/TO/AI-chat-logs/tools/session_init.py", "--agent", "codex"]
statusMessage = "Initializing session..."
```

Replace `/ABSOLUTE/PATH/TO/AI-chat-logs`. To pin a model:

```toml
command = ["python3", "/ABSOLUTE/PATH/TO/.../session_init.py", "--agent", "codex", "--model", "o4-mini"]
```

**Step 3 — Test:**

Open a new Codex session and check `sessions/` as above.

**Note on the `matcher` field for `SessionStart`:**

Setting `matcher = "*"` fires the hook on every session start (both new and
resumed sessions). You can restrict to new sessions only with `matcher = "startup"`.
Use `matcher = "resume"` to run only on resumed sessions. Most users want `"*"`.

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
platform_session_id: "session_abc123def456"
platform_url: "https://claude.ai/code/session_abc123def456"
timestamp_start: "2026-06-20T14:32:00Z"
timestamp_end: null
repo: null                    # fill in after session
branch: null                  # fill in after session
agent: "claude"
model: "claude-sonnet-4-6"
status: open
# ... remaining fields at null/empty defaults
```

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
# Claude Code simulation
echo '{"session_id": "test-abc-123", "hook_event_name": "UserPromptSubmit", "prompt": "hello"}' | \
  python3 tools/session_init.py --agent claude --dry-run

# Codex simulation
echo '{"session_id": "test-xyz-789"}' | \
  python3 tools/session_init.py --agent codex --dry-run
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
