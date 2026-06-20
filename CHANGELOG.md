# Changelog

Tracks structural changes to this system: folder conventions, metadata schema updates, tooling decisions, and naming changes. Not a task log (see `WORKLOG.md`).

---

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
