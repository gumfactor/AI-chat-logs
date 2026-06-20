# tools/

Python scripts for indexing and searching session transcripts. No third-party packages required — only the Python 3 standard library (`sqlite3`, `os`, `sys`). The optional `PyYAML` package is used automatically if installed, but the scripts fall back to a built-in YAML parser if it is not.

---

## `index.py` — Build the search index

Walks the `sessions/` directory recursively and upserts every `.md` file it finds into a SQLite FTS5 database at `index/sessions.db`. Metadata (session ID, date, agent, model, repo, status, platform URL) is read from each session's `metadata.yaml`.

**Prerequisites:** Python 3.6+. No pip installs needed.

**Usage:**

```bash
python tools/index.py
```

**Sample output:**

```
[indexed] TASK-20260620-0001 (2 files)

Done. 1 session(s), 2 file(s) indexed into /path/to/AI-chat-logs/index/sessions.db
```

**Re-running is safe.** The indexer deletes existing rows for each session before re-inserting, so running it multiple times produces no duplicates. Run it after every new session commit.

---

## `search.py` — Search the index

Queries the FTS5 full-text index and prints matching sessions with context snippets.

**Prerequisites:** Python 3.6+. No pip installs needed. Run `index.py` first.

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
Search results for: "audit"
============================

[1] TASK-20260620-0001
    Date     : 2026-06-20
    Agent    : chatgpt
    Repo     : gumfactor/AI-chat-logs
    File     : transcript.md
    Context  : ...>>>audit<<<ability and replicability...
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
