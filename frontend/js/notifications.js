/**
 * Notification banner + browser notifications.
 *
 * "Browser push notifications" here means the native Notification API,
 * fired while this dashboard tab is open and polling for new unread
 * notifications - not true push (which would need a service worker and
 * a push subscription server, out of scope for a personal V1 tool with
 * no such infrastructure). See docs/10_NOTIFICATION_SYSTEM.md.
 */

const POLL_INTERVAL_MS = 60_000;

const bannerEl = document.getElementById("notification-banner");
const listEl = document.getElementById("notification-list");
const markAllReadButton = document.getElementById("mark-all-read-button");
const enableNotificationsButton = document.getElementById("enable-notifications-button");

const notifiedIds = new Set();

function updateEnableButtonVisibility() {
  const supported = "Notification" in window;
  enableNotificationsButton.hidden = !supported || Notification.permission !== "default";
}

function fireBrowserNotification(notification) {
  if (!("Notification" in window) || Notification.permission !== "granted") {
    return;
  }
  const browserNotification = new Notification("JobPulse", { body: notification.message });
  browserNotification.onclick = () => {
    window.focus();
    if (notification.job_id) {
      window.location.href = `job-detail.html?id=${encodeURIComponent(notification.job_id)}`;
    }
  };
}

function renderNotifications(notifications) {
  if (notifications.length === 0) {
    bannerEl.hidden = true;
    listEl.replaceChildren();
    return;
  }

  bannerEl.hidden = false;
  const items = notifications.map((notification) => {
    const li = document.createElement("li");
    li.className = "notification-item";

    const link = document.createElement("a");
    link.textContent = notification.message;
    link.href = notification.job_id
      ? `job-detail.html?id=${encodeURIComponent(notification.job_id)}`
      : "#";

    const dismissButton = document.createElement("button");
    dismissButton.className = "notification-dismiss";
    dismissButton.type = "button";
    dismissButton.setAttribute("aria-label", "Mark as read");
    dismissButton.textContent = "×";
    dismissButton.addEventListener("click", () => markNotificationRead(notification.id));

    li.append(link, dismissButton);
    return li;
  });

  listEl.replaceChildren(...items);
}

async function markNotificationRead(notificationId) {
  try {
    await apiRequest(`/notifications/${encodeURIComponent(notificationId)}/read`, { method: "PATCH" });
    await loadNotifications();
  } catch (error) {
    console.error("Failed to mark notification as read:", error);
  }
}

async function markAllNotificationsRead() {
  try {
    await apiRequest("/notifications/mark-all-read", { method: "POST" });
    await loadNotifications();
  } catch (error) {
    console.error("Failed to mark all notifications as read:", error);
  }
}

async function loadNotifications() {
  let notifications;
  try {
    notifications = await apiRequest("/notifications?unread_only=true&limit=20");
  } catch (error) {
    console.error("Failed to load notifications:", error);
    return;
  }

  const freshOnes = notifications.filter((notification) => !notifiedIds.has(notification.id));
  freshOnes.forEach((notification) => {
    notifiedIds.add(notification.id);
    fireBrowserNotification(notification);
  });

  renderNotifications(notifications);
}

enableNotificationsButton.addEventListener("click", async () => {
  await Notification.requestPermission();
  updateEnableButtonVisibility();
});

markAllReadButton.addEventListener("click", markAllNotificationsRead);

updateEnableButtonVisibility();
loadNotifications();
setInterval(loadNotifications, POLL_INTERVAL_MS);
