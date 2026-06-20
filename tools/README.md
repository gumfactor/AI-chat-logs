# tools/

Python scripts for indexing and searching session transcripts. No third-party packages required — only the Python 3 standard library (`sqlite3`, `os`, `sys`). The optional `PyYAML` package is used automatically if installed, but the scripts fall back to a built-in YAML parser if it is not.

---

## `index.py` — Build the search index

Walks the `sessions/` directory recursively and upserts every `.md` file it finds into a SQLite FTS5 database at `index/sessions.db`. Metadata (session ID, date, agent, model, repo, status, platform URL) is read from each session's `metadata.yaml`.

**Prerequisites:** Python 3.7+. No pip installs needed.

**Usage:**

```bash
python tools/index.py
```

**Sample output:**

```
[indexed] TASK-20260620-0001 (2 files)

Done. 1 session(s), 2 file(s) indexed into /path/to/AI-chat-logs/index/sessions.db
```

**Re-running is safe.** The indexer upserts session rows on each run, so running it multiple times produces no duplicates. It also purges rows for any session folders that have been deleted from disk, printing `[purged] TASK-ID` for each one removed. Run it after every new session commit.

---

## `search.py` — Search the index

Queries the FTS5 full-text index and prints matching sessions with context snippets.

**Prerequisites:** Python 3.7+. No pip installs needed. Run `index.py` first.

**Usage:**

```bash
# Basic full-text search
python tools/search.py "authentication flow"

# Search within a specific session
python tools/search.py "audit" --session TASK-20260620-0001

# Show help
python tools/search.py --help
```

**Sample output:**

```
Search results for: "audit"  [session: TASK-20260620-0001]
==========================================================

[1] TASK-20260620-0001
    Date     : 2026-06-20
    Agent    : chatgpt
    Repo     : gumfactor/AI-chat-logs
    File     : summary.md
    Context  : ...1. **A private >>>audit<<< repo** (`AI-chat-logs`) holds all conversation transcripts as version-controlled...

[2] TASK-20260620-0001
    Date     : 2026-06-20
    Agent    : chatgpt
    Repo     : gumfactor/AI-chat-logs
    File     : transcript.md
    Context  : ...This makes every merged PR a navigable >>>audit<<< record.
```

**If the index does not exist**, the script prints a helpful error:

```
Error: index not found at .../index/sessions.db
Run `python tools/index.py` first to build the search index.
```

---

## How often to re-run the indexer

Run `python tools/index.py` after each new session folder is committed. It is fast (seconds, not minutes) even with hundreds of sessions, and running it multiple times is always safe.

A git post-commit hook or a simple cron job can automate this. See Phase 4 of `Plan.md` for planned automation options.

---

## `capture.py` — Capture a session transcript

Creates the full session folder structure from a raw transcript (file or stdin). Automatically assigns the next available Task ID for today, writes `transcript.md`, `metadata.yaml`, and a blank `summary.md`.

**Prerequisites:** Python 3.7+. No pip installs needed.

**Usage:**

```bash
# From a file
python tools/capture.py --file /path/to/transcript.txt

# From stdin — pipe text directly
echo "my transcript" | python tools/capture.py --agent claude

# From stdin — interactive paste (press Ctrl-D when done)
python tools/capture.py

# With pre-filled metadata
python tools/capture.py \
    --file /path/to/transcript.txt \
    --agent claude \
    --model claude-sonnet-4-6 \
    --repo gumfactor/my-project \
    --platform-url "https://claude.ai/chat/abc-123-uuid"

# Also run the indexer automatically after capture
python tools/capture.py --file transcript.txt --index
```

**Options:**

| Flag | Description |
|---|---|
| `--file PATH` | Read transcript from a file. If omitted, reads from stdin. |
| `--agent NAME` | Agent name: `claude`, `codex`, `gemini`, `chatgpt`, etc. |
| `--model MODEL` | Model string: `claude-sonnet-4-6`, `o4-mini`, etc. |
| `--repo ORG/REPO` | Repository the session worked on (e.g. `gumfactor/my-project`). |
| `--platform-url URL` | Canonical URL of the original chat (copy from browser address bar). |
| `--index` | Run `tools/index.py` automatically after capture (default: off). |

**Sample output:**

```
Session captured successfully.
  Task ID : TASK-20260620-0002
  Folder  : /path/to/AI-chat-logs/sessions/2026/2026-06-20/TASK-20260620-0002

  Files created:
    .../sessions/2026/2026-06-20/TASK-20260620-0002/transcript.md
    .../sessions/2026/2026-06-20/TASK-20260620-0002/metadata.yaml
    .../sessions/2026/2026-06-20/TASK-20260620-0002/summary.md
```

**What to do after capture:**

1. Open `metadata.yaml` and fill in any missing fields (`timestamp_end`, `branch`, `platform_url` if not provided).
2. After the session's PR is merged, update `metadata.yaml` with commit SHAs and the PR URL, and set `status: merged`.
3. Write the `summary.md` — including the **Self-Audit** section required by `AGENTS.md`.
4. Commit: `[TASK-ID] capture session transcript`.
