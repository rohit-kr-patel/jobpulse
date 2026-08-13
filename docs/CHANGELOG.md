# Changelog

## v0.10.0 - Phase 9: Browser Notifications
- Added `notifications` table (migration `0005`, chain-verified against a live SQLite engine on top of `0001`-`0004`): `user_id`, nullable `job_id`, a fully-formed `message` string, `is_read`, `created_at`.
- Added `notification_service.create_notifications_for_new_top_matches`, wired into the scheduler's `run_daily_pipeline` (Phase 8) right after the ranking refresh, reusing its already-computed top matches. A job counts as "new" (notification-worthy) if `created_at` and `fetched_at` are within 60 seconds of each other; since `fetched_at` bumps on every re-fetch but `created_at` doesn't, this alone prevents re-notifying about the same job on subsequent days.
- Added `GET /notifications` (`unread_only`/`limit` params), `PATCH /notifications/{id}/read`, `POST /notifications/mark-all-read`.
- Added the dashboard Notification Banner (`js/notifications.js`), the component deferred from Phase 6: polls every 60s, dismissible list linking to each job, "mark all as read," and real browser `Notification` API integration behind an explicit consent button (not an auto-prompt).
- **Scope note, documented in `docs/10_NOTIFICATION_SYSTEM.md`:** this is polling + the native Notification API, which only fires while the dashboard tab is open - not true push (that needs a service worker, a push subscription, and a push server with VAPID keys, none of which are referenced anywhere in the project docs). Flagged explicitly rather than overclaiming "push."
- Added 14 new backend tests (102 total): notification service unit tests (including the newness-heuristic with controlled timestamps), route integration tests, and one true end-to-end test running the real scheduler pipeline and asserting a notification appears/reads/clears correctly.
- Frontend verified the same way as Phase 6: `node --check` plus a temporary `jsdom` harness (8 assertions: banner rendering, browser notifications actually firing, dismiss, mark-all-read, and the permission-button show/hide flow) - not shipped as part of the deliverable.

## v0.9.0 - Phase 8: Scheduler
- Added `app/scheduler/` (new `docs/17_SCHEDULER.md`): APScheduler `BackgroundScheduler` running a daily cron job (`SCHEDULER_FETCH_HOUR`/`MINUTE`/`TIMEZONE`), started/stopped via the app's existing lifespan hook.
- The daily pipeline (`run_daily_pipeline`) calls the existing `job_service.fetch_and_store_all` (Phase 4/5, unchanged) and then `matching_service.get_top_matches` (Phase 7, unchanged) to exercise and log the full fetch-then-rank pipeline end-to-end - no new fetch or ranking logic, just automated triggering. Never raises; logs every branch (fetch summary, ranking refresh, skipped-no-preferences, no-jobs-to-rank).
- `SCHEDULER_ENABLED` defaults to `false` at the code level (so tests / a fresh checkout with no `.env` never start a background thread unexpectedly) but defaults `true` in `.env.example`, since automated daily fetching is the product's core promise. Verified both paths directly: disabled is a true no-op (checked via thread count), enabled actually starts, registers the job, and shuts down cleanly.
- **Scope note:** `tasks/PHASE_08_SCHEDULER.md` also lists "Update notifications," but no notifications system exists yet - that's Phase 9's explicit scope. Not implemented here; see `docs/17_SCHEDULER.md` for where it plugs in once Phase 9 exists.
- Added 9 new tests (93 total): the pipeline function's branches and the scheduler lifecycle (build/start/stop, disabled-is-noop, enabled-registers-job).
- Fixed a couple of missed `app.version` bumps in `main.py` from earlier phases (was still `0.7.0` going into this phase - now `0.9.0`).

## v0.8.0 - Phase 7: Matching Engine
- Added `app/matching/scoring.py`: TF-IDF + cosine similarity (scikit-learn) combined with four rule-based factors (skills, role, location, experience, remote-fit) into one weighted score in `[0, 1]`. TF-IDF was the locked-in V1 choice over sentence embeddings, made during initial project scoping.
- Weights (`MATCH_WEIGHT_*`) and the top-N cutoff (`MATCH_TOP_N`, default 20) are configurable via settings rather than hardcoded.
- Added `app/services/matching_service.get_top_matches`: builds a profile from preferences + the latest resume (skills unioned/deduped, experience prefers the resume's parsed figure) and ranks all stored jobs (up to `MATCH_CANDIDATE_POOL_SIZE`) against it.
- Added `GET /matches` (not in the original API spec - added since ranking jobs is the entire point of this phase and needs a way to surface the result), returning the top-N jobs with a full per-factor score breakdown. 404s if preferences aren't set yet; a missing resume degrades gracefully rather than blocking.
- Refactored: the whole-token keyword matcher and "years of experience" statement regex, previously private to `app/parsing/resume_parser.py`, are now shared via `app/text_extraction.py` so job matching doesn't duplicate them.
- Added 21 new tests (84 total): scoring-factor unit tests (including the neutral-vs-partial-credit experience logic and the empty-candidate/empty-vocabulary edge cases), profile-building tests, and integration tests for `matching_service` and `GET /matches`.
- **Scope note:** this phase is backend-only per its task list (TF-IDF, cosine similarity, weighted scoring, top 20) - the dashboard does not yet have a "Top Matches" view or display match scores.

## v0.7.0 - Phase 6: Dashboard
- Added `dashboard.html` (`js/dashboard.js`): stats cards, live client-side filters (search/source/remote), job card grid, and a "Refresh jobs" button wired to the existing `POST /jobs/fetch`. Distinguishes "no jobs fetched yet" from "no jobs match these filters" as separate empty states.
- Added `job-detail.html` (`js/job-detail.js`): reads `?id=` from the URL, fetches `GET /jobs/{id}`, renders full description + apply link; handles a missing/unknown id with a clear inline error instead of a blank page.
- Introduced a real design token system in `css/style.css` (color/type/shape custom properties) plus `css/dashboard.css` for dashboard-specific components - Space Grotesk (headings) + Inter (body) + JetBrains Mono (metadata) type pairing, a teal "pulse" accent, and a freshness indicator (pulsing dot + relative time) tied to each job's actual `fetched_at`. This also refined the shared styling used by the existing `preferences.html`/`resume-upload.html`/`index.html` pages so the whole frontend now shares one visual identity.
- All job data (titles, descriptions, company names) is rendered via `textContent`/`createElement`, never `innerHTML`, since it originates from third-party job-board APIs and must not be trusted as HTML.
- Factored shared relative-time formatting into `js/time-utils.js` to avoid duplicating it between `dashboard.js` and `job-detail.js`.
- **Verification note:** no browser rendering was available in the build environment. Verified via `node --check` (JS syntax) and a temporary `jsdom`-based harness that loaded the real HTML/CSS/JS, mocked `fetch`, and asserted on the resulting DOM across stats computation, freshness logic, both filters, the job-detail render, its 404 path, and both empty-state variants - not shipped as part of the deliverable.
- **Scope note:** Login and the Notification Banner (both listed in `docs/06_FRONTEND_DESIGN.md`) were not built - V1 has no auth, and notifications are Phase 9's explicit scope.

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
