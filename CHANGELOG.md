# Changelog

Tracks structural changes to this system: folder conventions, metadata schema updates, tooling decisions, and naming changes. Not a task log (see `WORKLOG.md`).

---

## 2026-06-20 — Phase 3: Searchable index tooling

- Added `tools/index.py` — SQLite FTS5 indexer; walks `sessions/` recursively; reads `metadata.yaml` per session; upserts `.md` files into `transcripts` (FTS5) and `session_meta` (relational) tables in `index/sessions.db`. Upsert strategy: delete-then-insert per session, so re-runs are idempotent.
- Added `tools/search.py` — FTS5 search CLI; prints session ID, date, agent, repo, filename, and context snippet per match; supports `--session` filter; prints helpful error if index is missing; supports `--help`.
- Added `tools/README.md` — usage documentation for both scripts; prerequisites, examples, re-run guidance.
- Removed `tools/.gitkeep` — replaced by real files.

## 2026-06-20 — Phase 2: GitHub integration files

- Added `.github/PULL_REQUEST_TEMPLATE.md` — GitHub-native PR template; auto-populates PR body with Task ID, transcript link, platform URL, agent/model, files changed, testing info, uncertainties, and follow-up tasks
- Updated `templates/pr-template.md` — corrected repo name reference from `agent-history` to `AI-chat-logs`; added instructional comments to all fields; aligned with Plan.md Phase 2 spec
- Added `AGENTS.md` — agent operating instructions for this repo: Task ID convention, branch naming (`agent/TASK-ID-description`), commit format (`[TASK-ID] description`), metadata.yaml field guidance, self-audit requirement, transcript immutability rule, merge rule, post-merge metadata update step
- Added `CLAUDE.md` — Claude Code auto-loads this file; it is a short pointer to `AGENTS.md` (Claude Code reads `CLAUDE.md`, not `AGENTS.md`, automatically)
- Added `docs/github-project-board.md` — setup guide for GitHub Projects board with seven-column pipeline (`Backlog → Assigned to Agent → Agent Returned → Human Review → Needs Repair → Merged → Archived`), step-by-step creation instructions, and per-column usage notes
- Updated `README.md` file table: added entries for `AGENTS.md`, `CLAUDE.md`, `docs/`, `.github/PULL_REQUEST_TEMPLATE.md`, and `questions-for-Matt.md`
- Noted in `questions-for-Matt.md` that the GitHub Project board must be created manually via GitHub UI

## 2026-06-20 — Initial structure

- Established repo as the canonical home for system design documents
- Defined task ID convention: `TASK-YYYYMMDD-NNNN`
- Defined session folder path: `sessions/YYYY/YYYY-MM-DD/TASK-ID/`
- Defined session contents: `metadata.yaml`, per-agent transcript files, `artifacts/`, `summary.md`
- Defined five-phase implementation plan (see `Plan.md`)
- Defined metadata schema v0.1 (see `Plan.md` → Phase 1)

## 2026-06-20 — Phase 1: folder structure and templates

- Created `sessions/2026/` directory with `.gitkeep` placeholder
- Created `templates/` directory with `metadata.yaml`, `session.md`, and `pr-template.md`
- Created `index/` directory (holds `sessions.db`, gitignored)
- Created `tools/` directory with `.gitkeep` placeholder (Python scripts added in Phase 3)
- Added `.gitignore` to exclude `index/sessions.db` and SQLite WAL/SHM files
- Created sample session `sessions/2026/2026-06-20/TASK-20260620-0001/` documenting the genesis conversation that produced this repository

---
