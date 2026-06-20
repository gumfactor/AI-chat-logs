# Vision: Agent Conversation Provenance System

## The Problem

When using AI coding agents — Codex, Claude, subagents running in parallel — the actual work happens in the chat. The code is only the final artifact. Every decision, rejected approach, dead end, and intermediate reasoning step lives in the conversation and nowhere else.

Current practice papers over this: summaries, standups, and weekly ledgers are lossy compressions. A PR description tells you what changed, not why option 2 was chosen over option 1, or what the orchestrator told three subagents, or what the agent said it was uncertain about. That reasoning trail is organizational intellectual property, and right now it evaporates.

Code is versioned. Documents are versioned. Data is versioned. **Agent reasoning is not.** This project fixes that.

## Core Insight

Chat logs are the laboratory notebook of AI-assisted development. They are the equivalent of design notes, meeting minutes, and architectural decision records — except they happen to also contain the actual implementation work. Treating them as ephemeral UI state is a category error.

## Goals

1. **Complete audit trail.** Every agent session — including subagent forks, parallel runs, and orchestrator threads — is captured as a durable artifact.
2. **Traceability in both directions.** Given a commit, you can find the exact conversation that produced it. Given a conversation, you can find every commit, PR, and issue it touched.
3. **Searchable reasoning history.** Query across all conversations: every time a topic came up, every agent that touched a file, every approach that was considered and rejected.
4. **Minimal friction.** Capture should be as close to automatic as possible. Manual overhead must not become a tax that causes the system to be abandoned.
5. **Personal/small-team scale.** No enterprise tooling required. Built on GitHub, plain files, and lightweight local tooling.

## Constraints

- Must work without enterprise access to vendor conversation APIs (export-based, not API-based).
- Must be operable by a single person as the sole reviewer and merger. Agents propose; the human merges.
- Storage lives in a private GitHub repository. No third-party SaaS required.
- Must survive the loss of any single tool or platform. Transcripts are plain Markdown. Metadata is YAML. No proprietary formats.
- Cost must remain near zero. SQLite over hosted Postgres; flat files over managed search.

## What Success Looks Like

- You can answer "what was the conversation that led to this commit?" in under 30 seconds.
- You can find every conversation where a given file, function, or concept was discussed.
- When a subagent makes a surprising decision, you have the full reasoning chain, not just the output.
- When you return to a problem months later, the chat history serves as institutional memory.
- The system is self-documenting: the audit repo contains the conversations that built the audit repo.

## Scope Boundaries

**In scope:**
- Capturing and versioning full chat transcripts
- Linking conversations to issues, branches, PRs, and commits
- A searchable index of transcript content
- Metadata tracking (agent, model, session ID, files touched, parent session)
- A simple dashboard (GitHub Project board)

**Out of scope (for now):**
- Real-time streaming capture (start with manual/semi-manual export)
- Automated summarization or LLM-based analysis of transcripts
- Multi-user collaboration features
- Integration with non-GitHub issue trackers
