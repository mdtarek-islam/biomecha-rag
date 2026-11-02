---
name: ci-cd-harness
description: CI stages, local reproduction of each job, flaky test triage and the release checklist for biomecha-rag. Use when CI fails, when changing workflows or when cutting a release.
---

# ci-cd-harness

## 1. CI stages

1. secrets: pinned gitleaks binary with checksum, then a regex scan of tracked files.
2. audit: pip-audit on requirements, bandit on src/.
3. quality: ruff check, ruff format check, mypy on src/.
4. test: pytest on Python 3.12.
5. governance: guard-claude-md --audit and scan-skill all.
6. terraform: fmt -check and validate with the backend disabled.

## 2. Local reproduction

Run each command from the repo root inside a .venv.

| Job | Command |
|---|---|
| secrets | git ls-files -z, then grep -E with the SECRET_RE value from ci.yml |
| audit | pip-audit -r requirements.txt |
| bandit | bandit -q -r src -ll |
| lint | ruff check src tests |
| types | mypy src |
| test | pytest -q |
| governance | bash .claude/hooks/guard-claude-md.sh --audit |
| skills | bash .claude/hooks/scan-skill.sh all |
| terraform | terraform -chdir=terraform fmt -check -recursive |
| validate | terraform -chdir=terraform init -backend=false, then validate |

## 3. Failure triage

1. Read the first error line, not the last. Later errors follow from it.
2. Reproduce locally with the command above before any edit.
3. Classify: code fault, configuration fault, flaky test, upstream outage.
4. Fix the cause. Never raise a timeout or add a retry to hide a fault.
5. Record the incident in docs/incidents/ with job, cause and fix.

## 4. Flaky test triage

1. Run the test 20 times: pytest path::test -q --count 20 if pytest-repeat exists, else a loop.
2. Check order dependence: run the test alone, then in the suite.
3. Check time, random seed, network and shared files. Tests use fakes and tmp_path.
4. Fix by removing the shared state. Quarantine a test only with a dated issue note.

## 5. Hook failures

1. guard-claude-md --audit fails on length above 110 lines, missing sections or dash characters.
2. scan-skill all fails on hash mismatch after a reviewed skill or hook change.
3. Regenerate the locks with scan-skill --relock only after the owner reviews the change.

## 6. Release checklist

1. All CI jobs green on main.
2. CHANGELOG.md Unreleased section moved under the new version and date.
3. pyproject.toml version bumped by semantic versioning.
4. terraform plan reviewed by the owner. No apply without approval.
5. Tag vX.Y.Z created by the owner after the commit lands.
6. README maintenance status matches the commit history.
