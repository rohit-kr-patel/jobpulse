# Frontend Design

Pages:
- Login (optional/simple)
- Dashboard
- Job Details
- Preferences
- Resume Upload

Components:
- Job Card
- Filters
- Notification Banner
- Stats Cards

## Implementation (Phase 6)

Built: **Dashboard** (`dashboard.html`), **Job Details** (`job-detail.html`), **Job Card**, **Filters**, **Stats Cards**. Vanilla HTML/CSS/JS throughout, no framework or build step, consistent with `docs/03_TECH_STACK.md`.

**Not built:** Login - V1 has no auth, see `docs/15_PROJECT_SCOPE.md`/`TODO.md`. (Notification Banner was deferred here to Phase 9, and is now built - see below.)

### Design system

Introduced a token system in `css/style.css` (`:root` custom properties), extended by `css/dashboard.css` for dashboard-specific components:
- **Color:** cool-neutral canvas/surface (`--canvas #F3F5F8`, `--surface #FFFFFF`) with a teal "pulse" accent (`--pulse #0FA3A0`) as the signal color for freshness/primary actions, and an amber (`--signal #F5A524`) reserved for the remote badge.
- **Type:** Space Grotesk for headings/titles/stat numbers, Inter for body/UI text, JetBrains Mono for metadata (source tags, timestamps, filter counts) - loaded via Google Fonts, a deliberate three-role pairing rather than a single default sans stack.
- **Signature element:** a small "pulse" dot on every job card that gently animates (respecting `prefers-reduced-motion`) when a job was fetched within the last 6 hours, paired with a relative-time label ("fetched 2h ago"). This is a real signal computed from `fetched_at`, not decoration, and ties directly to the product name.

This token update also refined the shared styling used by `preferences.html`/`resume-upload.html`/`index.html` from earlier phases (same structure, refined colors/type) so the whole app now shares one coherent visual identity instead of the Phase 1 placeholder look.

### Dashboard (`dashboard.html`, `js/dashboard.js`)

- Fetches up to 200 most-recently-fetched jobs from `GET /jobs` on load (no new backend endpoint - existing pagination is reused; see known limitation below).
- **Stats cards:** total jobs, remote count, distinct source count, and "last fetched" (relative time) - all computed client-side from the fetched job list.
- **Filters:** free-text search (title/company), source dropdown, remote-only checkbox - all applied client-side, live (no submit needed).
- **Refresh jobs button:** calls `POST /jobs/fetch` (built in Phase 4), shows a one-line summary of the result, then reloads the job list.
- **Empty states:** distinguish "no jobs fetched yet" (with guidance to configure a source and hit Refresh) from "no jobs match these filters" (with guidance to loosen them).
- Job cards and job details are built via `document.createElement`/`textContent`, never `innerHTML` with interpolated API data, since job titles/descriptions come from third-party sources and must not be trusted as HTML.

### Job Details (`job-detail.html`, `js/job-detail.js`)

Reads `?id=` from the URL, fetches `GET /jobs/{id}`, and renders the full (untruncated) description, posted/fetched timestamps, and an "Apply on company site" link (opens in a new tab via `target="_blank" rel="noopener noreferrer"`). A missing or unknown id renders a clear inline error with guidance back to the dashboard, rather than a blank page.

### Notification Banner (`dashboard.html`, `js/notifications.js`) - Phase 9

The component deferred from Phase 6. Polls `GET /notifications?unread_only=true` every 60 seconds while the dashboard tab is open; renders a dismissible banner listing each unread notification (linking to its job), a "Mark all as read" action, and - only when the browser's Notification permission hasn't been decided yet - an explicit "Enable browser notifications" button (consent-first, not an auto-prompt on page load). Newly-seen notifications also fire a native `Notification`, tracked client-side by id so re-polling never re-fires the same alert; clicking a fired notification focuses the tab and navigates to the job. See `docs/10_NOTIFICATION_SYSTEM.md` for why this is polling + the Notification API rather than true push.

### Application Tracking (`job-detail.html`, `js/job-detail.js`) - Phase 10

A "Your tracking" section on the job detail page: current status (with a relative-time note once applied/rejected), three buttons - Save / Mark Applied / Mark Rejected, the active one disabled - and a notes textarea. There's no "get application by job id" endpoint, so like the dashboard's job list, this fetches the bounded `GET /applications` list and matches client-side by job id. An "expired" badge appears next to the source tag for jobs marked expired.

### My Applications (`applications.html`, `js/applications.js`) - Phase 10

The application history view - not one of the five pages originally listed above, added because "application history" is an explicit Phase 10 task with nowhere else to live. Every tracked application, filterable by status, each showing the job, status, notes preview, and a saved/applied/rejected timeline, linking back to its job detail page.

### Known limitation

The dashboard fetches only the 200 most recent jobs (`GET /jobs`'s max `limit`) and filters/searches entirely client-side - there's no server-side search or pagination-aware filtering yet. Fine at V1's personal, single-user scale; would need a real search/filter query param on `GET /jobs` if the job count grows meaningfully past a few hundred.

### Verification

No visual/browser rendering was available in the build environment, so behavior was verified two ways: `node --check` for JS syntax validity, and a `jsdom`-based harness (temporary, not part of the deliverable) that loaded each page's real HTML/CSS/JS, mocked `fetch` with representative API responses, and asserted on the resulting DOM - covering stats computation, freshness-dot logic, both filter interactions, the job-detail render and its 404 path, and both dashboard empty-state variants.
