# AGENTS.md — Instructions for Agents Working on This Repo

This file governs how any AI agent (Claude, Codex, Gemini, or other) should behave when working **on this repository** (`AI-chat-logs`). Tasks in this repo include: adding new session captures, maintaining templates, running or updating the indexer, and updating documentation.

---

## 1. Task ID Convention

Every agent task has a unique ID:

```
TASK-YYYYMMDD-NNNN
```

Examples: `TASK-20260620-0001`, `TASK-20260621-0003`

The NNNN counter resets per day and increments monotonically.

**How the Task ID is assigned:**

- **Normal path (hook installed):** The `session_init.py` hook fires when the human presses Enter on their first message. The hook assigns the next available Task ID, writes a `metadata.yaml` stub, and injects the Task ID into your system context before you respond. You will see it in your initial context — use it from your first commit onward.

- **Fallback (no hook, or injection failed):** Check the session folder at `sessions/YYYY/YYYY-MM-DD/` — if a stub exists for today's session, that Task ID is yours. If nothing exists, ask the human for a Task ID before doing any work.

**The Task ID must appear in:**
- The transcript folder name (`sessions/YYYY/YYYY-MM-DD/TASK-ID/`)
- The branch name (see below)
- Every commit message (see below)
- The PR title and body
- The `metadata.yaml` for the session
- The GitHub issue title/body (if an issue exists)

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
| `platform_url` | Optional — copy from browser address bar if available; URLs frequently don't resolve long-term, so `session_id` is the durable reference |
| `timestamp_start` / `timestamp_end` | ISO 8601 with Z suffix; set to `null` if unknown |
| `agent` | Lowercase: `claude`, `codex`, `gemini`, `chatgpt`, etc. |
| `model` | Specific model string: `claude-sonnet-4-6`, `o4-mini`, etc.; set to `null` if unknown |
| `branch` | The branch this session's work landed on |
| `orchestrator` | Set to `true` if this session spawned subagent sessions |
| `subagent_sessions` | List the TASK-IDs of all subagents this session spawned |
| `parent_session` | Set to the TASK-ID of the orchestrator that spawned this session |
| `commits` | Add SHAs after the session ends and commits are made |
| `prs` | Add PR URLs after PRs are opened |
| `status` | Start as `open`; update to `returned`, `merged`, or `abandoned` as status changes |

After the session ends and the PR is merged, update `metadata.yaml` with final commit hashes and the PR URL, then commit that update.

---

## 5. Multi-Agent Session Layout

There are two distinct multi-agent patterns. Choose the right one for your situation.

### Pattern A — Multiple transcripts, one session (same platform invocation)

When a supervisor and one or more delegates all run inside the same platform session (same TASK-ID, same branch), each agent gets its own transcript file inside the shared session folder:

```
sessions/YYYY/YYYY-MM-DD/TASK-ID/
├── metadata.yaml          ← one shared metadata file for the whole task
├── orchestrator.md        ← the supervisor's transcript
├── agent-a.md             ← first subagent's transcript (name descriptively)
├── agent-b.md             ← second subagent's transcript
├── artifacts/             ← generated files, diffs, outputs
└── summary.md             ← written by the human/orchestrator after the task closes
```

Naming convention for per-agent files: use the agent's role, not a generic letter if possible. Examples: `orchestrator.md`, `research-agent.md`, `coder-agent.md`, `reviewer-agent.md`.

For single-agent sessions, use `transcript.md` as the filename.

### Pattern B — Separate sessions per subagent (each gets its own TASK-ID)

When each agent runs as a separate platform session (separate Claude Code invocation, separate hook firing), each gets its own TASK-ID and its own `sessions/YYYY/YYYY-MM-DD/TASK-ID/` folder. The DAG links them:

- Orchestrator session: `orchestrator: true`, `subagent_sessions: [TASK-ID-a, TASK-ID-b]`
- Each subagent session: `parent_session: TASK-ID-of-orchestrator`

This is what `tools/dag.py` reads to generate the Mermaid diagram. Use `tools/generate_summary.py TASK-ID` on the orchestrator session to append the full DAG to its `summary.md`.

---

## 6. Self-Audit Requirement

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

## 7. Transcript Immutability Rule

**Transcripts are never edited after the first commit.**

Once a transcript file (`transcript.md`, `orchestrator.md`, `agent-a.md`, etc.) is committed, it is a permanent record. Do not edit it to fix typos, add context, or update conclusions.

If a correction is needed:
- Create a `corrections/` subdirectory inside the session folder
- Add a new file there (e.g., `corrections/correction-001.md`) explaining what is wrong and what the correct information is
- The original transcript remains unchanged

This applies only to transcript files. `metadata.yaml`, `summary.md`, and `artifacts/` can be updated after the fact (with appropriate commit messages explaining why).

---

## 8. The Human Merges; Agents Propose

Agents work on branches and open PRs. No agent output goes to `main` without explicit human review and merge. This rule has no exceptions.

If you find yourself on `main` or about to push directly to `main`, stop. Create a branch instead.

---

## 9. What to Do When Working on This Repo

When an agent task involves work on `AI-chat-logs` itself (as opposed to capturing a session from another repo):

1. Confirm you have a Task ID.
2. Work on an `agent/TASK-...` branch.
3. Prefix every commit with `[TASK-ID]`.
4. When done, open a PR. GitHub will auto-populate the PR body from `.github/PULL_REQUEST_TEMPLATE.md`. Do not copy from `templates/pr-template.md` manually — `templates/pr-template.md` is the canonical reference definition for documentation purposes, but GitHub's auto-population handles the actual PR body. Fill in every field in the auto-populated body.
5. Complete the self-audit in `summary.md` before considering the task finished.
6. If you have open questions for the human, append them to `questions-for-Matt.md` using the established format (see Section 10).
7. **Post-merge step:** After the human merges the PR, update the session's `metadata.yaml` with the final commit hashes (in `commits:`) and the PR URL (in `prs:`), then change `status:` to `merged`. Commit that update with message `[TASK-ID] update metadata post-merge`.

---

## 10. Open Questions

If you encounter something ambiguous or undecided, do not guess and silently proceed. Append the question to `/home/user/AI-chat-logs/questions-for-Matt.md` using this format:

```markdown
## N. Short title of the question — **[NEEDS YOUR INPUT]**

**Issue:** [Describe the ambiguity or gap.]

**Options considered:** [What are the reasonable choices?]

**Supervisor recommendation:** [What would you do if forced to choose?]

**Decision needed from you:** [Exactly what you need answered.]
```

Then proceed with the supervisor recommendation (or the most conservative option) and note in the summary that a decision is pending.

---

## 11. Site-Wide Agent Instructions

This `AGENTS.md` governs work **on this repo only**. Site-wide instructions that apply across all repos live in a separate `.dotfiles` repository (under `.claude/` and `.agents/` directories), which Claude Code and other agent runtimes can be configured to load automatically.

If you are working in a project repo and need guidance that isn't covered by that repo's local `AGENTS.md` or `CLAUDE.md`, check whether site-wide instructions exist in the `.dotfiles` repo. When in doubt, err on the side of caution and ask.
