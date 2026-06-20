# Worklog

Running log of work done on this system. Most recent entry first.

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
