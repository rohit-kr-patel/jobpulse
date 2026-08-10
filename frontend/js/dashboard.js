/**
 * Dashboard: loads jobs from GET /jobs, computes stats client-side,
 * applies search/source/remote filters, and renders job cards.
 * "Refresh jobs" triggers POST /jobs/fetch (built in Phase 4) then reloads.
 */

const JOB_FETCH_LIMIT = 200;
const FRESH_WITHIN_HOURS = 6;

const SOURCE_LABELS = {
  greenhouse: "Greenhouse",
  lever: "Lever",
  remotive: "Remotive",
  arbeitnow: "Arbeitnow",
};

let allJobs = [];

const resultsEl = document.getElementById("job-results");
const fetchSummaryEl = document.getElementById("fetch-summary");
const refreshButton = document.getElementById("refresh-button");
const searchInput = document.getElementById("filter-search");
const sourceSelect = document.getElementById("filter-source");
const remoteCheckbox = document.getElementById("filter-remote");
const filterCountEl = document.getElementById("filter-count");
const filterForm = document.getElementById("filter-form");

function computeStats(jobs) {
  const total = jobs.length;
  const remoteCount = jobs.filter((job) => job.is_remote).length;
  const sourceCount = new Set(jobs.map((job) => job.source)).size;
  const lastFetched = jobs.reduce((latest, job) => {
    return !latest || new Date(job.fetched_at) > new Date(latest) ? job.fetched_at : latest;
  }, null);

  document.getElementById("stat-total").textContent = String(total);
  document.getElementById("stat-remote").textContent = String(remoteCount);
  document.getElementById("stat-sources").textContent = String(sourceCount);
  document.getElementById("stat-last-fetched").textContent = lastFetched
    ? relativeTime(lastFetched)
    : "never";
}

function createJobCard(job) {
  const card = document.createElement("a");
  card.className = "job-card";
  card.href = `job-detail.html?id=${encodeURIComponent(job.id)}`;

  const top = document.createElement("div");
  top.className = "job-card-top";

  const freshness = document.createElement("span");
  freshness.className = "freshness";
  const dot = document.createElement("span");
  dot.className = "pulse-dot" + (hoursSince(job.fetched_at) < FRESH_WITHIN_HOURS ? " is-fresh" : "");
  const freshnessText = document.createElement("span");
  freshnessText.textContent = `fetched ${relativeTime(job.fetched_at)}`;
  freshness.append(dot, freshnessText);

  const sourceTag = document.createElement("span");
  sourceTag.className = "source-tag";
  sourceTag.textContent = job.source;

  top.append(freshness, sourceTag);

  const title = document.createElement("h3");
  title.className = "job-title";
  title.textContent = job.title;

  const meta = document.createElement("div");
  meta.className = "job-meta";
  if (job.is_remote) {
    const remoteBadge = document.createElement("span");
    remoteBadge.className = "remote-badge";
    remoteBadge.textContent = "Remote";
    meta.append(`${job.company} · `, remoteBadge, job.location ? ` · ${job.location}` : "");
  } else {
    meta.textContent = job.location ? `${job.company} · ${job.location}` : job.company;
  }

  const snippet = document.createElement("p");
  snippet.className = "job-description-snippet";
  snippet.textContent = job.description;

  const viewLink = document.createElement("span");
  viewLink.className = "view-link";
  viewLink.textContent = "View details →";

  card.append(top, title, meta, snippet, viewLink);
  return card;
}

function renderEmptyState() {
  const wrapper = document.createElement("div");
  wrapper.className = "empty-state";

  const heading = document.createElement("h2");
  const message = document.createElement("p");

  if (allJobs.length === 0) {
    heading.textContent = "No jobs yet";
    message.textContent =
      "Configure a source in .env (Greenhouse/Lever board tokens, or none needed for Remotive/Arbeitnow) and hit Refresh jobs.";
  } else {
    heading.textContent = "No jobs match these filters";
    message.textContent = "Try a different search term, source, or turn off Remote only.";
  }

  wrapper.append(heading, message);
  resultsEl.replaceChildren(wrapper);
}

function applyFiltersAndRender() {
  const searchTerm = searchInput.value.trim().toLowerCase();
  const sourceFilter = sourceSelect.value;
  const remoteOnly = remoteCheckbox.checked;

  const filtered = allJobs.filter((job) => {
    if (sourceFilter && job.source !== sourceFilter) return false;
    if (remoteOnly && !job.is_remote) return false;
    if (searchTerm) {
      const haystack = `${job.title} ${job.company}`.toLowerCase();
      if (!haystack.includes(searchTerm)) return false;
    }
    return true;
  });

  filterCountEl.textContent = `${filtered.length} of ${allJobs.length} jobs`;

  if (filtered.length === 0) {
    renderEmptyState();
    return;
  }

  const grid = document.createElement("div");
  grid.className = "job-grid";
  filtered.forEach((job) => grid.appendChild(createJobCard(job)));
  resultsEl.replaceChildren(grid);
}

async function loadJobs() {
  try {
    allJobs = await apiRequest(`/jobs?limit=${JOB_FETCH_LIMIT}`);
  } catch (error) {
    resultsEl.replaceChildren(Object.assign(document.createElement("div"), {
      className: "empty-state",
      textContent: `Couldn't load jobs: ${error.message}`,
    }));
    return;
  }
  computeStats(allJobs);
  applyFiltersAndRender();
}

async function refreshJobs() {
  refreshButton.disabled = true;
  refreshButton.textContent = "Refreshing...";
  fetchSummaryEl.textContent = "";

  try {
    const summaries = await apiRequest("/jobs/fetch", { method: "POST" });
    const totalCreated = summaries.reduce((sum, s) => sum + s.created, 0);
    const totalUpdated = summaries.reduce((sum, s) => sum + s.updated, 0);
    const failedSources = summaries.filter((s) => s.failed).map((s) => s.source);

    let summaryText = `Fetched: ${totalCreated} new, ${totalUpdated} updated.`;
    if (failedSources.length > 0) {
      summaryText += ` Failed: ${failedSources.join(", ")}.`;
    }
    fetchSummaryEl.textContent = summaryText;

    await loadJobs();
  } catch (error) {
    fetchSummaryEl.textContent = `Refresh failed: ${error.message}`;
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent = "Refresh jobs";
  }
}

refreshButton.addEventListener("click", refreshJobs);
searchInput.addEventListener("input", applyFiltersAndRender);
sourceSelect.addEventListener("change", applyFiltersAndRender);
remoteCheckbox.addEventListener("change", applyFiltersAndRender);
filterForm.addEventListener("submit", (event) => event.preventDefault());

loadJobs();
