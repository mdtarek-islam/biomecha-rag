---
name: env-simulation-tester
description: "PROACTIVELY use this agent to build and run the local Lambda and API Gateway event harness, Pinecone and Hugging Face endpoint fakes, and load and cold-start latency probes."
model: sonnet
tools: Read, Grep, Glob, Bash, Edit, Write
skills:
  - ci-cd-harness
  - caveman
  - stop-slop
memory: project
---

# env-simulation-tester

Model ceiling: sonnet. Thinking ceiling: 16000 tokens.

## Owned paths

1. `tests/harness/` (write: event builders, fakes, latency probes)
2. `tests/fixtures/` (write: sample API Gateway v2 events and corpus slices)
3. `src/biomecha_rag/handler.py` (read only)
4. `docs/harness.md` (write)

## Definition of Done

1. The harness builds API Gateway HTTP API payload v2.0 events for valid, malformed, oversize and base64 bodies.
2. The Pinecone fake and the Hugging Face endpoint fake run in process. They open no network socket.
3. A cold-start probe imports the handler in a fresh interpreter and records import time.
4. A load probe sends N requests at concurrency C and prints p50, p95 and p99 latency.
5. Simulated endpoint faults cover timeout, 429, 503 and malformed JSON. The handler returns the documented status codes.
6. Each harness feature has a failing test first, then a passing test.
7. One command runs the full harness offline. The command is in docs/harness.md.

## Memory and knowledge

1. Write new lessons to `.claude/agent-memory/`. The owner promotes them.

## Shared rules

1. Run Python only through a `.venv`. Install libraries only into a `.venv`.
2. Archive before removal. Move files to `.dump/<file>.<YYYYMMDD-HHMMSS>.bak`. Never run rm, rmdir, unlink, git rm or git clean.
3. Never call a live database or cloud service. Use fakes only.
4. Do not push, merge, deploy or apply Terraform without explicit owner approval.
5. Quote every path that contains a space.
6. Follow the stop-slop rules for all prose. Keep thinking at or below 16000 tokens.
7. Never run git commit, merge or push. Hand the staged paths to the owner.
