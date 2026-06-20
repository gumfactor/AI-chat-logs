# GitHub Project Board Setup Guide

This document explains how to create and use the GitHub Project board for tracking agent tasks. Creating the board requires the GitHub UI — it cannot be done by an agent via files alone.

---

## Column Names (in order)

```
Backlog → Assigned to Agent → Agent Returned → Human Review → Needs Repair → Merged → Archived
```

---

## Step-by-Step Setup (GitHub Projects — new Projects, not classic)

> **Note on the new Projects UI:** GitHub's new Projects experience (ProjectsV2) represents columns as values of a single-select "Status" field, not as separate independent columns. When this guide says "add a column," it means "add a Status field value." The board view renders each Status value as a column.

### 1. Create the Project

1. Go to [github.com/gumfactor](https://github.com/gumfactor) (your profile or the org).
2. Click the **Projects** tab.
3. Click **New project**.
4. Choose the **Board** template (columns view). If you land on a table view instead, click **+ New view** at the top and select **Board**.
5. Name the project: `Agent Task Pipeline` (or your preferred name).
6. Click **Create project**.

### 2. Set the Status Field Values (Columns)

In the new Projects UI, the board columns come from a **Status** single-select field. You edit its values to create your columns.

To edit the Status field values:
- In the board view, click the **...** menu (top-right of the board) → **Settings** → **Fields** → click on **Status**.
- Alternatively: on the board, click the field name in any column header.

**Delete the default values** (`Todo`, `In Progress`, `Done`) and **replace with these seven values** in order:

| Column / Status Value | Description |
|---|---|
| `Backlog` | Task defined, Task ID assigned, not yet started |
| `Assigned to Agent` | Agent has been given the task and is working |
| `Agent Returned` | Agent opened a PR; work is waiting for human review |
| `Human Review` | Human is actively reviewing the PR |
| `Needs Repair` | PR was reviewed and sent back; agent needs to fix something |
| `Merged` | PR merged to main; task complete |
| `Archived` | Abandoned, superseded, or moved to a future phase |

Click **Save** after editing the field values.

### 3. Add Issues and PRs from This Repo

In the new Projects UI there is no "link a repository" setting in the traditional sense. Items from a specific repo are added to the project in two ways:

**Option A — Manual add:**
- On the board, click **+ Add item** at the bottom of any column.
- Type `#` to search for issues or PRs from any repo you have access to, including `gumfactor/AI-chat-logs`.
- Select the item to add it as a card.

**Option B — From the repo:**
- Go to `gumfactor/AI-chat-logs` → open any issue or PR.
- In the right sidebar, under **Projects**, click the gear icon and select `Agent Task Pipeline`.
- The issue/PR is added to the project as a card.

### 4. Enable Auto-Add (Optional but Recommended)

Auto-add lets GitHub automatically add new issues/PRs from this repo to the project.

1. In the project, click **...** (top-right) → **Settings** → **Workflows**.
2. Click **Auto-add to project** (or enable it if it exists as a toggle).
3. Configure the trigger: select the repository `gumfactor/AI-chat-logs` and the event (e.g., "issue opened", "pull request opened").
4. In the same workflow, add a **"Set field"** action: set **Status** = `Backlog`. This ensures auto-added items land in the Backlog column, not unsorted.
5. Save the workflow.

Without step 4, auto-added items have no Status and will not appear in any column on the board view.

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

- GitHub Projects (new) uses a different UI from the deprecated "classic" Projects. This guide covers the new Projects experience (ProjectsV2, as of 2026). If you see a "classic" option when creating a project, choose the new Projects instead.
- The board is a dashboard, not a database. The canonical record is always the session folder in `sessions/` and the `metadata.yaml`.
- Cards can be sorted or filtered by a custom field if you add a field matching the `metadata.yaml` `status` values (`open`, `returned`, `repair`, `merged`, `abandoned`). This lets you cross-reference the board state with the YAML metadata.
- Moving a card on the board updates the item's **Status** field value. This is the only thing that changes — it does not automatically update `metadata.yaml`. Status changes in the YAML must be made manually after merge or abandonment.
