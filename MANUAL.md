# Manual: AI Chat Logs

How to use this system as the human operator. For agent-facing rules, see `AGENTS.md`.

---

## Core idea in one sentence

Before starting an AI agent session, assign it a Task ID. After the session, capture the transcript. Everything else flows from that.

---

## Starting a session

1. **Assign a Task ID** before opening the chat:
   ```
   TASK-YYYYMMDD-NNNN
   ```
   Example: `TASK-20260621-0001`. The NNNN counter starts at 0001 each day.

2. **Tell the agent the Task ID** at the start of the session so it uses it in branch names and commit messages.

3. **Open the chat** in Claude, Codex, or whichever platform you're using.

---

## Capturing a session after it ends

Copy the transcript to a file, then run:

```bash
python tools/capture.py \
  --file /path/to/transcript.txt \
  --agent claude \
  --model claude-sonnet-4-6 \
  --repo gumfactor/my-project \
  --platform-url "https://claude.ai/chat/abc-123"
```

Or pipe from stdin:

```bash
pbpaste | python tools/capture.py --agent claude --model claude-sonnet-4-6
```

The script:
- Auto-assigns the next available Task ID for today (or use `--task-id` to override)
- Creates `sessions/YYYY/YYYY-MM-DD/TASK-ID/` with `transcript.md`, `metadata.yaml`, and a blank `summary.md`
- Prints the folder path so you know where to find it

To also update the search index immediately:
```bash
python tools/capture.py --file transcript.txt --agent claude --index
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
| Capture a session | `python tools/capture.py --file transcript.txt --agent claude` |
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
