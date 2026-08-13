# Notification System

V1:
- Browser Push Notification
- Dashboard notification
- Daily scheduler

Future:
- Email
- Telegram

## Implementation (Phase 9)

### Backend

- `notifications` table (`app/models/notification.py`, migration `0005`): `user_id`, `job_id` (nullable, for a "view job" link), a fully-formed `message` string, `is_read`, `created_at`.
- **Creation:** `notification_service.create_notifications_for_new_top_matches`, called by `app/scheduler/jobs.py` right after the daily ranking refresh (Phase 8), using that step's already-computed top matches - no separate query. A job is considered "new" (worth notifying about) if its `created_at` and `fetched_at` are within 60 seconds of each other, meaning this fetch run is the first time it's been seen. Since `fetched_at` is bumped on every re-fetch but `created_at` never changes, this naturally stops re-notifying about the same job on day 2+ without any extra bookkeeping.
- **Endpoints:** `GET /notifications` (documented in the original API spec; supports `unread_only` and `limit`), `PATCH /notifications/{id}/read`, and `POST /notifications/mark-all-read` (both new - "mark as read" needs somewhere to go through).

### Frontend ("Dashboard notification" + "Browser Push Notification")

- **Dashboard notification banner** (`dashboard.html`, `js/notifications.js`): polls `GET /notifications?unread_only=true` every 60s while the tab is open, renders a dismissible list with a link to each job, and "mark all as read".
- **Browser notifications:** uses the native `Notification` API (`new Notification(...)`), gated behind an explicit "Enable browser notifications" button (shown only when permission hasn't been granted/denied yet - consent-first, not an auto-prompt on page load). Fires once per notification id (tracked client-side) so re-polling doesn't re-fire the same alert. Clicking a fired notification focuses the tab and navigates to the job.

**Important scope note - this is not true push.** A real Push API implementation (service worker + push subscription + a push server with VAPID keys) would let notifications arrive even when no tab is open, but that's substantial infrastructure not referenced anywhere in the project docs. What's built here only fires while the dashboard tab is open and polling - a deliberate, documented interpretation of "browser push notifications" appropriate for a personal, single-user, no-extra-infrastructure V1 tool. `docs/16_BACKLOG.md`'s "Future: Email, Telegram" section is the natural place a true always-on push/notification channel would eventually land.

### What Phase 9 does *not* do

`applications`/the Application Tracker remain Phase 10's explicit scope - notifications here are read-only regarding job status (no "mark as applied" from a notification).

