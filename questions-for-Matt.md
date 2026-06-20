# Questions for Matt

Items marked **[DECIDED]** were resolved by the supervisor and implemented. Items marked **[NEEDS YOUR INPUT]** are waiting on you.

Generated during Phase 1 implementation (2026-06-20).

---

## 1. Session file naming convention: `transcript.md` vs. `session.md` — **[DECIDED]**

**Issue:** The `templates/session.md` template defines a unified file (transcript + summary + self-audit in one). The Plan.md describes per-agent files (`orchestrator.md`, `agent-a.md`) plus a separate `summary.md`. The sample session uses `transcript.md` + `summary.md` as separate files.

**Supervisor recommendation:** Option B (separate files). Plan.md states "Transcripts are immutable after commit" — this is only enforceable if transcript and summary are separate files. A combined file would require editing the transcript section to add the summary, violating immutability.

**Decision needed from you:** Confirm Option B, or override. Once confirmed, `templates/session.md` will be split into `templates/transcript.md` and `templates/summary.md`.
**Matt's Decision:** Confirmed Option B.

---

## 2. `agent-history` vs. `AI-chat-logs` repo name — **[DECIDED]**

**Decision:** `AI-chat-logs` is the canonical name. Plan.md has been updated to remove `agent-history` references.

---

## 3. Missing genesis session data — **[DECIDED]**

**Issue:** For TASK-20260620-0001, the following could not be reconstructed:
- `platform_url` — the ChatGPT conversation URL is unknown
- `timestamp_start` / `timestamp_end` — exact times not recorded; stored as `null`
- `model` — the ChatGPT model version is unknown
- `commits` — SHA(s) from the initial repo setup were not recorded

**Action needed:** If you have access to the original ChatGPT conversation, the URL and model version can be retrieved. Otherwise, these remain as null/unknown.
**Matt'Decision:** URL should not be required, as this will rarely resolve; ID/Ref# are sufficient. Same with timestamp and model if those will not ever resolve (though it would be much better if they could).

---

## 4. `.gitignore` scope — **[DECIDED]**

**Decision:** Switched to `index/*.db`, `index/*.db-shm`, `index/*.db-wal` glob patterns. Any SQLite file in `index/` is ignored, which is the right default — there's no reason to commit database files there.

---

## 5. Multi-agent file layout — **[DECIDED]**

**Issue:** Plan.md specifies per-agent files inside each task folder (`orchestrator.md`, `agent-a.md`, etc.). This is not yet reflected in the templates. If you're actively running multi-agent sessions now, this should be defined before the first one is captured.

**Supervisor recommendation:** Keep it as Plan.md specifies — one `.md` file per agent role, named descriptively (`orchestrator.md`, `research-agent.md`, `coder-agent.md`). Single-agent sessions use `transcript.md`. The `summary.md` is always separate (see Q1).

**Decision needed from you:** Are you running multi-agent sessions yet? If yes, confirm the layout and it will be added to templates.
**Matt's Decision:** Yes, I'm running multi-agent sessions - often supervisor/delegate structures. So connections between these agents will need to be identifiable/auditable through the files/file structure.

---

## 6. GitHub Project board creation — **[DECIDED]**

**Issue:** Phase 2 requires a GitHub Project board with columns `Backlog → Assigned to Agent → Agent Returned → Human Review → Needs Repair → Merged → Archived`. This board **cannot be created by an agent via files** — it requires the GitHub web UI (GitHub's GraphQL API could be used via `gh api` calls, but that is not implemented here).

**Options considered:**
- A) You create it manually now, following `docs/github-project-board.md`.
- B) Defer until Phase 3 is complete and you have a reason to track tasks actively.

**Supervisor recommendation:** Option A — create it now. The board is cheap to set up and immediately useful for tracking the Phase 3 and Phase 4 tasks.

**Decision needed from you:** Follow the setup guide at `docs/github-project-board.md` to create the board manually. No further file changes are needed in this repo once it exists.
**Matt's Decision:** Defer for now.

---

## 7. PR template propagation to other project repos — **[DECIDED]**

**Issue:** The `.github/PULL_REQUEST_TEMPLATE.md` created in Phase 2 applies to PRs opened in `AI-chat-logs` itself. Plan.md Phase 2 item 3 says to add an `AGENTS.md` (or `CLAUDE.md`) to **each project repo** where agent work happens. Those repos are separate — the template and agent instructions need to be manually added or propagated to each one.

**Options considered:**
- A) Copy manually each time you start a new project repo that uses agents.
- B) Create a small shell script or `gh` command that bootstraps a new project repo with the PR template and `AGENTS.md`/`CLAUDE.md`.
- C) Create a GitHub repository template containing these files, so new repos created from it inherit them automatically.

**Supervisor recommendation:** Option A for now (you have few project repos), with Option C as the Phase 4 upgrade when the system is stable.

**Decision needed from you:** How many project repos do you currently use agents on? If it's more than 2–3, Option B or C becomes worth the setup cost now.
**Matt's Decision:** I have a .dotfiles repo set up to hold skills that should be auto inherited across repos. Particulary in the .Claude and .Agents folders. This hasn't yet been turned into a template, but it probably should be.

---

## 8. Indexer purge behavior when a session folder is deleted — **[DECIDED]**

**Issue:** `tools/index.py` now purges DB rows for any session whose folder no longer exists on disk. This was a real bug: the adversarial subagent created and then deleted a test folder (`TASK-TEST-NO-META`), leaving a stale row in the DB that caused the idempotency assertion to fail. The fix was applied.

**However, there is a design question:** should deleted session folders be purged from the index silently, or should their rows be preserved as a "tombstone" so you know a session once existed? The current fix purges them and prints `[purged] <session_id> (folder no longer exists)` during indexing.

**Options:**
- A) Current behavior: purge stale sessions from the index when the folder is deleted. Clean index, no history of deleted sessions.
- B) Keep stale rows but mark them `status = deleted` in `session_meta`. Lets you see that a session was once captured and then removed.
- C) Refuse to delete and error: print a warning when a DB row has no matching folder, requiring manual cleanup.

**Supervisor recommendation:** Option A is correct for test/scratch sessions. Option B is worth considering if you ever intentionally delete a real session folder (e.g., to remove sensitive content), since you'd want a record that it existed.

**Decision needed from you:** Are you likely to intentionally delete committed session folders? If no, Option A is fine as-is.
**Matt's Decision:** Preserve everything.

---

## 9. `capture.py` — indexer failure exit code behavior — **[DECIDED]**

**Issue:** When `--index` is used and `tools/index.py` exits non-zero, `capture.py` prints a warning to stderr but still exits 0. The session was captured successfully, so success is arguably correct. But if you run this in a script that checks exit codes, a broken indexer will go undetected.

**Options considered:**
- A) Current behavior: exit 0 even when the indexer fails. The capture succeeded; the index can be rebuilt manually.
- B) Exit 1 (same as indexer) when `--index` is used and indexer fails. More strict; better for scripting.
- C) Exit 2 (distinct code) to signal "captured OK but index failed." Allows callers to distinguish "capture failed" from "index failed."

**Supervisor recommendation:** Option A is correct for interactive use. Option B or C is better if you plan to use `capture.py` in CI or automation scripts.

**Decision needed from you:** Will you use `--index` in automated scripts that check exit codes?
**Matt's Decision:** Yes, I may use --index in automated scripts.

---

## 10. DAG `--append-to` vs. `generate_summary.py` idempotency semantics — **[DECIDED]**

**Issue:** `tools/dag.py --append-to FILE` is intentionally NOT idempotent — it appends the Mermaid block every time it is called. `tools/generate_summary.py` IS idempotent (checks for the `<!-- dag:generated -->` marker before appending). This split is deliberate: `dag.py` is a low-level primitive; `generate_summary.py` is the high-level workflow tool.

**However:** if you call `dag.py --append-to summary.md` directly (bypassing `generate_summary.py`), repeated calls will duplicate the diagram in the file.

**Options:**
- A) Current behavior: `--append-to` is a dumb append; users should use `generate_summary.py` for idempotent workflow. Document clearly.
- B) Make `--append-to` idempotent by checking for the DAG marker before appending (like `generate_summary.py` does).
- C) Remove `--append-to` from `dag.py` entirely — all file-append use goes through `generate_summary.py`.

**Supervisor recommendation:** Option A is fine for now. `generate_summary.py` is the recommended entry point; `--append-to` is a power-user escape hatch. The README already documents the distinction.

**Decision needed from you:** Are you likely to call `dag.py --append-to` directly in scripts? If yes, Option B is safer.
**Matt's Decision:** Option B is safer.

---

## 11. DAG re-generation when session graph changes — **[DECIDED]**

**Issue:** `generate_summary.py` is idempotent — once the DAG section is written to `summary.md`, it will not update it even if new subagent sessions are added to the graph later. This means the DAG in `summary.md` can become stale if the session tree grows after the initial generation.

**Options:**
- A) Current behavior: once written, the DAG section is never updated automatically. Users manually re-run `generate_summary.py` after deleting the `<!-- dag:generated -->` marker.
- B) Add a `--force` flag to `generate_summary.py` that replaces (not appends) the DAG section even if already present.
- C) Always replace the DAG section on each run (no idempotency check; last write wins).

**Supervisor recommendation:** Option B — add `--force` as an explicit opt-in. The current default protects against accidental overwrites in a no-op run; `--force` provides an escape hatch for intentional regeneration.

**Decision needed from you:** Will session graphs change after initial `summary.md` generation (i.e., do you add subagents to an in-progress session mid-task)? If yes, Option B or C is needed.
**Matt's Decision:** Option B
