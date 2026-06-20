# Hook Setup: Automatic Session Initialization

This guide wires `tools/session_init.py` into Claude Code and Codex so that
every new chat automatically receives a Task ID before the agent sees your
first message.

What the hook does:
- Assigns the next `TASK-YYYYMMDD-NNNN` for today
- Creates `sessions/YYYY/YYYY-MM-DD/TASK-ID/metadata.yaml` with a pre-filled stub
- Captures: platform session ID, start timestamp, model (when available in payload)
- Injects the Task ID into the agent's system context so it uses it from the first commit

---

## Prerequisites

- Python 3.7+
- This repo cloned somewhere permanent on your machine (the hook script must be reachable at a fixed path)
- Note the absolute path to this repo — you'll paste it into config files below

---

## Claude Code

Claude Code hooks are configured in `~/.claude/settings.json`.

**Step 1 — Locate or create the file:**

```bash
# macOS / Linux
mkdir -p ~/.claude
touch ~/.claude/settings.json
```

**Step 2 — Add the `UserPromptSubmit` hook:**

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

**Step 3 — If you know your default model, pin it:**

```json
"command": "python3 /ABSOLUTE/PATH/TO/AI-chat-logs/tools/session_init.py --agent claude --model claude-sonnet-4-6"
```

If you leave `--model` out, the script tries to read it from the hook payload or from
`$ANTHROPIC_MODEL` / `$CLAUDE_MODEL` environment variables. If none of those are set,
`model` is left blank in the stub (fill it in manually after the session).

**Step 4 — Test the hook:**

Open a new Claude Code session, send any message, and then check:

```bash
ls sessions/$(date +%Y)/$(date +%Y-%m-%d)/
```

You should see a `TASK-<today>-NNNN/` folder. Open its `metadata.yaml` to confirm
`platform_session_id` and `timestamp_start` were captured.

**Why `UserPromptSubmit` and not `SessionStart`?**

Claude Code's `UserPromptSubmit` hook fires when you press Enter on any prompt.
The script uses a temp-file lock (keyed on `platform_session_id`) so it only
initializes once per session — subsequent prompts are a no-op. If Claude Code
adds a dedicated `SessionStart` hook in a future release, prefer that instead.

---

## Codex (CLI and VS Code / Cursor / Windsurf extension)

Codex uses `~/.codex/config.toml`. The VS Code extension reads the same file.

**Step 1 — Locate or create the file:**

```bash
mkdir -p ~/.codex
touch ~/.codex/config.toml
```

**Step 2 — Add the `session_start` hook:**

```toml
[hooks]
session_start = "python3 /ABSOLUTE/PATH/TO/AI-chat-logs/tools/session_init.py --agent codex"
```

Replace the path, optionally add `--model o4-mini` (or your default model).

**Step 3 — Test the hook:**

Open a new Codex session and check `sessions/` as above.

**Note on Codex injection format:**

`session_init.py` outputs `{"additionalSystemPrompt": "..."}` to stdout. Verify
that this field name is correct for your Codex version — the Codex hooks API may
use a different key. If the Task ID does not appear in the agent's context after
setup, check Codex hooks documentation for the correct injection field name and
open an issue or update the script.

---

## What gets written

`session_init.py` creates this file at hook time:

```
sessions/YYYY/YYYY-MM-DD/TASK-ID/
└── metadata.yaml     ← stub with what's known at session start
```

The stub contains:
- `session_id`: the assigned Task ID (`TASK-YYYYMMDD-NNNN`)
- `platform_session_id`: the platform's native session UUID or thread ID
- `platform_url`: best-effort constructed URL (verify and correct if needed)
- `timestamp_start`: UTC timestamp when the hook fired
- `agent` / `model`: from `--agent` flag and payload or env vars
- Everything else (`repo`, `branch`, `commits`, etc.) is `null` — fill in after the session

---

## Capturing the transcript after the session ends

Because the hook pre-created the metadata stub, pass `--task-id` to `capture.py`
so it uses the same Task ID and does not overwrite the hook-written metadata:

```bash
python tools/capture.py \
  --task-id TASK-20260620-0003 \
  --file /path/to/transcript.txt \
  --repo gumfactor/my-project
```

`capture.py` will:
1. Write `transcript.md` into the existing session folder
2. Create a blank `summary.md` if one doesn't exist
3. Leave `metadata.yaml` untouched (it already has `platform_session_id` and `timestamp_start`)

After capture, fill in the remaining fields in `metadata.yaml`:
- `repo`, `branch`, `model` (if blank)
- `commits`, `prs` (after the PR merges)
- `timestamp_end`, `status`

---

## Troubleshooting

**Hook fires but no folder appears**

- Check the absolute path in your config — a wrong path fails silently
- Run the script manually with a test payload:
  ```bash
  echo '{"session_id": "test-session-001"}' | \
    python3 tools/session_init.py --agent claude --dry-run
  ```

**Task ID does not appear in the agent's context**

- The metadata stub is created, but injection into the model's context requires
  the platform to honour the hook's stdout JSON
- Verify the `additionalSystemPrompt` field name against current Claude Code / Codex docs
- As a fallback, read the Task ID from `metadata.yaml` and paste it to the agent manually

**Every session gets a new Task ID even after the session restarts**

- The state file lives in `/tmp/ai-chat-logs-sessions/` and is cleared on reboot
- If a session spans a reboot, re-initialization will assign a new Task ID
- This is acceptable for solo use; for long-running sessions, record the Task ID
  from `metadata.yaml` before rebooting and use `--task-id` at capture time

**Multiple concurrent sessions**

- Each session gets its own `platform_session_id`, so they get distinct Task IDs
- `next_task_id()` scans the filesystem — if two sessions start simultaneously
  they could get the same ID. In practice this is unlikely in solo use; the
  folder-creation step acts as a natural collision guard.

---

## Environment variables recognised by `session_init.py`

| Variable | Description |
|---|---|
| `ANTHROPIC_MODEL` | Model name (e.g. `claude-sonnet-4-6`) |
| `CLAUDE_MODEL` | Alternative model name variable |
| `OPENAI_MODEL` | Model name for Codex sessions (e.g. `o4-mini`) |

These are checked only when `--model` is not passed and the hook payload does not
include a `model` field.
