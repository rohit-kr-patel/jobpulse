# TODO

## Done
- [x] Phase 1 - Project Setup (folder structure, FastAPI, PostgreSQL config, Docker Compose, env vars, health endpoint)
- [x] Phase 2 - User Profile (preferences CRUD, resume upload, DB models/migration, validation, frontend forms)
- [x] Phase 3 - Resume Parser (PyMuPDF text extraction, rule-based skills/education/experience extraction, persisted to `resumes`)
- [x] Phase 4 - Job Fetchers (Greenhouse, Lever, Remotive, Arbeitnow; normalization, dedup via `(source, external_id)`, `GET /jobs`, `GET /jobs/{id}`, manual `POST /jobs/fetch` trigger)
- [x] Phase 5 - Database & APIs (`fetch_logs` table + `GET /fetch-logs`; error-handling tests for the global exception handler). `applications`/`notifications` deliberately NOT built here - see note below.
- [x] Phase 6 - Dashboard (job cards, live client-side filters, stats cards, job detail page, design token system, responsive layout)
- [x] Phase 7 - Matching Engine (TF-IDF + cosine similarity + weighted skills/role/location/experience/remote scoring, `GET /matches` returning top 20)
- [x] Phase 8 - Scheduler (APScheduler daily cron job triggering the existing fetch + ranking pipelines; "Update notifications" deliberately NOT built here - see note below)
- [x] Phase 9 - Browser Notifications (`notifications` table, creation wired into the daily scheduler pipeline, `GET /notifications`, mark-as-read endpoints, dashboard Notification Banner + browser Notification API integration)

## Next Up - Phase 10: Application Tracker
- [ ] `applications` table + model + migration
- [ ] `POST /applications` (save/applied/rejected status)
- [ ] `PATCH /applications/{id}`
- [ ] Expired job detection
- [ ] Application history view

## Notes / Open Questions
- **Phase 5 scope decision:** `docs/05_API_SPECIFICATION.md` lists `POST /applications`, `PATCH /applications/{id}`, `GET /notifications` without assigning them to a phase, which could read as Phase 5's responsibility. But `tasks/PHASE_09_BROWSER_NOTIFICATIONS.md` and `tasks/PHASE_10_APPLICATION_TRACKER.md` explicitly own that behavior (save/applied/rejected/expired/history; push/dashboard/mark-as-read). Building those tables/endpoints in Phase 5 would have preempted those phases entirely, so Phase 5 built only `fetch_logs` (the one remaining table not claimed anywhere else) instead - notifications were correctly picked up later in Phase 9, and `applications` remains for Phase 10.
- Phase 2 built the `users`/`resumes`/`preferences` tables, and Phase 4 built `jobs`, both ahead of Phase 5's nominal ownership of "SQLAlchemy models, Alembic migrations" - each was required to make its own phase's stated tasks ("store profile in database", "store jobs") actually functional.
- Parsed resume fields (skills/education/experience) were added as new nullable columns directly on `resumes` (not a separate table) - resolved per the default noted in the previous phase.
- Resume parsing is rule-based and approximate by design (no LLMs, per project scope) - false negatives are expected for resumes that don't match the curated skill/degree keyword lists or use unusual phrasing for experience. Worth revisiting the skill list as real resumes are tested against it.
- Job dedup only catches re-fetches of the *same* source's job (via `source`+`external_id`); the same job posted on two different boards (e.g. a company's own Greenhouse board and a Remotive listing) is not detected. No fuzzy cross-source matching implemented - flagged as a known limitation, not silently ignored.
- Greenhouse/Lever fetch nothing until `GREENHOUSE_BOARD_TOKENS`/`LEVER_COMPANY_SLUGS` are configured with real company slugs in `.env` - there's no public directory of companies using these ATSes, so this is a manual, per-deployment configuration step, not a bug.
- The dashboard fetches only the 200 most recent jobs and filters/searches entirely client-side (no server-side search endpoint exists yet). Fine at V1 scale; would need a real query param on `GET /jobs` if job volume grows substantially.
- No browser was available to visually render/screenshot the dashboard in the build environment - verified instead via JS syntax checks and a jsdom harness asserting on real DOM output against mocked API responses (not shipped). Worth a quick visual check on your end before considering Phase 6 fully signed off.
- Matching (Phase 7) does not use CTC/salary as a factor - `docs/09_MATCHING_ENGINE.md`'s canonical factor list is skills/role/location/experience/remote only, and salary data isn't reliably structured across all four job sources (Remotive has an optional freeform string; the others rarely include it at all). Not implemented, not silently dropped.
- The dashboard does not yet have a "Top Matches" view or display match scores from `GET /matches` - Phase 7's task list is backend-only (TF-IDF/cosine/weighted-scoring/top-20), and no phase explicitly claims wiring matches into the UI. Worth deciding whether that belongs in a later phase or as an ad-hoc addition.
- Phase 8's "Update notifications" task was not implemented at the time - there was no notifications system yet. Phase 9 has since wired notification creation into `run_daily_pipeline` (app/scheduler/jobs.py) right after the ranking-refresh step, using that step's already-computed top matches, as anticipated.
- `SCHEDULER_ENABLED` defaults to `false` in code (`app/core/config.py`) but `true` in `.env.example` - intentional split so tests/fresh-checkouts stay inert by default while real deployments get automated fetching out of the box. Worth double-checking your `.env` has `SCHEDULER_ENABLED=true` if you want it running.
- Phase 9's "browser push notifications" are polling + the native `Notification` API (fires only while the dashboard tab is open), not true Web Push (service worker + push subscription + VAPID-keyed push server, which would let notifications arrive with no tab open). No such push infrastructure is referenced anywhere in the project docs, so building it wasn't assumed in scope - flagged explicitly rather than silently under-delivering on "push." Worth a deliberate decision if always-on push matters enough to justify that infrastructure later.
- The "is this job new" heuristic for notifications (comparing `created_at` to `fetched_at` within 60 seconds) is simple and self-contained (no changes needed to Phase 4/5's fetch code) but is a heuristic, not a hard guarantee - a sufficiently slow fetch run for a single source (many jobs, slow upstream API) could theoretically push some jobs' insert time past the 60s window and skip a notification. Not observed as an issue at V1's scale; worth widening the threshold if it ever is.
