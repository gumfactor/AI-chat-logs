# Manual: AI Chat Logs

How to use this system as the human operator. For agent-facing rules, see `AGENTS.md`.

---

## Core idea in one sentence

Before starting an AI agent session, assign it a Task ID. After the session, capture the transcript. Everything else flows from that.

---

## One-time hook setup

Install the session-init hook once and Task IDs are assigned automatically every time you start a chat. See **`docs/hooks-setup.md`** for step-by-step configuration for Claude Code and Codex (CLI and VS Code / Cursor / Windsurf extension).

Without the hook, assign the Task ID manually (see Fallback below).

---

## Starting a session

### With the hook installed (normal path)

1. **Open the chat** in Claude Code or Codex — that's it.
2. The hook fires the moment you press Enter on your first message.
3. The hook assigns the next `TASK-YYYYMMDD-NNNN`, writes a `metadata.yaml` stub, and injects the Task ID into the agent's context before it responds.
4. The agent will know its Task ID and use it in branch names and commit messages automatically.

### Fallback (no hook, or hook failed)

1. Check `sessions/YYYY/YYYY-MM-DD/` for a stub folder from today — the Task ID is the folder name.
2. If none exists, assign one manually:
   ```
   TASK-YYYYMMDD-NNNN
   ```
   Example: `TASK-20260621-0001`. NNNN starts at 0001 each day.
3. Tell the agent the Task ID in your first message.

---

## Capturing a session after it ends

### When the hook was active (normal path)

The hook already created the session folder and `metadata.yaml` stub. Pass `--task-id` so `capture.py` uses the same Task ID and does not overwrite the hook-written metadata:

```bash
python tools/capture.py \
  --task-id TASK-20260620-0003 \
  --file /path/to/transcript.txt \
  --repo gumfactor/my-project
```

Or from stdin (e.g. paste from clipboard):

```bash
pbpaste | python tools/capture.py --task-id TASK-20260620-0003 --repo gumfactor/my-project
```

The Task ID is printed in the agent's first response (injected by the hook), and it's also the folder name under today's date in `sessions/`.

### When no hook was active (fallback)

```bash
python tools/capture.py \
  --file /path/to/transcript.txt \
  --agent claude \
  --model claude-sonnet-4-6 \
  --repo gumfactor/my-project \
  --platform-url "https://claude.ai/chat/abc-123"
```

The script auto-assigns the next available Task ID for today.

### To also update the search index immediately:

```bash
python tools/capture.py --task-id TASK-20260620-0003 --file transcript.txt --index
```

---

## After capture: fill in the gaps

Open the new session folder and:

1. **`metadata.yaml`** — fill in anything `capture.py` couldn't infer:
   - `branch` — the branch the agent worked on
   - `timestamp_end` — when the session ended
   - `platform_url` — the chat URL, if you have it (optional)

2. **`summary.md`** — write this yourself after the session closes:
   - What was accomplished
   - What remains open
   - Complete the Self-Audit section (required)

3. **After the PR merges** — update `metadata.yaml`:
   - Add commit SHAs to `commits:`
   - Add the PR URL to `prs:`
   - Set `status: merged`
   - Commit: `[TASK-ID] update metadata post-merge`

---

## Multi-agent sessions (supervisor + delegates)

When you run a supervisor that spawns subagents, each agent gets its own transcript file in the same session folder:

```
sessions/2026/2026-06-21/TASK-20260621-0001/
├── metadata.yaml
├── orchestrator.md      ← the supervisor's transcript
├── coder-agent.md       ← first subagent
├── reviewer-agent.md    ← second subagent
├── artifacts/
└── summary.md
```

In `metadata.yaml` for the orchestrator session:
```yaml
orchestrator: true
subagent_sessions:
  - TASK-20260621-0002
  - TASK-20260621-0003
```

In `metadata.yaml` for each subagent session:
```yaml
parent_session: TASK-20260621-0001
```

Capture each agent's transcript separately using `capture.py`, or paste them manually into the named files.

---

## Keeping the search index current

After committing new sessions:

```bash
python tools/index.py
```

This updates `index/sessions.db`. Run it any time — it's idempotent and fast.

---

## Searching your session history

```bash
# Search across all sessions
python tools/search.py "authentication flow"

# Search within a specific session
python tools/search.py "redis" --session TASK-20260620-0041

# Include sessions that have been deleted from disk
python tools/search.py "old topic" --include-deleted
```

Results show the session ID, date, agent, file, and a context snippet with the matched terms highlighted as `>>>term<<<`.

---

## Generating DAG diagrams

For any session that has subagents, generate a Mermaid diagram:

```bash
# All sessions
python tools/dag.py

# Rooted at a specific session
python tools/dag.py --root TASK-20260621-0001

# Write to a file
python tools/dag.py --root TASK-20260621-0001 --output /tmp/dag.md
```

To append the diagram to a session's `summary.md`:

```bash
python tools/generate_summary.py TASK-20260621-0001
```

This is idempotent — safe to run multiple times. If the session graph changed (new subagents added), use `--force` to replace the existing diagram:

```bash
python tools/generate_summary.py TASK-20260621-0001 --force
```

---

## Committing sessions

```bash
git add sessions/YYYY/YYYY-MM-DD/TASK-ID/
git commit -m "[TASK-ID] capture session transcript"
git push
```

---

## If a session was accidentally deleted

Sessions deleted from disk are **tombstoned**, not purged. Their index rows are preserved with `status: deleted`. They won't appear in search results by default but are still there:

```bash
python tools/search.py "topic" --include-deleted
```

To restore, recreate the session folder and re-run `python tools/index.py`.

---

## Quick reference

| Task | Command |
|---|---|
| Hook setup (one-time) | See `docs/hooks-setup.md` |
| Capture (hook was active) | `python tools/capture.py --task-id TASK-ID --file transcript.txt` |
| Capture (no hook) | `python tools/capture.py --file transcript.txt --agent claude` |
| Update index | `python tools/index.py` |
| Search | `python tools/search.py "query"` |
| Session-scoped search | `python tools/search.py "query" --session TASK-ID` |
| Generate DAG | `python tools/dag.py --root TASK-ID` |
| Append DAG to summary | `python tools/generate_summary.py TASK-ID` |
| Replace stale DAG | `python tools/generate_summary.py TASK-ID --force` |

---

## File layout

```
AI-chat-logs/
├── sessions/
│   └── YYYY/
│       └── YYYY-MM-DD/
│           └── TASK-ID/
│               ├── metadata.yaml      ← fill in after capture
│               ├── transcript.md      ← raw chat (immutable after commit)
│               ├── orchestrator.md    ← multi-agent: per-agent files
│               ├── agent-a.md
│               ├── artifacts/         ← generated files, diffs
│               └── summary.md         ← write this yourself
├── templates/
│   ├── metadata.yaml                  ← blank template
│   ├── transcript.md                  ← blank transcript template
│   └── summary.md                     ← blank summary template
├── tools/
│   ├── capture.py                     ← create session folders
│   ├── index.py                       ← build search index
│   ├── search.py                      ← search transcripts
│   ├── dag.py                         ← generate DAG diagrams
│   └── generate_summary.py            ← append DAG to summary.md
└── index/
    └── sessions.db                    ← SQLite index (gitignored)
```
