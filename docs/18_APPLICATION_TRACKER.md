# Application Tracker

## Implementation (Phase 10)

### Applications: Save / Applied / Rejected

`applications` table (`app/models/application.py`, migration `0007`): one row per `(user_id, job_id)` - enforced by a unique constraint, since "saving" the same job twice should update the existing row's status, not create a duplicate. Status is one of `saved` / `applied` / `rejected` (`ApplicationStatus`). `applied_at`/`rejected_at` are set automatically the first time the status transitions to that value and are never cleared by a later transition, giving a lightweight timeline without a separate transition-log table. An optional `notes` field supports free-text tracking ("recruiter said role is on hold", etc.) - not explicitly named in the original docs, but a natural, low-risk fit for "track application lifecycle."

**Endpoints:**
- `POST /applications` (in the original spec) - creates a tracked application, default status `saved`. 404s if the job doesn't exist; **409s if it's already tracked** - use PATCH to change its status instead of re-POSTing, keeping create/update semantics unambiguous.
- `PATCH /applications/{id}` (in the original spec) - partial update. Distinguishes "notes omitted from the request" (leave unchanged) from "notes explicitly `null`" (clear them) by reading the raw request body rather than relying on Pydantic defaults alone.
- `GET /applications` (not in the original spec - added since "application history" needs somewhere to view it), filterable by `status`.

### Expired jobs

A job is marked expired if it hasn't reappeared in a fetch for its source in `JOB_EXPIRE_AFTER_DAYS` (default 3) days. Concretely: after every source's fetch completes in `job_service`, any job of that source whose `fetched_at` predates `now - JOB_EXPIRE_AFTER_DAYS` gets `is_expired = true`. Every job actually returned by a fetch is explicitly set `is_expired = false` in that same run, so a job that disappears and later reappears (e.g. reposted) is automatically un-expired - no separate "confirmed gone" tracking needed.

This piggybacks entirely on data the fetch pipeline already produces (`fetched_at`, bumped on every successful re-fetch); no changes were needed to the fetchers themselves (Phase 4) or the fetch orchestration (Phase 5/8).

`GET /jobs` excludes expired jobs by default; pass `include_expired=true` to see them too (e.g. to review a job you already tracked before it expired). `GET /jobs/{id}` is unaffected - a directly-linked expired job (from an existing application, say) still loads, with an "expired" badge on `job-detail.html`.

**Known limitation:** this is an absence-based heuristic, not a confirmed-removal signal (no per-job existence check against the source). A single failed fetch run for a source doesn't immediately expire its jobs (the multi-day threshold absorbs that), but a source that's been silently broken for longer than the threshold would have all of its jobs expire even though they might still be open. Acceptable at V1 scale given the existing `fetch_logs` visibility into fetch failures (Phase 5).

### Frontend

- **`job-detail.html`** ("Your tracking" section, `js/job-detail.js`): current status (with a relative-time note once applied/rejected), three buttons (Save / Mark Applied / Mark Rejected - the active one disabled), and a notes textarea. The page has no separate "GET application by job" endpoint to call - like the dashboard's job list, it fetches the bounded `GET /applications` list and matches client-side by job id, consistent with the pattern established in Phase 6.
- **`applications.html`** ("My Applications", `js/applications.js`) - the application history view: every tracked application, filterable by status, each showing the job, status, notes preview, and timeline, linking back to its job detail page. Not one of the five pages originally listed in `docs/06_FRONTEND_DESIGN.md`, added because "application history" is an explicit Phase 10 task with nowhere else to live.

### Verification

Backend: 22 new tests (124 total) - service-layer tests (including the notes omitted-vs-null distinction, and the applied_at/rejected_at timestamp behavior), route integration tests (including the 409-on-duplicate-save case), and expiry-detection tests (marks-stale, doesn't-mark-recent, un-expires-on-reappearance, and the `GET /jobs` default-exclusion behavior).

Frontend: verified with the same jsdom-harness approach as Phases 6 and 9 (not shipped) - confirmed the job-detail tracking flow doesn't create duplicate applications when clicking through Save → Mark Applied (POST then correctly PATCH, not POST twice), and that the applications history page renders and filters correctly.
