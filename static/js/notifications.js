/** Top-bar notification bell: unread badge + dropdown list + mark-read. */
document.addEventListener("DOMContentLoaded", () => {
  const API = window.API, UI = window.UI;
  if (!API.isAuthenticated()) return;

  const btn = document.getElementById("notif-btn");
  const panel = document.getElementById("notif-panel");
  const badge = document.getElementById("notif-badge");
  const list = document.getElementById("notif-list");
  const readAll = document.getElementById("notif-read-all");
  if (!btn) return;

  const ICON = { COMPLIANCE: "⚠️", CSR: "🤝", GAMIFICATION: "🏆", SYSTEM: "🔔" };

  async function refreshBadge() {
    try {
      const res = await API.request("/notifications/unread_count/");
      if (!res.ok) return;
      const { unread } = await res.json();
      if (unread > 0) {
        badge.textContent = unread > 9 ? "9+" : unread;
        badge.classList.remove("hidden");
      } else {
        badge.classList.add("hidden");
      }
    } catch (e) { /* silent */ }
  }

  async function loadList() {
    list.innerHTML = `<li class="px-4 py-6 text-center text-sm text-odoo-muted">Loading…</li>`;
    try {
      const res = await API.request("/notifications/?page_size=8");
      const data = await res.json();
      const rows = (data.results || data).slice(0, 8);
      if (!rows.length) {
        list.innerHTML = `<li class="px-4 py-6 text-center text-sm text-odoo-muted">No notifications.</li>`;
        return;
      }
      list.innerHTML = rows.map((n) => `
        <li class="px-4 py-3 ${n.is_read ? "" : "bg-odoo-purple/5"}">
          <div class="flex items-start gap-2">
            <span>${ICON[n.category] || "🔔"}</span>
            <div class="min-w-0">
              <p class="truncate text-sm text-odoo-text">${UI.escapeHtml(n.title)}</p>
              <p class="text-xs text-odoo-muted">${UI.fmtDate(n.created_at)}</p>
            </div>
          </div>
        </li>`).join("");
    } catch (e) {
      list.innerHTML = `<li class="px-4 py-6 text-center text-sm text-red-600">Failed to load.</li>`;
    }
  }

  function toggle(open) {
    const show = open ?? panel.classList.contains("hidden");
    panel.classList.toggle("hidden", !show);
    if (show) loadList();
  }

  btn.addEventListener("click", (e) => { e.stopPropagation(); toggle(); });
  document.addEventListener("click", (e) => {
    if (!panel.contains(e.target) && !btn.contains(e.target)) panel.classList.add("hidden");
  });
  readAll.addEventListener("click", async () => {
    await API.request("/notifications/read_all/", { method: "POST" }).catch(() => {});
    await Promise.all([loadList(), refreshBadge()]);
  });

  refreshBadge();
});
