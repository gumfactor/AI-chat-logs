# Questions for Matt

Generated during Phase 1 implementation (2026-06-20).

---

## 1. Session file naming convention: `transcript.md` vs. `session.md`

**Issue:** The `templates/session.md` template defines a unified file (transcript + summary + self-audit in one). The Plan.md describes per-agent files (`orchestrator.md`, `agent-a.md`) plus a separate `summary.md`. The sample session uses `transcript.md` + `summary.md` as separate files.

**Decision needed:** Which convention is authoritative?
- Option A: Single unified file per agent, named after the agent role (`orchestrator.md`, `agent-a.md`, `transcript.md` for single-agent sessions). Summary and Self-Audit are sections within it.
- Option B: Separate `transcript.md` (raw export) and `summary.md` (written after close) as distinct files, so the transcript is immutable once committed.
- Option C: Something else.

The current implementation uses Option B for the sample session and Option A in the template. This should be unified before sessions accumulate.

---

## 2. `agent-history` vs. `AI-chat-logs` repo name

**Issue:** The genesis conversation (TASK-20260620-0001) and Plan.md both refer to the repo as `agent-history`. The actual repo is named `AI-chat-logs`. The GitHub org/repo path recorded in the sample session is `gumfactor/AI-chat-logs`.

**Decision needed:** Is `AI-chat-logs` the final name, or is a rename planned? If final, Plan.md should be updated to remove `agent-history` references to avoid confusion for future readers.

---

## 3. Missing genesis session data

**Issue:** For TASK-20260620-0001, the following could not be reconstructed:
- `platform_url` — the ChatGPT conversation URL is unknown
- `timestamp_start` / `timestamp_end` — exact times not recorded; stored as `null`
- `model` — the ChatGPT model version is unknown
- `commits` — SHA(s) from the initial repo setup were not recorded

**Action needed:** If you have access to the original ChatGPT conversation, the URL and model version can be retrieved. Otherwise, these remain as null/unknown.

---

## 4. `.gitignore` scope: only `index/sessions.db` vs. broader patterns

**Current state:** `.gitignore` covers `index/sessions.db`, `index/sessions.db-shm`, and `index/sessions.db-wal`.

**Question:** Should the gitignore also cover `index/*.db` (any SQLite file in index/) in case the database is renamed or additional databases are added in Phase 3? Or should it remain explicit to avoid accidentally ignoring intentional files?

---

## 5. `orchestrator.md` / `agent-a.md` convention from genesis conversation

**Issue:** Turn 2 of the genesis transcript proposed per-agent files inside each task folder. This is not yet reflected in the templates or sample session. If multi-agent sessions are coming soon, the folder convention should be documented before the first multi-agent capture.

**Decision needed:** Confirm the multi-agent file layout so it can be added to Plan.md and templates before Phase 2 begins.
