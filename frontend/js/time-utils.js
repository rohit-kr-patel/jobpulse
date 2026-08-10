/**
 * Shared time-formatting helpers for the dashboard and job-detail pages.
 */

function hoursSince(isoString) {
  const thenMs = new Date(isoString).getTime();
  return (Date.now() - thenMs) / (1000 * 60 * 60);
}

function relativeTime(isoString) {
  const diffHours = hoursSince(isoString);
  if (diffHours < 1 / 60) return "just now";
  if (diffHours < 1) return `${Math.floor(diffHours * 60)}m ago`;
  if (diffHours < 24) return `${Math.floor(diffHours)}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}
