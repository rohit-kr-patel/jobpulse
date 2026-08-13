# API Specification

POST /resume/upload
GET /jobs
GET /jobs/{id}
POST /applications
PATCH /applications/{id}
GET /notifications
POST /preferences
GET /preferences

## Implemented (Phase 2)

### GET /preferences
Returns the current user's preferences.
- 200: `PreferencesResponse` (see below)
- 404: `{"detail": "No preferences set for user <id>"}` if never saved

### POST /preferences
Creates or updates (upserts) the current user's preferences. Body: `PreferencesRequest`.
- 200: `PreferencesResponse`
- 422: validation error (empty role/skill/location list, `experience_years` outside 0-60, `max_ctc < min_ctc`, invalid `work_mode`)

**PreferencesRequest**
```json
{
  "target_roles": ["Backend Engineer"],
  "skills": ["Python", "SQL"],
  "locations": ["Bangalore", "Remote"],
  "experience_years": 2,
  "min_ctc": 800000,
  "max_ctc": 1500000,
  "work_mode": "remote"
}
```
`min_ctc`/`max_ctc` are optional (nullable). `work_mode` is one of `remote`, `hybrid`, `onsite`, `any`.

**PreferencesResponse**: same fields as the request, plus `id`, `user_id`, `created_at`, `updated_at`.

### POST /resume/upload
Multipart upload, field name `file`. Accepts a single PDF (max size configured via `RESUME_MAX_SIZE_MB`, default 5MB).
- 201: `ResumeResponse`
- 400: file missing, wrong extension/content-type, empty, not a valid PDF (magic-byte check), or over the size limit

**ResumeResponse**
```json
{
  "id": 1,
  "user_id": 1,
  "original_filename": "resume.pdf",
  "content_type": "application/pdf",
  "size_bytes": 48213,
  "uploaded_at": "2026-08-04T12:00:00Z",
  "parsed_skills": ["Python", "FastAPI", "PostgreSQL"],
  "parsed_education": ["B.Tech"],
  "parsed_experience_years": 3.0,
  "parsed_at": "2026-08-05T09:00:00Z"
}
```
`parsed_*` fields come from rule-based extraction (see `docs/08_RESUME_PARSER.md`) and are null/empty if nothing was found or parsing failed - this never fails the upload itself.

Remaining endpoints (`/applications`) are implemented in a later phase.

## Implemented (Phase 4)

### GET /jobs
List stored jobs, most recently fetched first.
- Query params: `source` (optional, e.g. `greenhouse`), `limit` (default 50, max 200), `offset` (default 0)
- 200: `list[JobResponse]`

### GET /jobs/{id}
Return a single job by id.
- 200: `JobResponse`
- 404: `{"detail": "No job found with id <id>"}`

**JobResponse**
```json
{
  "id": 1,
  "source": "greenhouse",
  "external_id": "4020123",
  "title": "Backend Engineer",
  "company": "Acme",
  "location": "Remote - US",
  "is_remote": true,
  "description": "Build our API...",
  "apply_url": "https://boards.greenhouse.io/acme/jobs/4020123",
  "posted_at": "2026-08-01T16:00:00Z",
  "fetched_at": "2026-08-06T09:00:00Z"
}
```

### POST /jobs/fetch
Manually runs the fetch pipeline for all four sources (Greenhouse, Lever, Remotive, Arbeitnow) and upserts results. Not in the original endpoint list above - added because the scheduler that will normally trigger this doesn't exist until Phase 8.
- 200: `list[JobFetchSummary]`, one entry per source

**JobFetchSummary**
```json
{"source": "greenhouse", "fetched": 12, "created": 10, "updated": 2, "failed": false}
```
A source with nothing configured (Greenhouse/Lever with no board tokens/company slugs set) still returns a summary with `fetched: 0`, not an error.

## Implemented (Phase 5)

### GET /fetch-logs
List recent job-fetch run history (one entry per source per run), most recent first. Not in the original endpoint list - added since `app/services/job_service` already computes this data on every fetch; this makes it visible instead of discarding it after the response.
- Query params: `source` (optional), `limit` (default 50, max 200)
- 200: `list[FetchLogResponse]`

**FetchLogResponse**
```json
{
  "id": 1,
  "source": "greenhouse",
  "fetched_count": 12,
  "created_count": 10,
  "updated_count": 2,
  "failed": false,
  "started_at": "2026-08-08T09:00:00Z",
  "finished_at": "2026-08-08T09:00:03Z"
}
```

**Note on `POST /applications`, `PATCH /applications/{id}`:** these appear in the original endpoint list above but are *not* implemented yet. They're owned by Phase 10 (Application Tracker), per that phase's explicit task list - see `tasks/PHASE_10_APPLICATION_TRACKER.md`. `GET /notifications` (also originally listed here) is now implemented - see Phase 9 below.

## Implemented (Phase 7)

### GET /matches
Return the top-N jobs ranked against the current user's preferences + latest resume (see `docs/09_MATCHING_ENGINE.md`).
- 200: `list[JobMatchResponse]`, best match first
- 404: `{"detail": "No preferences set for user <id>"}` if preferences haven't been set yet

**JobMatchResponse**
```json
{
  "job": { "...": "same shape as JobResponse" },
  "score": 0.83,
  "text_similarity": 0.61,
  "skill_score": 1.0,
  "role_score": 1.0,
  "location_score": 1.0,
  "experience_score": 1.0,
  "remote_score": 1.0
}
```

## Implemented (Phase 9)

### GET /notifications
List the current user's notifications, most recent first.
- Query params: `unread_only` (default `false`), `limit` (default 50, max 200)
- 200: `list[NotificationResponse]`

**NotificationResponse**
```json
{
  "id": 1,
  "job_id": 42,
  "message": "New match: Backend Engineer at Acme (85% fit)",
  "is_read": false,
  "created_at": "2026-08-12T06:00:00Z"
}
```

### PATCH /notifications/{id}/read
Mark a single notification as read. Not in the original endpoint list - added since "mark as read" is an explicit Phase 9 task.
- 200: `NotificationResponse`
- 404: `{"detail": "No notification found with id <id>"}`

### POST /notifications/mark-all-read
Mark every unread notification for the current user as read. Also not in the original list, added for the same reason.
- 200: `{"updated": <count>}`
