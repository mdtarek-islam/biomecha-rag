---
description: Run the security checklist over the API, retrieval path, dependencies and Terraform. Writes a findings report.
argument-hint: "[area: api|rag|deps|iam|all]"
---

Use the secops-pentest-auditor agent with the secops-pentest skill. Area: $ARGUMENTS (default: all).

1. Run pip-audit and bandit. Attach the output.
2. Run the regex secret scan over tracked files.
3. Walk the OWASP API Top 10 checklist against src/biomecha_rag/handler.py.
4. Run the prompt-injection and exfiltration cases against local fakes only.
5. Review every IAM statement in terraform/. Write the report to docs/security/audit-<YYYYMMDD>.md.

Write a failing test in tests/security/ for each confirmed finding. Do not fix source files in this command.
