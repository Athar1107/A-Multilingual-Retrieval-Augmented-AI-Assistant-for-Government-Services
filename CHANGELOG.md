# Changelog

> **Research baseline:** Current Konkani-English research scope is maintained in [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md); repository-specific status is in [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md).

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Documentation
- Added `docs/RESEARCH_PLAN.md` to codify the owner-approved Konkani (Devanagari)-to-English active-corpus route, translation-audit separation, and evaluation design.
- Added an implementation audit that distinguishes present prototype code from missing or broken runtime functionality.
- Updated the Markdown documentation with implementation-status references.

### Added
- Complete project documentation (AGENT.md, PROJECT.md, ARCHITECTURE.md, IMPLEMENTATION.md, DATA_MODEL.md, RAG_PIPELINE.md, API_SPEC.md, CODING_STANDARDS.md, TESTING.md, ROADMAP.md, PROMPTS.md, SECURITY.md, TASKS.md)
- Full monorepo directory structure
- Backend placeholder modules for all pipeline components
- Frontend i18n translation files (English and Gujarati)
- Docker Compose local development stack
- GitHub Actions CI workflows for backend and frontend
- `.gitignore`, `CONTRIBUTING.md`, `README.md`
- `backend/pyproject.toml` with all pinned dependencies
- `backend/.env.example` with all configuration keys documented
- Nginx configuration with rate limiting and security headers

---

## [0.1.0] — 2026-08-07

- Initial repository structure created (TASK-001 complete)
