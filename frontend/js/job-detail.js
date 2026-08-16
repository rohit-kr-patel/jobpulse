/**
 * Job detail page: reads the job id from the URL query string, fetches
 * it, and renders full details with an apply link plus application
 * tracking controls (save / mark applied / mark rejected / notes).
 */

const containerEl = document.getElementById("job-detail-container");

const STATUS_LABELS = { saved: "Saved", applied: "Applied", rejected: "Rejected" };

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

  const tags = document.createElement("div");
  tags.className = "job-card-top";
  const sourceTag = document.createElement("span");
  sourceTag.className = "source-tag";
  sourceTag.textContent = job.source;
  tags.append(sourceTag);
  if (job.is_expired) {
    const expiredTag = document.createElement("span");
    expiredTag.className = "source-tag expired-tag";
    expiredTag.textContent = "expired";
    tags.append(expiredTag);
  }

  top.append(freshness, tags);

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

  const trackingSection = document.createElement("div");
  trackingSection.id = "tracking-section";
  trackingSection.className = "tracking-section";

  card.append(header, description, applyButton, trackingSection);
  containerEl.replaceChildren(card);
}

function renderTracking(job, application) {
  const section = document.getElementById("tracking-section");
  section.replaceChildren();

  const heading = document.createElement("h2");
  heading.textContent = "Your tracking";

  const statusText = document.createElement("p");
  statusText.className = "tracking-status";
  if (application) {
    let detail = STATUS_LABELS[application.status];
    if (application.status === "applied" && application.applied_at) {
      detail += ` · ${relativeTime(application.applied_at)}`;
    } else if (application.status === "rejected" && application.rejected_at) {
      detail += ` · ${relativeTime(application.rejected_at)}`;
    }
    statusText.textContent = `Status: ${detail}`;
  } else {
    statusText.textContent = "Not tracked yet";
  }

  const buttonRow = document.createElement("div");
  buttonRow.className = "tracking-buttons";
  Object.entries(STATUS_LABELS).forEach(([statusValue, label]) => {
    const button = document.createElement("button");
    button.className = "btn btn-secondary";
    button.type = "button";
    button.textContent = label === "Saved" ? "Save" : `Mark ${label}`;
    button.disabled = application?.status === statusValue;
    button.addEventListener("click", () => setApplicationStatus(job, application, statusValue));
    buttonRow.appendChild(button);
  });

  const notesLabel = document.createElement("label");
  notesLabel.setAttribute("for", "tracking-notes");
  notesLabel.textContent = "Notes";

  const notesTextarea = document.createElement("textarea");
  notesTextarea.id = "tracking-notes";
  notesTextarea.rows = 3;
  notesTextarea.value = application?.notes || "";

  const saveNotesButton = document.createElement("button");
  saveNotesButton.className = "btn btn-secondary";
  saveNotesButton.type = "button";
  saveNotesButton.textContent = "Save notes";
  saveNotesButton.addEventListener("click", () => saveNotes(job, application, notesTextarea.value));

  const trackingMessage = document.createElement("p");
  trackingMessage.id = "tracking-message";
  trackingMessage.className = "form-message";

  section.append(heading, statusText, buttonRow, notesLabel, notesTextarea, saveNotesButton, trackingMessage);
}

function showTrackingMessage(text, isError) {
  const el = document.getElementById("tracking-message");
  el.textContent = text;
  el.className = `form-message ${isError ? "form-message-error" : "form-message-success"}`;
}

async function setApplicationStatus(job, existingApplication, newStatus) {
  try {
    const updated = existingApplication
      ? await apiRequest(`/applications/${existingApplication.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: newStatus }),
        })
      : await apiRequest("/applications", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_id: job.id, status: newStatus }),
        });
    renderTracking(job, updated);
    showTrackingMessage("Saved.", false);
  } catch (error) {
    showTrackingMessage(error.message, true);
  }
}

async function saveNotes(job, existingApplication, notes) {
  try {
    const updated = existingApplication
      ? await apiRequest(`/applications/${existingApplication.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ notes }),
        })
      : await apiRequest("/applications", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_id: job.id, notes }),
        });
    renderTracking(job, updated);
    showTrackingMessage("Notes saved.", false);
  } catch (error) {
    showTrackingMessage(error.message, true);
  }
}

async function loadTracking(job) {
  let applications;
  try {
    applications = await apiRequest("/applications");
  } catch (error) {
    console.error("Failed to load application tracking:", error);
    applications = [];
  }
  const existing = applications.find((application) => application.job.id === job.id);
  renderTracking(job, existing);
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
    await loadTracking(job);
  } catch (error) {
    renderError(error.message);
  }
}

loadJob();
