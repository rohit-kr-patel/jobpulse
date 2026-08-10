# TODO

## Done
- [x] Phase 1 - Project Setup (folder structure, FastAPI, PostgreSQL config, Docker Compose, env vars, health endpoint)
- [x] Phase 2 - User Profile (preferences CRUD, resume upload, DB models/migration, validation, frontend forms)
- [x] Phase 3 - Resume Parser (PyMuPDF text extraction, rule-based skills/education/experience extraction, persisted to `resumes`)
- [x] Phase 4 - Job Fetchers (Greenhouse, Lever, Remotive, Arbeitnow; normalization, dedup via `(source, external_id)`, `GET /jobs`, `GET /jobs/{id}`, manual `POST /jobs/fetch` trigger)
- [x] Phase 5 - Database & APIs (`fetch_logs` table + `GET /fetch-logs`; error-handling tests for the global exception handler). `applications`/`notifications` deliberately NOT built here - see note below.
- [x] Phase 6 - Dashboard (job cards, live client-side filters, stats cards, job detail page, design token system, responsive layout)

## Next Up - Phase 7: Matching Engine
- [ ] TF-IDF vectorization of resume + preferences vs. job descriptions
- [ ] Cosine similarity scoring
- [ ] Weighted ranking (skills/experience/location/CTC fit)
- [ ] Return top 20 ranked jobs

## Notes / Open Questions
- **Phase 5 scope decision:** `docs/05_API_SPECIFICATION.md` lists `POST /applications`, `PATCH /applications/{id}`, `GET /notifications` without assigning them to a phase, which could read as Phase 5's responsibility. But `tasks/PHASE_09_BROWSER_NOTIFICATIONS.md` and `tasks/PHASE_10_APPLICATION_TRACKER.md` explicitly own that behavior (save/applied/rejected/expired/history; push/dashboard/mark-as-read). Building those tables/endpoints in Phase 5 would have preempted those phases entirely, so Phase 5 built only `fetch_logs` (the one remaining table not claimed anywhere else) instead. Flagging this prominently in case the intent was actually for Phase 5 to own them - happy to move the work earlier if so.
- Phase 2 built the `users`/`resumes`/`preferences` tables, and Phase 4 built `jobs`, both ahead of Phase 5's nominal ownership of "SQLAlchemy models, Alembic migrations" - each was required to make its own phase's stated tasks ("store profile in database", "store jobs") actually functional.
- Parsed resume fields (skills/education/experience) were added as new nullable columns directly on `resumes` (not a separate table) - resolved per the default noted in the previous phase.
- Resume parsing is rule-based and approximate by design (no LLMs, per project scope) - false negatives are expected for resumes that don't match the curated skill/degree keyword lists or use unusual phrasing for experience. Worth revisiting the skill list as real resumes are tested against it.
- Job dedup only catches re-fetches of the *same* source's job (via `source`+`external_id`); the same job posted on two different boards (e.g. a company's own Greenhouse board and a Remotive listing) is not detected. No fuzzy cross-source matching implemented - flagged as a known limitation, not silently ignored.
- Greenhouse/Lever fetch nothing until `GREENHOUSE_BOARD_TOKENS`/`LEVER_COMPANY_SLUGS` are configured with real company slugs in `.env` - there's no public directory of companies using these ATSes, so this is a manual, per-deployment configuration step, not a bug.
- The dashboard fetches only the 200 most recent jobs and filters/searches entirely client-side (no server-side search endpoint exists yet). Fine at V1 scale; would need a real query param on `GET /jobs` if job volume grows substantially.
- No browser was available to visually render/screenshot the dashboard in the build environment - verified instead via JS syntax checks and a jsdom harness asserting on real DOM output against mocked API responses (not shipped). Worth a quick visual check on your end before considering Phase 6 fully signed off.
