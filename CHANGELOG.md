# Changelog

Tracks structural changes to this system: folder conventions, metadata schema updates, tooling decisions, and naming changes. Not a task log (see `WORKLOG.md`).

---

## 2026-06-20 — Hook-based session initialization

- Added `tools/session_init.py` — hook script called by Claude Code (`UserPromptSubmit`) and Codex (`session_start`) at session start; assigns next `TASK-YYYYMMDD-NNNN`, creates `sessions/.../TASK-ID/metadata.yaml` stub, outputs `{"additionalSystemPrompt": "..."}` to inject Task ID into agent context. Idempotent via temp-file state lock in `/tmp/ai-chat-logs-sessions/`. Flags: `--agent`, `--model`, `--dry-run`.
- Added `docs/hooks-setup.md` — step-by-step hook configuration for Claude Code (`~/.claude/settings.json`) and Codex (`~/.codex/config.toml`), including VS Code/Cursor/Windsurf extension. Covers: verification steps, `--dry-run` testing, Codex injection caveat, troubleshooting.
- Updated `templates/metadata.yaml` — added `platform_session_id` field (platform's native UUID/thread ID, captured automatically by hook).
- Updated `tools/capture.py` — added `--task-id` flag; when given and session folder already exists (hook-initialized), writes only `transcript.md` and `summary.md` and preserves the hook-written `metadata.yaml`.
- Updated `AGENTS.md §1` — task ID is now injected by hook on normal path; fallback instructions for sessions without a hook.
- Updated `MANUAL.md` — rewritten "Starting a session" section reflects hook-first workflow; updated capture section with `--task-id` usage.
- Updated `tools/README.md` — added `session_init.py` section; updated `capture.py` section with `--task-id` option.

**Schema change:** `metadata.yaml` now has a `platform_session_id` field between `session_id` and `platform_url`. Existing sessions are unaffected (the field is optional in practice).

## 2026-06-20 — Phase 5: DAG visualization

- Added `tools/dag.py` — Mermaid DAG generator; reads all `metadata.yaml` files in `sessions/`; builds parent/child graph using `subagent_sessions` (primary) and `parent_session` (fallback); renders `graph TD` Mermaid diagram. Flags: `--root SESSION-ID` (subtree scope), `--output FILE` (write to file), `--append-to FILE` (append to existing file). Node labels: `"SESSION-ID (agent)"` with ` [orchestrator]` suffix when `orchestrator: true`. Abandoned sessions styled grey. Circular reference detection with warning; handles fully-circular graphs (no root nodes) by falling back to per-node DFS. Silently skips session folders missing `metadata.yaml`. Prints "no relationships" message when all sessions are independent.
- Added `tools/generate_summary.py` — creates or updates `summary.md` for a session; creates blank template if missing; appends Mermaid DAG section; idempotent (skips if DAG marker already present). Imports and reuses DAG logic from `dag.py`.
- Added `sessions/2026/2026-06-20/TASK-20260620-0002/` — stub sample session demonstrating multi-agent provenance; `parent_session: TASK-20260620-0001` creates the TASK-0001 → TASK-0002 edge in the DAG.
- Updated `tools/README.md` — added sections for `dag.py` and `generate_summary.py`.
- Updated `sessions/2026/2026-06-20/TASK-20260620-0001/summary.md` — appended auto-generated Mermaid DAG section.

## 2026-06-20 — Phase 4: Semi-automatic capture

- Added `tools/capture.py` — CLI capture tool; reads transcript from `--file` or stdin; auto-generates next `TASK-YYYYMMDD-NNNN` ID by scanning existing session folders; creates `sessions/YYYY/YYYY-MM-DD/TASK-ID/` with `transcript.md`, `metadata.yaml`, and blank `summary.md`; `--index` flag triggers the indexer post-capture; exits non-zero with error message on empty transcript.
- Updated `tools/README.md` — added `capture.py` section with full usage reference.

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
