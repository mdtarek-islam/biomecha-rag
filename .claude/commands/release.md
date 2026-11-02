---
description: Prepare a release. Bump the version, update CHANGELOG.md and draft the commit. Stops before commit.
argument-hint: "[major|minor|patch]"
---

Use the sre-release-steward agent. Bump type: $ARGUMENTS (default: infer from the changelog).

1. Run `git status` and `git branch --show-current`. Stop if the branch is not main.
2. Run the local CI commands from the ci-cd-harness skill. Stop on any failure.
3. Move the Unreleased entries in CHANGELOG.md under a new version heading with today's date.
4. Update the version field in pyproject.toml. Touch no dependency line.
5. Draft the commit with senior-commit. Print the staged paths and the subject.

Stop and wait for the owner. The owner commits, tags and pushes.
