/**
 * Resume upload form: validates the file client-side, then uploads it
 * as multipart/form-data.
 */

const form = document.getElementById("resume-form");
const messageEl = document.getElementById("form-message");
const parsedResultsEl = document.getElementById("parsed-results");
const MAX_SIZE_BYTES = 5 * 1024 * 1024;

function showMessage(text, isError) {
  messageEl.textContent = text;
  messageEl.className = `form-message ${isError ? "form-message-error" : "form-message-success"}`;
}

function renderParsedResults(resume) {
  const skills = resume.parsed_skills?.length ? resume.parsed_skills.join(", ") : "none detected";
  const education = resume.parsed_education?.length
    ? resume.parsed_education.join(", ")
    : "none detected";
  const experience =
    resume.parsed_experience_years !== null ? `${resume.parsed_experience_years} years` : "not detected";

  parsedResultsEl.innerHTML = `
    <h2>What we found</h2>
    <p><strong>Skills:</strong> ${skills}</p>
    <p><strong>Education:</strong> ${education}</p>
    <p><strong>Experience:</strong> ${experience}</p>
    <p class="field-hint">Rule-based extraction - review for accuracy.</p>
  `;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const fileInput = document.getElementById("resume_file");
  const file = fileInput.files[0];

  if (!file) {
    showMessage("Please choose a PDF file first.", true);
    return;
  }

  parsedResultsEl.innerHTML = "";

  if (!file.name.toLowerCase().endsWith(".pdf") || file.type !== "application/pdf") {
    showMessage("Only PDF files are accepted.", true);
    return;
  }

  if (file.size > MAX_SIZE_BYTES) {
    showMessage("File exceeds the 5MB size limit.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const resume = await apiRequest("/resume/upload", {
      method: "POST",
      body: formData,
    });
    showMessage(`Uploaded "${resume.original_filename}" successfully.`, false);
    renderParsedResults(resume);
    form.reset();
  } catch (error) {
    showMessage(error.message, true);
  }
});
