# Questions for Matt

Items marked **[DECIDED]** were resolved by the supervisor and implemented. Items marked **[NEEDS YOUR INPUT]** are waiting on you.

Generated during Phase 1 implementation (2026-06-20).

---

## 1. Session file naming convention: `transcript.md` vs. `session.md` — **[NEEDS YOUR INPUT]**

**Issue:** The `templates/session.md` template defines a unified file (transcript + summary + self-audit in one). The Plan.md describes per-agent files (`orchestrator.md`, `agent-a.md`) plus a separate `summary.md`. The sample session uses `transcript.md` + `summary.md` as separate files.

**Supervisor recommendation:** Option B (separate files). Plan.md states "Transcripts are immutable after commit" — this is only enforceable if transcript and summary are separate files. A combined file would require editing the transcript section to add the summary, violating immutability.

**Decision needed from you:** Confirm Option B, or override. Once confirmed, `templates/session.md` will be split into `templates/transcript.md` and `templates/summary.md`.

---

## 2. `agent-history` vs. `AI-chat-logs` repo name — **[DECIDED]**

**Decision:** `AI-chat-logs` is the canonical name. Plan.md has been updated to remove `agent-history` references.

---

## 3. Missing genesis session data

**Issue:** For TASK-20260620-0001, the following could not be reconstructed:
- `platform_url` — the ChatGPT conversation URL is unknown
- `timestamp_start` / `timestamp_end` — exact times not recorded; stored as `null`
- `model` — the ChatGPT model version is unknown
- `commits` — SHA(s) from the initial repo setup were not recorded

**Action needed:** If you have access to the original ChatGPT conversation, the URL and model version can be retrieved. Otherwise, these remain as null/unknown.

---

## 4. `.gitignore` scope — **[DECIDED]**

**Decision:** Switched to `index/*.db`, `index/*.db-shm`, `index/*.db-wal` glob patterns. Any SQLite file in `index/` is ignored, which is the right default — there's no reason to commit database files there.

---

## 5. Multi-agent file layout — **[NEEDS YOUR INPUT]**

**Issue:** Plan.md specifies per-agent files inside each task folder (`orchestrator.md`, `agent-a.md`, etc.). This is not yet reflected in the templates. If you're actively running multi-agent sessions now, this should be defined before the first one is captured.

**Supervisor recommendation:** Keep it as Plan.md specifies — one `.md` file per agent role, named descriptively (`orchestrator.md`, `research-agent.md`, `coder-agent.md`). Single-agent sessions use `transcript.md`. The `summary.md` is always separate (see Q1).

**Decision needed from you:** Are you running multi-agent sessions yet? If yes, confirm the layout and it will be added to templates.
