# TODO

## Done
- [x] Phase 1 - Project Setup (folder structure, FastAPI, PostgreSQL config, Docker Compose, env vars, health endpoint)
- [x] Phase 2 - User Profile (preferences CRUD, resume upload, DB models/migration, validation, frontend forms)
- [x] Phase 3 - Resume Parser (PyMuPDF text extraction, rule-based skills/education/experience extraction, persisted to `resumes`)
- [x] Phase 4 - Job Fetchers (Greenhouse, Lever, Remotive, Arbeitnow; normalization, dedup via `(source, external_id)`, `GET /jobs`, `GET /jobs/{id}`, manual `POST /jobs/fetch` trigger)

## Next Up - Phase 5: Database & APIs
- [ ] `applications` table + model + migration
- [ ] `notifications` table + model + migration
- [ ] `fetch_logs` table + model + migration
- [ ] `POST /applications`, `PATCH /applications/{id}`
- [ ] `GET /notifications`
- [ ] Error handling review across all endpoints

## Notes / Open Questions
- Phase 2 built the `users`/`resumes`/`preferences` tables, and Phase 4 built `jobs`, both ahead of Phase 5's nominal ownership of "SQLAlchemy models, Alembic migrations" - each was required to make its own phase's stated tasks ("store profile in database", "store jobs") actually functional. Phase 5 now only needs `applications`, `notifications`, `fetch_logs` on top of the same Alembic setup.
- Parsed resume fields (skills/education/experience) were added as new nullable columns directly on `resumes` (not a separate table) - resolved per the default noted in the previous phase.
- Resume parsing is rule-based and approximate by design (no LLMs, per project scope) - false negatives are expected for resumes that don't match the curated skill/degree keyword lists or use unusual phrasing for experience. Worth revisiting the skill list as real resumes are tested against it.
- Job dedup only catches re-fetches of the *same* source's job (via `source`+`external_id`); the same job posted on two different boards (e.g. a company's own Greenhouse board and a Remotive listing) is not detected. No fuzzy cross-source matching implemented - flagged as a known limitation, not silently ignored.
- Greenhouse/Lever fetch nothing until `GREENHOUSE_BOARD_TOKENS`/`LEVER_COMPANY_SLUGS` are configured with real company slugs in `.env` - there's no public directory of companies using these ATSes, so this is a manual, per-deployment configuration step, not a bug.
