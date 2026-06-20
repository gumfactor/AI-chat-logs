# Worklog

Running log of work done on this system. Most recent entry first.

---

## 2026-06-20 — Phase 4: Semi-Automatic Capture

Built `tools/capture.py` — a CLI script that creates the full session folder structure from a raw transcript (file or stdin), eliminating the manual folder-creation and template-copying steps.

- Created `tools/capture.py` — reads a transcript from `--file` or stdin; generates the next available `TASK-YYYYMMDD-NNNN` ID for today; creates `sessions/YYYY/YYYY-MM-DD/TASK-ID/`; writes `transcript.md` (with header block), `metadata.yaml` (all known fields filled, unknowns set to `null`), and a blank `summary.md` template. Optional `--index` flag runs the indexer automatically. Handles: missing sessions/ dir, ID increment from existing sessions, empty transcript error, collision guard.
- Updated `tools/README.md` — added full `capture.py` section with usage examples, options table, sample output, and post-capture workflow.

All tests passed:
1. Basic capture from file — session folder created, all three files present, metadata.yaml valid YAML, summary.md is blank template.
2. Task ID increment — second capture on same date produced NNNN+1 (0003 after 0002).
3. Empty transcript — exited with clear error message, no folder created.
4. Stdin mode (`echo "..." | python tools/capture.py`) — worked correctly.
5. `--index` flag — indexer ran automatically after capture, printed session count.

Phase 4 acceptance criterion: a session can be captured in under 60 seconds with no manual text copying. Criterion met — one command with `--file` or a pipe from stdin.

---

## 2026-06-20 — Phase 3: Searchable Index

Built the SQLite FTS5 search tooling so all captured transcripts are queryable by keyword, topic, or session.

- Created `tools/index.py` — walks `sessions/` recursively; reads each session's `metadata.yaml`; upserts all `.md` files into two SQLite tables: `transcripts` (FTS5 full-text) and `session_meta` (structured metadata). Idempotent: safe to re-run after every commit. Prints one `[indexed]` line per session.
- Created `tools/search.py` — queries the FTS5 index and prints session ID, date, agent, repo, filename, and a context snippet (~200 chars) for each match. Supports `--session` filter to restrict search to a specific session. Prints a clear error if the index has not been built yet.
- Created `tools/README.md` — documents both scripts: what they do, prerequisites (Python 3 standard library only), usage examples, and re-run guidance.
- Removed `tools/.gitkeep` placeholder (now that real files live in `tools/`).

All tests passed:
1. `python tools/index.py` — completed, printed `[indexed] TASK-20260620-0001 (2 files)`.
2. `python tools/search.py "audit"` — returned 2 matching results with snippets.
3. `python tools/search.py "nonexistent_term_xyz"` — printed "No results found."
4. `python tools/search.py "audit" --session TASK-20260620-0001` — filtered results correctly.
5. Missing-db error — printed helpful message directing user to run index.py first.
6. Idempotency — running indexer twice produces exactly 2 transcript rows and 1 metadata row (no duplicates).

Phase 3 acceptance criterion: `python tools/search.py "auth flow"` returns all sessions that discussed authentication. Verified.

---

## 2026-06-20 — Phase 2: GitHub Integration

Linked every conversation to the GitHub work it produces.

- Created `.github/PULL_REQUEST_TEMPLATE.md` — GitHub auto-uses this as the default PR body for all PRs in this repo; matches the canonical template with GitHub-specific formatting
- Updated `templates/pr-template.md` — fixed "agent-history" reference (old name), added help text for Agent/Model fields and Files Changed, aligned with Plan.md spec
- Created `AGENTS.md` — instructs any agent working on this repo: task ID convention, branch naming, commit message format, metadata.yaml guidance, self-audit requirement, immutability rule, merge rule, post-merge metadata update
- Created `CLAUDE.md` — Claude Code loads this automatically; short pointer to `AGENTS.md` (Claude Code looks for `CLAUDE.md`, not `AGENTS.md`)
- Created `docs/github-project-board.md` — step-by-step setup guide for the GitHub Projects board; the board itself must be created manually via GitHub UI
- Updated `README.md` — added `AGENTS.md`, `CLAUDE.md`, `docs/`, `.github/PULL_REQUEST_TEMPLATE.md`, and `questions-for-Matt.md` to the file table
- Appended two items to `questions-for-Matt.md`: Q6 (GitHub Project board requires manual UI creation) and Q7 (PR template propagation to other project repos)

Phase 2 acceptance criterion: given any merged PR, you can navigate to the full transcript in under 30 seconds (via Task ID in PR → transcript folder in this repo).

---

## 2026-06-20

**Bootstrapped the repo.**

Genesis conversation with ChatGPT established the core problem: chat logs are the actual intellectual record of agent-assisted development, not summaries or PRs. Decided to treat conversations as version-controlled objects.

- Created `Vision.md` — goals, constraints, success criteria
- Created `Plan.md` — five-phase implementation plan
- Created `README.md`, `WORKLOG.md`, `CHANGELOG.md`

Phase 1 (manual capture) not yet started. No sessions captured yet.

---
