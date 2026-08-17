# Testing Strategy

Unit Tests:
- Resume parser
- Matching
- Fetchers

Integration:
- APIs
- Database

Manual:
- Dashboard
- Notifications
- Scheduler

## As implemented (Phase 11)

124 automated backend tests (`pytest`), run against an in-memory SQLite database built directly from the SQLAlchemy models (no live Postgres needed for the suite):
- **Unit**: resume parser (skills/education/experience extraction, edge cases), matching/scoring (each factor independently, plus integration), text extraction helpers, fetchers (mocked HTTP via `respx`, realistic payloads per source)
- **Integration**: every API route (preferences, resume upload, jobs, matches, fetch-logs, notifications, applications), the scheduler's daily pipeline end-to-end, and the global exception handler
- **Migrations**: every migration's `upgrade()`/`downgrade()` verified directly against a live SQLite engine at each phase, and the full migration-built schema cross-checked against the ORM-model-built schema for exact agreement (see `docs/18_APPLICATION_TRACKER.md` for the most recent example)

What stayed manual, and why: the **Dashboard** and **Notification Banner** have no visual/browser-rendering test in this environment (no browser available in the build sandbox) - instead verified with a `jsdom` harness that loads the real HTML/CSS/JS, mocks `fetch`, and asserts on the resulting DOM (covering stats computation, filtering, freshness logic, browser-notification firing, and the application-tracking flow). These harnesses aren't shipped as part of the deliverable; a real visual check in an actual browser is still worth doing. The **Scheduler**'s wall-clock trigger itself isn't tested (no test waits on real time) - only the pipeline function it calls, which is fully covered.
