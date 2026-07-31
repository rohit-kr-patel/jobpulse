# CLAUDE.md

# JobPulse V1 - AI Development Guide

## Purpose
You are the primary software engineer for JobPulse V1.

JobPulse is a personal job assistant for a single user. The objective is to automatically fetch relevant software jobs every day based on the user's resume and preferences, rank them, and present them in a clean dashboard.

This repository is the single source of truth.

---

# Project Scope

Implement ONLY V1.

Never implement V2/V3 features unless explicitly instructed.

Allowed:
- Resume upload
- Resume parsing
- User preferences
- Job fetchers
- Matching engine
- PostgreSQL
- Dashboard
- Browser notifications
- Scheduler
- Save / Applied / Rejected
- Expired jobs

Do NOT implement:
- LLMs
- AI Chat
- Auto Apply
- LinkedIn scraping
- Cover letter generation
- Resume rewriting
- Mobile app
- Email notifications
- Telegram bot

---

# Development Workflow

Before every task:

1. Read README.md
2. Read docs/15_PROJECT_SCOPE.md
3. Read the requested PHASE document
4. Read related docs if needed

Never skip these steps.

Implement ONLY the requested phase.

---

# Architecture Rules

Backend
- FastAPI
- SQLAlchemy ORM
- Alembic
- APScheduler
- PostgreSQL

Frontend
- HTML
- CSS
- Vanilla JavaScript

Keep frontend and backend separated.

Use layered architecture:

Routes
↓

Services
↓

Repositories

↓

Database

Business logic belongs in services.

---

# Code Quality

Always

- Type hints
- Docstrings for public functions
- Small functions
- Modular code
- Dependency injection where appropriate
- Clear variable names
- No duplicated logic

Never

- Hardcode secrets
- Commit API keys
- Leave commented-out code
- Leave TODO placeholders in completed phases

---

# Git Rules

Every completed phase:

- Update CHANGELOG.md
- Update TODO.md
- Update relevant docs

Use focused commits.

Examples

feat: add resume parser

feat: implement dashboard

fix: resolve duplicate job detection

---

# Documentation Rules

If code changes architecture:

Update

- System Architecture
- API Specification
- Database Design

If API changes:

Update API documentation.

If schema changes:

Update database documentation.

---

# Error Handling

Always

- Validate inputs
- Return meaningful HTTP status codes
- Log unexpected exceptions
- Avoid exposing internal stack traces

---

# Logging

Use structured logging.

Log:

- Job fetch start/end
- Resume upload
- Parsing success/failure
- Scheduler runs
- Notification events
- API failures

Never log sensitive data.

---

# Database

Use migrations.

No raw SQL unless necessary.

Indexes for searchable columns.

Normalize where practical.

---

# Job Fetchers

Supported V1 sources:

- Greenhouse
- Lever
- Remotive
- Arbeitnow

Normalize all fetched jobs into one schema.

Deduplicate before saving.

---

# Matching Engine

No LLM.

Use:
- TF-IDF or sentence-transformer embeddings (non-generative)
- Cosine similarity
- Weighted ranking

Return Top 20 jobs.

---

# Testing

Every phase should be runnable.

Add tests for core services when practical.

Verify:
- API endpoints
- Scheduler
- Resume parsing
- Matching

---

# Definition of Done

A phase is complete only when:

- Acceptance criteria satisfied
- Code runs
- Documentation updated
- No placeholder code
- Clean commit ready

Never continue to the next phase automatically.

Wait for explicit instruction.

---

# Communication

If requirements conflict:

Stop.

Explain the conflict.

Request clarification.

Never make large architectural changes without approval.

Be conservative.

Maintainability is preferred over cleverness.

This document is authoritative for the repository.
