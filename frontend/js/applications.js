/**
 * Application history: lists every tracked application, filterable by status.
 */

let allApplications = [];

const listEl = document.getElementById("applications-list");
const statusSelect = document.getElementById("filter-status");
const filterCountEl = document.getElementById("filter-count");

const STATUS_LABELS = { saved: "Saved", applied: "Applied", rejected: "Rejected" };

function createApplicationRow(application) {
  const row = document.createElement("a");
  row.className = "job-card";
  row.href = `job-detail.html?id=${encodeURIComponent(application.job.id)}`;

  const top = document.createElement("div");
  top.className = "job-card-top";

  const statusTag = document.createElement("span");
  statusTag.className = "source-tag";
  statusTag.textContent = STATUS_LABELS[application.status];

  const sourceTag = document.createElement("span");
  sourceTag.className = "source-tag";
  sourceTag.textContent = application.job.source;

  top.append(statusTag, sourceTag);

  const title = document.createElement("h3");
  title.className = "job-title";
  title.textContent = application.job.title;

  const meta = document.createElement("div");
  meta.className = "job-meta";
  meta.textContent = application.job.location
    ? `${application.job.company} · ${application.job.location}`
    : application.job.company;

  const timeline = document.createElement("p");
  timeline.className = "job-description-snippet";
  timeline.textContent = `Saved ${relativeTime(application.created_at)}`;
  if (application.status === "applied" && application.applied_at) {
    timeline.textContent += ` · Applied ${relativeTime(application.applied_at)}`;
  } else if (application.status === "rejected" && application.rejected_at) {
    timeline.textContent += ` · Rejected ${relativeTime(application.rejected_at)}`;
  }

  row.append(top, title, meta, timeline);

  if (application.notes) {
    const notes = document.createElement("p");
    notes.className = "job-description-snippet";
    notes.textContent = `Notes: ${application.notes}`;
    row.appendChild(notes);
  }

  return row;
}

function renderEmptyState() {
  const wrapper = document.createElement("div");
  wrapper.className = "empty-state";

  const heading = document.createElement("h2");
  const message = document.createElement("p");

  if (allApplications.length === 0) {
    heading.textContent = "No applications tracked yet";
    message.textContent = "Open a job from the dashboard and hit Save to start tracking it here.";
  } else {
    heading.textContent = "No applications match this filter";
    message.textContent = "Try a different status.";
  }

  wrapper.append(heading, message);
  listEl.replaceChildren(wrapper);
}

function applyFilterAndRender() {
  const statusFilter = statusSelect.value;
  const filtered = statusFilter
    ? allApplications.filter((application) => application.status === statusFilter)
    : allApplications;

  filterCountEl.textContent = `${filtered.length} of ${allApplications.length}`;

  if (filtered.length === 0) {
    renderEmptyState();
    return;
  }

  const grid = document.createElement("div");
  grid.className = "job-grid";
  filtered.forEach((application) => grid.appendChild(createApplicationRow(application)));
  listEl.replaceChildren(grid);
}

async function loadApplications() {
  try {
    allApplications = await apiRequest("/applications");
  } catch (error) {
    listEl.replaceChildren(
      Object.assign(document.createElement("div"), {
        className: "empty-state",
        textContent: `Couldn't load applications: ${error.message}`,
      })
    );
    return;
  }
  applyFilterAndRender();
}

statusSelect.addEventListener("change", applyFilterAndRender);
document.getElementById("filter-form").addEventListener("submit", (event) => event.preventDefault());

loadApplications();
