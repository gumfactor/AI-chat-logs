# AGENTS.md — Instructions for Agents Working on This Repo

This file governs how any AI agent (Claude, Codex, Gemini, or other) should behave when working **on this repository** (`AI-chat-logs`). Tasks in this repo include: adding new session captures, maintaining templates, running or updating the indexer, and updating documentation.

---

## 1. Task ID Convention

Every agent task must have a unique ID assigned **before work begins**:

```
TASK-YYYYMMDD-NNNN
```

Examples: `TASK-20260620-0001`, `TASK-20260621-0003`

The NNNN counter resets per day and increments monotonically. If two tasks start on the same day, they get sequential numbers. The human assigns the ID before starting the session.

**The Task ID must appear in:**
- The transcript folder name (`sessions/YYYY/YYYY-MM-DD/TASK-ID/`)
- The branch name (see below)
- Every commit message (see below)
- The PR title and body
- The `metadata.yaml` for the session
- The GitHub issue title/body (if an issue exists)

No task ID = no agent work. If you were not given a Task ID, ask for one before proceeding.

---

## 2. Branch Naming Convention

```
agent/TASK-YYYYMMDD-NNNN-short-description
```

Examples:
- `agent/TASK-20260620-0002-add-phase2-files`
- `agent/TASK-20260621-0001-update-indexer`

Rules:
- Always prefix with `agent/`
- Include the full Task ID after the prefix
- Follow with a short hyphenated description (3–6 words)
- Use lowercase and hyphens only — no underscores, no uppercase

---

## 3. Commit Message Format

```
[TASK-YYYYMMDD-NNNN] brief imperative description
```

Examples:
- `[TASK-20260620-0002] add Phase 2 github integration files`
- `[TASK-20260621-0001] fix indexer handling of empty sessions`

Rules:
- The Task ID in brackets is mandatory — it is the traceability anchor
- Use imperative mood ("add", "fix", "update", "remove") not past tense
- Keep the subject line under 72 characters
- Add a body paragraph if context is needed (leave a blank line after subject)

---

## 4. Filling Out `metadata.yaml` When Capturing a Session

When you add a new session to this repo, copy `templates/metadata.yaml` into the session folder and fill in every field. Required fields with no known value should be set to `null`, not left blank or omitted.

Key fields to fill carefully:

| Field | Notes |
|---|---|
| `session_id` | Must match the folder name exactly |
| `platform_url` | Canonical URL of the original chat (copy from browser address bar) |
| `timestamp_start` / `timestamp_end` | ISO 8601 with Z suffix; estimate if exact time unknown, note the uncertainty |
| `agent` | Lowercase: `claude`, `codex`, `gemini`, `chatgpt`, etc. |
| `model` | Specific model string: `claude-sonnet-4-5`, `o4-mini`, `gemini-2.0-flash`, etc. |
| `branch` | The branch this session's work landed on |
| `commits` | Add SHAs after the session ends and commits are made |
| `prs` | Add PR URLs after PRs are opened |
| `status` | Start as `open`; update to `returned`, `merged`, or `abandoned` as status changes |

After the session ends and the PR is merged, update `metadata.yaml` with final commit hashes and the PR URL, then commit that update.

---

## 5. Self-Audit Requirement

Every session's `summary.md` must end with a **Self-Audit** section. The session is not complete without it. Use this exact structure:

```markdown
## Self-Audit

**What did I change?**
[List every file added, modified, or deleted. Be specific.]

**What did I not touch?**
[List files or areas you deliberately left alone, and why.]

**What could be wrong?**
[Honest assessment of risks, edge cases, or things you could not verify.]

**How did I test it?**
[Describe exactly what you ran or checked. "I didn't test it" is an acceptable answer if true — just say so.]

**What is unresolved?**
[Open questions, follow-up tasks, or decisions deferred to the human.]
```

Do not summarize or abbreviate the self-audit. It is the primary record of the agent's confidence and uncertainty.

---

## 6. Transcript Immutability Rule

**Transcripts are never edited after the first commit.**

Once a transcript file (`transcript.md`, `orchestrator.md`, `agent-a.md`, etc.) is committed, it is a permanent record. Do not edit it to fix typos, add context, or update conclusions.

If a correction is needed:
- Create a `corrections/` subdirectory inside the session folder
- Add a new file there (e.g., `corrections/correction-001.md`) explaining what is wrong and what the correct information is
- The original transcript remains unchanged

This applies only to transcript files. `metadata.yaml`, `summary.md`, and `artifacts/` can be updated after the fact (with appropriate commit messages explaining why).

---

## 7. The Human Merges; Agents Propose

Agents work on branches and open PRs. No agent output goes to `main` without explicit human review and merge. This rule has no exceptions.

If you find yourself on `main` or about to push directly to `main`, stop. Create a branch instead.

---

## 8. What to Do When Working on This Repo

When an agent task involves work on `AI-chat-logs` itself (as opposed to capturing a session from another repo):

1. Confirm you have a Task ID.
2. Work on an `agent/TASK-...` branch.
3. Prefix every commit with `[TASK-ID]`.
4. When done, open a PR using `templates/pr-template.md` as the body.
5. Complete the self-audit in `summary.md` before considering the task finished.
6. If you have open questions for the human, append them to `questions-for-Matt.md` using the established format.

---

## 9. Open Questions

If you encounter something ambiguous or undecided, do not guess and silently proceed. Append the question to `/home/user/AI-chat-logs/questions-for-Matt.md` using this format:

```markdown
## N. Short title of the question — **[NEEDS YOUR INPUT]**

**Issue:** [Describe the ambiguity or gap.]

**Options considered:** [What are the reasonable choices?]

**Supervisor recommendation:** [What would you do if forced to choose?]

**Decision needed from you:** [Exactly what you need answered.]
```

Then proceed with the supervisor recommendation (or the most conservative option) and note in the summary that a decision is pending.
