# Contributing to Government AI Assistant

> **Research baseline:** Follow [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md) for the Konkani-English research scope and data boundary. Use [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for repository-specific setup gaps.

Thank you for contributing. Please read this guide before opening a PR.

---

## Quick Reference

| Task | Command |
|---|---|
| Start dev environment | `docker compose up` |
| Run all tests | `make test` |
| Run linters | `make lint` |
| Format code | `make format` |

---

## Before You Start

1. Read [docs/AGENT.md](docs/AGENT.md) — all rules apply to every contributor
2. Read [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) — code style guide
3. Check [docs/TASKS.md](docs/TASKS.md) — pick a `Todo` task to work on

---

## Branch Naming

```
feature/{ticket-id}-{short-description}   e.g. feature/GOV-42-gujarati-translation
fix/{ticket-id}-{short-description}       e.g. fix/GOV-17-chunk-overlap
docs/{description}                        e.g. docs/update-api-spec
```

Never push directly to `main` or `develop`.

---

## Commit Messages

Follow Conventional Commits:

```
feat(rag): add hybrid BM25 + vector retrieval
fix(chunker): prevent empty chunks from being indexed
docs(api): update chat endpoint response schema
```

---

## Pull Request Checklist

Before submitting:

- [ ] `make lint` passes with zero errors
- [ ] `make test` passes with no regressions
- [ ] New functions have docstrings
- [ ] Documentation updated (API_SPEC.md, PROMPTS.md, etc. if applicable)
- [ ] No secrets or .env files committed
- [ ] PR description explains what and why

---

## Need Help?

Open a GitHub Discussion or tag `@lead-architect` in the issue.
