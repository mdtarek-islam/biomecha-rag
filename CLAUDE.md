# biomecha-rag: Main Office Governance

Owner: Md Tarek Islam. Branch: main. Scope: production maintenance, security and CI/CD.
Output style: action first, numbered steps, max 5 items per list, no pleasantries.

## 1. Purpose and Zones

Hybrid RAG engine for sports biomechanics notes. BGE dense and BM25 sparse vectors feed a
Pinecone hybrid index. A cross-encoder reranks. Mistral-7B answers via LangChain on Hugging Face
endpoints. AWS Lambda and API Gateway serve it. Terraform builds the stack. GitHub Actions gate it.

| Zone | Path | Rule |
|---|---|---|
| Source | src/biomecha_rag/ | Change only through a reviewed pull request. |
| Tests | tests/ | Every fix gets a failing test first. |
| Infrastructure | terraform/ | Run fmt and validate. Never apply without approval. |
| Decisions | docs/adr/ | One record per significant choice. |
| Governance | .claude/, CLAUDE.md, .github/, .coderabbit.yaml | Owner approves each change. |
| Local vault | .dump/, .claude/ipc/, .claude/agent-memory/ | Local only. Never staged or pushed. |
| Data | data/ | Read only unless the owner says otherwise. |

## 2. Rules

1. Run Python only through a .venv. Install libraries only into a .venv.
2. Delete nothing. Move files to .dump/<file>.<YYYYMMDD-HHMMSS>.bak. Never run rm or git clean.
3. Stage by exact path. Never use git add -A or git add . in this repo.
4. Sole author: Md Tarek Islam. Add no Co-Authored-By line. Name no tool in commits.
5. Write British English, active voice, imperative verbs, sentences under 20 words.
6. Use zero emojis, zero em-dashes, zero en-dashes. Obey the stop-slop banned word list.
7. Keep secrets out of the repo. Read only the example environment file.
8. Ask for approval before commit, merge, push, deploy or terraform apply.

## 3. Branch Policy

1. main is production and the ops office. It holds src/, tests/, terraform/, docs/ and CI files.
2. generator is the R&D office. It holds prompts, scratch work and experiments.
3. Only the /merge-to-main command in the generator office moves code into main.
4. Never merge .claude/ from generator into main. The two offices keep separate governance.
5. Fix production faults on main first. Then merge main back into generator.

## 4. Agents

| Agent | Model | Job |
|---|---|---|
| sre-release-steward | haiku | Semantic versions, CHANGELOG.md, pull request checks, commit text. |
| secops-pentest-auditor | sonnet | OWASP API Top 10, prompt injection, pip-audit, IAM review. |
| env-simulation-tester | sonnet | Local Lambda and API Gateway harness, service fakes, latency runs. |
| ci-incident-responder | haiku | Diagnose GitHub Actions and CodeRabbit failures. |

1. Route by task. Use the cheapest model that fits.
2. Hand off between agents with caveman compression.

## 5. Skills

1. caveman: compress agent handoffs.
2. stop-slop: enforce prose rules before any prose file.
3. senior-commit: branch, stage and commit workflow with approval.
4. secops-pentest: security checklist, test cases and report format.
5. ci-cd-harness: CI stages, local reproduction, flaky triage, release checklist.

## 6. Commands and Checks

1. /release: prepare a version bump, changelog entry and release notes.
2. /security-audit: run the secops checklist and write a findings report.
3. /simulate-env: run the local event harness and latency probes.
4. Governance check: bash .claude/hooks/guard-claude-md.sh --audit
5. Skill check: bash .claude/hooks/scan-skill.sh all
