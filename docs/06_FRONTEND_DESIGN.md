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

**Not built:** Login (V1 has no auth - see `docs/15_PROJECT_SCOPE.md`/`TODO.md`) and Notification Banner, which is Phase 9's explicit scope (`tasks/PHASE_09_BROWSER_NOTIFICATIONS.md`).

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

### Known limitation

The dashboard fetches only the 200 most recent jobs (`GET /jobs`'s max `limit`) and filters/searches entirely client-side - there's no server-side search or pagination-aware filtering yet. Fine at V1's personal, single-user scale; would need a real search/filter query param on `GET /jobs` if the job count grows meaningfully past a few hundred.

### Verification

No visual/browser rendering was available in the build environment, so behavior was verified two ways: `node --check` for JS syntax validity, and a `jsdom`-based harness (temporary, not part of the deliverable) that loaded each page's real HTML/CSS/JS, mocked `fetch` with representative API responses, and asserted on the resulting DOM - covering stats computation, freshness-dot logic, both filter interactions, the job-detail render and its 404 path, and both dashboard empty-state variants.
