# Worklog

Running log of work done on this system. Most recent entry first.

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
