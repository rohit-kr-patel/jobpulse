# Changelog

## v0.6.0 - Phase 5: Database & APIs
- **Scope clarification (see docs/TODO.md for the full note):** `applications` and `notifications` were *not* built in this phase, despite being nominally listed in the database/API docs. Their behavior is explicitly owned by Phase 10 (Application Tracker) and Phase 9 (Browser Notifications) per those phases' own task lists - building them now would have preempted that work rather than filled a gap.
- Added a `fetch_logs` table via migration `0004_create_fetch_logs_table.py` (verified against a live SQLite engine, chained on top of `0001`-`0003`), the one table from the original list not explicitly claimed by any other phase.
- `app/services/job_service.fetch_and_store_all` now records one `FetchLog` row per source per run (fetched/created/updated counts, failed flag, start/finish timestamps), committed in the same transaction as that source's job upserts.
- Added `GET /fetch-logs` (filterable by `source`, paginated) to make this fetch history visible.
- Added a dedicated test suite for the global unhandled-exception handler (`app/main.py`), confirming it actually returns a clean generic 500 without leaking exception details - previously wired up but never directly exercised by a test, since FastAPI's `TestClient` re-raises exceptions by default unless `raise_server_exceptions=False` is set.
- Added 8 new tests (60 total): fetch-log persistence/filtering in the service layer, `GET /fetch-logs` integration tests, and the error-handling tests above.

## v0.5.0 - Phase 4: Job Fetchers
- Added a `jobs` table via migration `0003_create_jobs_table.py` (verified against a live SQLite engine, chained on top of `0001`/`0002`), with a unique constraint on `(source, external_id)` as the deduplication key.
- Added fetchers (`app/fetchers/`) for all four confirmed V1 sources - Greenhouse, Lever, Remotive, Arbeitnow (verified each source's real API shape via web research before implementing, rather than guessing). Each normalizes into a shared `NormalizedJob` dataclass. Greenhouse/Lever are per-company APIs configured via `GREENHOUSE_BOARD_TOKENS`/`LEVER_COMPANY_SLUGS`; Remotive/Arbeitnow are general boards needing no per-company config.
- Added shared fetcher utilities (`app/fetchers/utils.py`): HTML-to-plain-text via BeautifulSoup, remote-location heuristic, and defensive ISO/epoch datetime parsing - all fail-soft since these are third-party APIs.
- Added `app/services/job_service.fetch_and_store_all`: runs and commits each source independently, so one source's failure (network error, bad response shape, unexpected exception) never blocks or rolls back the others. Returns a per-source `fetched`/`created`/`updated`/`failed` summary.
- Added `GET /jobs` (list, filterable by `source`, paginated), `GET /jobs/{id}`, and `POST /jobs/fetch` (manual trigger - Phase 8 will wire the same pipeline to a daily scheduler instead).
- Added 21 new tests (52 total): fetcher unit tests with mocked HTTP (`respx`) covering normalization, per-source failure handling, and Arbeitnow pagination bounding; job-service tests covering the create/update/dedup lifecycle across repeated fetch runs and cross-source failure isolation; and endpoint integration tests.
- Added `beautifulsoup4` (HTML parsing) and `respx` (test-only HTTP mocking) dependencies; `httpx` promoted from test-only to a production dependency.
- Documented known limitation: dedup only catches re-fetches of the *same* source's job (via `source`+`external_id`); the same job posted on two different boards is not detected - see `docs/07_JOB_FETCHER_DESIGN.md`.

## v0.4.0 - Phase 3: Resume Parser
- Added a rule-based resume parsing pipeline (`app/parsing/`): PDF text extraction via PyMuPDF, then skills, education, and experience-years extraction via keyword/regex matching. No LLMs, per docs/08_RESUME_PARSER.md.
- Skills matching (`app/parsing/skills_data.py`, ~70 curated tech skills) suppresses shadowed substrings (e.g. won't report "C" when "C++" also matched, or "SQL" when "PostgreSQL" matched) and uses case-sensitive matching for short ambiguous names (`Go`, `R`, `C`) to avoid matching common English words.
- Education matching (`app/parsing/education_data.py`) checks a curated list of degree keywords/abbreviations, with case-sensitive matching for `BE`/`ME` to avoid colliding with the pronouns "be"/"me".
- Experience-years extraction first looks for an explicit statement (e.g. "5+ years of experience"), falling back to the span between the earliest and latest 4-digit year mentioned (an approximation, only used when no explicit statement exists).
- Added `parsed_skills`, `parsed_education`, `parsed_experience_years`, `parsed_at` nullable columns on `resumes` via migration `0002_add_resume_parsed_fields.py` (verified against a live SQLite engine, chained correctly on top of `0001`).
- Wired parsing into `POST /resume/upload`: runs automatically after a successful upload; a parse failure (e.g. corrupt/unreadable PDF) never fails the upload - it just leaves the parsed fields empty, and is logged server-side.
- Extended `ResumeResponse` to include the parsed fields.
- Updated `resume-upload.html` to display the parsed skills/education/experience after a successful upload, with a note that it's rule-based and should be reviewed.
- Added 16 new tests (32 total): parser unit tests (skill/education/experience extraction edge cases, real-PDF text extraction) and endpoint integration tests using real PyMuPDF-generated PDFs.

## v0.3.0 - Phase 2: User Profile
- Added `users`, `resumes`, `preferences` tables via a hand-authored Alembic migration (`backend/alembic/versions/0001_initial_users_resumes_preferences.py`), verified against a live SQLite engine.
- Added SQLAlchemy models (`app/models/`): `User`, `Resume`, `Preferences` (with a `WorkMode` enum). List-like preference fields (roles, skills, locations) use portable JSON columns rather than Postgres-specific ARRAY types.
- Added a repository layer (`app/repositories/`) for plain data access and a service layer (`app/services/`) for validation/business logic, per the Routes → Services → Repositories → Database architecture in CLAUDE.md.
- Added `GET /preferences` and `POST /preferences` (upsert) endpoints with full validation: non-empty role/skill/location lists, experience range, `max_ctc >= min_ctc`, and a constrained `work_mode`.
- Added `POST /resume/upload`: validates file extension, declared content-type, PDF magic bytes, non-empty content, and a configurable max size (default 5MB); stores the file on disk and records metadata in the `resumes` table. Resume *parsing* is out of scope here — see Phase 3.
- Added startup seeding of the single hardcoded V1 user (no auth) via `app/db/seed.py`.
- Added a global exception handler that logs unhandled errors server-side and returns a generic message to the client (no stack traces leaked).
- Added frontend pages: `preferences.html` (prefills from `GET /preferences`, validates, upserts) and `resume-upload.html` (client + server-side PDF validation), linked from the homepage.
- Added 14 new backend tests (16 total) covering preferences CRUD/validation and resume upload/validation, run against an in-memory SQLite DB built from the ORM models.
- Added `python-multipart` dependency (required by FastAPI for file uploads); `.gitignore` now excludes the local `backend/uploads/` resume storage folder.

## v0.2.0 - Phase 1: Project Setup
- Created `backend/` (FastAPI app, layered `core/db/api` structure) and `frontend/` (static placeholder page) folder structure.
- Configured FastAPI application factory with CORS and structured logging (`app/main.py`, `app/core/logging.py`).
- Configured environment-driven settings via `pydantic-settings` (`app/core/config.py`); see `.env.example` for all variables.
- Configured PostgreSQL connectivity (SQLAlchemy engine + session factory in `app/db/session.py`). No ORM models yet — those arrive in Phase 5.
- Added `GET /health` endpoint reporting API and database status.
- Added Docker Compose orchestration for `db` (Postgres 16) and `backend` services, plus a backend `Dockerfile`.
- Added unit tests for the health endpoint (`backend/tests/test_health.py`), passing with mocked DB sessions.
- Added `.gitignore` covering Python artifacts, `.env`, and editor/OS files.

## v0.1.0
- Documentation initialized.
