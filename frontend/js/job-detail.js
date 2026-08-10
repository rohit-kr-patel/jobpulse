/**
 * Job detail page: reads the job id from the URL query string, fetches
 * it, and renders full details with an apply link.
 */

const containerEl = document.getElementById("job-detail-container");

function renderError(message) {
  const wrapper = document.createElement("div");
  wrapper.className = "empty-state";

  const heading = document.createElement("h2");
  heading.textContent = "Couldn't load this job";

  const text = document.createElement("p");
  text.textContent = message;

  wrapper.append(heading, text);
  containerEl.replaceChildren(wrapper);
}

function renderJob(job) {
  const card = document.createElement("article");
  card.className = "job-detail-card";

  const header = document.createElement("div");
  header.className = "job-detail-header";

  const top = document.createElement("div");
  top.className = "job-card-top";

  const freshness = document.createElement("span");
  freshness.className = "freshness";
  const dot = document.createElement("span");
  dot.className = "pulse-dot" + (hoursSince(job.fetched_at) < 6 ? " is-fresh" : "");
  const freshnessText = document.createElement("span");
  freshnessText.textContent = `fetched ${relativeTime(job.fetched_at)}`;
  freshness.append(dot, freshnessText);

  const sourceTag = document.createElement("span");
  sourceTag.className = "source-tag";
  sourceTag.textContent = job.source;

  top.append(freshness, sourceTag);

  const title = document.createElement("h1");
  title.className = "job-detail-title";
  title.textContent = job.title;

  const meta = document.createElement("div");
  meta.className = "job-detail-meta";
  if (job.is_remote) {
    const remoteBadge = document.createElement("span");
    remoteBadge.className = "remote-badge";
    remoteBadge.textContent = "Remote";
    meta.append(`${job.company} · `, remoteBadge, job.location ? ` · ${job.location}` : "");
  } else {
    meta.textContent = job.location ? `${job.company} · ${job.location}` : job.company;
  }

  const timestamps = document.createElement("div");
  timestamps.className = "job-detail-timestamps";
  const postedText = job.posted_at ? `posted ${relativeTime(job.posted_at)}` : "posted date unknown";
  timestamps.textContent = `${postedText} · fetched ${relativeTime(job.fetched_at)}`;

  header.append(top, title, meta, timestamps);

  const description = document.createElement("p");
  description.className = "job-detail-description";
  description.textContent = job.description || "No description provided.";

  const applyButton = document.createElement("a");
  applyButton.className = "btn btn-primary";
  applyButton.href = job.apply_url;
  applyButton.target = "_blank";
  applyButton.rel = "noopener noreferrer";
  applyButton.textContent = "Apply on company site →";

  card.append(header, description, applyButton);
  containerEl.replaceChildren(card);
}

async function loadJob() {
  const params = new URLSearchParams(window.location.search);
  const jobId = params.get("id");

  if (!jobId) {
    renderError("No job id was given in the URL.");
    return;
  }

  try {
    const job = await apiRequest(`/jobs/${encodeURIComponent(jobId)}`);
    renderJob(job);
  } catch (error) {
    renderError(error.message);
  }
}

loadJob();
