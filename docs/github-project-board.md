# GitHub Project Board Setup Guide

This document explains how to create and use the GitHub Project board for tracking agent tasks. Creating the board requires the GitHub UI — it cannot be done by an agent via files alone.

---

## Column Names (in order)

```
Backlog → Assigned to Agent → Agent Returned → Human Review → Needs Repair → Merged → Archived
```

---

## Step-by-Step Setup (GitHub Projects — new Projects, not classic)

### 1. Create the Project

1. Go to [github.com/gumfactor](https://github.com/gumfactor) (your profile or the org).
2. Click the **Projects** tab.
3. Click **New project**.
4. Select **Board** layout (columns view).
5. Name the project: `Agent Task Pipeline` (or your preferred name).
6. Click **Create project**.

### 2. Set the Columns

GitHub creates default columns (usually `Todo`, `In Progress`, `Done`). Replace them with the seven columns below.

For each default column you don't need: click the `...` menu on the column header → **Delete column**.

To add a column: click **+ Add column** (far right of the board).

Create these columns **in order**:

| Column | Description |
|---|---|
| `Backlog` | Task defined, Task ID assigned, not yet started |
| `Assigned to Agent` | Agent has been given the task and is working |
| `Agent Returned` | Agent opened a PR; work is waiting for human review |
| `Human Review` | Human is actively reviewing the PR |
| `Needs Repair` | PR was reviewed and sent back; agent needs to fix something |
| `Merged` | PR merged to main; task complete |
| `Archived` | Abandoned, superseded, or moved to a future phase |

### 3. Link the Project to This Repo

1. In the project, click **Settings** (top-right gear icon).
2. Under **Manage access**, add the repository `gumfactor/AI-chat-logs`.
3. Alternatively, go to the `AI-chat-logs` repo → **Projects** tab → **Link a project** → select the project you just created.

Linking lets you reference the board from issues and PRs in the repo.

### 4. Enable Auto-Add (Optional but Recommended)

In the project Settings → **Workflows**:
- Enable **Auto-add to project** for new issues and PRs from `AI-chat-logs`.
- Set items to land in `Backlog` by default.

---

## How to Use the Board

### What Each Column Means in Practice

**Backlog**
A Task ID has been assigned (format: `TASK-YYYYMMDD-NNNN`). The issue exists in GitHub Issues with the task ID in the title. No agent has started work yet.

**Assigned to Agent**
The task was handed to an agent (Claude, Codex, Gemini, etc.). The branch `agent/TASK-ID-description` has been created. Move the card here when you kick off the session.

**Agent Returned**
The agent has finished and opened a PR. The PR body includes the Task ID, transcript link, confidence level, and self-audit. Move the card here when the PR is opened.

**Human Review**
You (the human) are actively reading the PR, reviewing the transcript, and checking the self-audit. Move the card here when you start your review — this signals the item is not just waiting but is being actively evaluated.

**Needs Repair**
You reviewed the PR and found problems. The PR has review comments explaining what needs to be fixed. The agent will be re-engaged for a repair session. Move the card here when you post the review requesting changes.

**Merged**
The PR passed review and was merged to `main`. The `metadata.yaml` has been updated with the final commit hash and PR URL. Move the card here after merge.

**Archived**
The task was abandoned (no longer needed), superseded by another task, or moved to a future phase. Move here instead of deleting — preserves history.

### When to Move a Card

| Event | Move from | Move to |
|---|---|---|
| Task ID assigned, issue created | (new) | Backlog |
| Agent session started | Backlog | Assigned to Agent |
| Agent opens PR | Assigned to Agent | Agent Returned |
| You start reading the PR | Agent Returned | Human Review |
| You request changes | Human Review | Needs Repair |
| Agent re-engaged for repair | Needs Repair | Assigned to Agent |
| PR merged | Human Review | Merged |
| Task abandoned or deferred | any | Archived |

---

## Linking Cards to Issues and PRs

For each task:
1. Create a GitHub Issue titled `[TASK-ID] short description`.
2. When the agent opens a PR, it should reference the issue in the PR body (e.g., `Closes #42`).
3. Add the issue to the project board — it will appear as a card.
4. The card automatically links to the PR once the PR references the issue.

This creates the traceability chain: **board card → issue → PR → transcript folder → full conversation**.

---

## Notes

- GitHub Projects (new) uses a different UI from the deprecated "classic" Projects. This guide covers the new Projects experience (as of 2026).
- The board is a dashboard, not a database. The canonical record is always the session folder in `sessions/` and the `metadata.yaml`.
- Cards can be sorted by `status` field if you add a custom `status` field matching the `metadata.yaml` `status` values (`open`, `returned`, `repair`, `merged`, `abandoned`).
