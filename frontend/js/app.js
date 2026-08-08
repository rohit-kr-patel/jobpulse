/**
 * Phase 1 sanity check only: pings the backend /health endpoint and
 * reflects its status. Real dashboard logic is built in Phase 6.
 */

const API_BASE_URL = "http://localhost:8000";

async function checkApiStatus() {
  const statusEl = document.getElementById("api-status");
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Unexpected status code: ${response.status}`);
    }
    const data = await response.json();
    statusEl.textContent = `${data.status} (database: ${data.database})`;
  } catch (error) {
    statusEl.textContent = "unreachable";
    console.error("Failed to reach backend /health endpoint:", error);
  }
}

checkApiStatus();
