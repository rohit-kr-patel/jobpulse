/**
 * Preferences form: loads existing preferences (if any) to prefill the
 * form, then creates/updates them on submit.
 */

const form = document.getElementById("preferences-form");
const messageEl = document.getElementById("form-message");

function parseCommaSeparatedList(rawValue) {
  return rawValue
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function showMessage(text, isError) {
  messageEl.textContent = text;
  messageEl.className = `form-message ${isError ? "form-message-error" : "form-message-success"}`;
}

function parseOptionalInt(rawValue) {
  if (rawValue === "" || rawValue === null || rawValue === undefined) {
    return null;
  }
  return Number(rawValue);
}

async function loadExistingPreferences() {
  try {
    const preferences = await apiRequest("/preferences");
    form.target_roles.value = preferences.target_roles.join(", ");
    form.skills.value = preferences.skills.join(", ");
    form.locations.value = preferences.locations.join(", ");
    form.experience_years.value = preferences.experience_years;
    form.min_ctc.value = preferences.min_ctc ?? "";
    form.max_ctc.value = preferences.max_ctc ?? "";
    form.work_mode.value = preferences.work_mode;
  } catch (error) {
    // No preferences saved yet is expected on first visit - leave the form blank.
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const targetRoles = parseCommaSeparatedList(form.target_roles.value);
  const skills = parseCommaSeparatedList(form.skills.value);
  const locations = parseCommaSeparatedList(form.locations.value);
  const minCtc = parseOptionalInt(form.min_ctc.value);
  const maxCtc = parseOptionalInt(form.max_ctc.value);

  if (targetRoles.length === 0 || skills.length === 0 || locations.length === 0) {
    showMessage("Target roles, skills, and locations each need at least one value.", true);
    return;
  }

  if (minCtc !== null && maxCtc !== null && maxCtc < minCtc) {
    showMessage("Maximum CTC must be greater than or equal to minimum CTC.", true);
    return;
  }

  const payload = {
    target_roles: targetRoles,
    skills,
    locations,
    experience_years: Number(form.experience_years.value),
    min_ctc: minCtc,
    max_ctc: maxCtc,
    work_mode: form.work_mode.value,
  };

  try {
    await apiRequest("/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showMessage("Preferences saved.", false);
  } catch (error) {
    showMessage(error.message, true);
  }
});

loadExistingPreferences();
