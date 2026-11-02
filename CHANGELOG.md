# Changelog

All notable changes to this project are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Main office governance: hooks, agents, skills and commands for production maintenance.
- CI jobs for secret scan, pip-audit, bandit, ruff, mypy, pytest, governance and Terraform.
- Dependabot for pip, GitHub Actions and Terraform. CodeRabbit review rules.
- Tool configuration for mypy and bandit in pyproject.toml.

## [0.1.0]

### Added

- Hybrid retrieval with BGE dense and BM25 sparse vectors on a Pinecone index.
- Cross-encoder reranking and Mistral-7B generation through Hugging Face endpoints.
- AWS Lambda handler, API Gateway and Terraform stack.
