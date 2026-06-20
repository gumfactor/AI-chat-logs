# AI Chat Logs

Version-controlled audit trail for AI agent conversations, decisions, and reasoning history.

## What This Is

Chat logs are the laboratory notebook of AI-assisted development. Code is the final artifact; the conversation is where decisions get made, approaches get rejected, and reasoning happens. This repo captures and versions that trail.

## What's Here

| File | Purpose |
|---|---|
| `Vision.md` | Goals, constraints, and what success looks like |
| `Plan.md` | Phased implementation plan |
| `WORKLOG.md` | Running log of work done on this system |
| `CHANGELOG.md` | Structural and schema changes |
| `sessions/` | Captured agent transcripts (once Phase 1 is underway) |
| `templates/` | Blank session and metadata templates |
| `tools/` | Indexer and search scripts |

## Quick Reference

- Every agent session gets a task ID before work begins: `TASK-YYYYMMDD-NNNN`
- Transcripts live at `sessions/YYYY/YYYY-MM-DD/TASK-ID/`
- Each session folder contains `metadata.yaml`, one `.md` file per agent, and a `summary.md`
- The task ID threads through: issue → branch → commits → PR → transcript folder

## Status

See `WORKLOG.md` for current progress and `CHANGELOG.md` for structural decisions.
