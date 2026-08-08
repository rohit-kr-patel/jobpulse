/**
 * Shared API helper for all frontend pages.
 */

const API_BASE_URL = "http://localhost:8000";

/**
 * Perform a JSON request and return the parsed body.
 * Throws an Error with the backend's detail message on non-2xx responses.
 */
async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await response.json() : null;

  if (!response.ok) {
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
      : detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return body;
}
