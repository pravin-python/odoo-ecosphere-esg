/** Renders the active module tab: data tables, cards, and interactive flows. */
(function () {
  "use strict";
  const API = window.API, UI = window.UI, Toast = window.Toast;

  // ── Reports each module's Export button maps to ──
  const MODULE_REPORT = {
    environmental: "ENVIRONMENTAL", social: "SOCIAL",
    governance: "GOVERNANCE", gamification: "ESG_SUMMARY",
    reports: "ESG_SUMMARY", settings: "ESG_SUMMARY",
  };

  // ── helpers ──
  async function listFetch(endpoint) {
    const res = await API.request(endpoint);
    if (!res.ok) throw new Error("load failed");
    const data = await res.json();
    return Array.isArray(data) ? data : data.results || [];
  }
  async function post(path) {
    const res = await API.request(path, { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || firstErr(data) || "Action failed");
    return data;
  }
  function firstErr(data) {
    if (!data || typeof data !== "object") return "";
    const k = Object.keys(data)[0];
    if (!k) return "";
    const v = data[k];
    return Array.isArray(v) ? v[0] : v;
  }
  function pill(text, cls) {
    return `<span class="rounded-full px-2 py-0.5 text-xs font-medium ${cls}">${UI.escapeHtml(text)}</span>`;
  }
  function statusPill(status, label) {
    const map = {
      APPROVED: "bg-green-100 text-green-700", ACHIEVED: "bg-green-100 text-green-700",
      RESOLVED: "bg-green-100 text-green-700", ACTIVE: "bg-blue-100 text-blue-700",
      PENDING: "bg-amber-100 text-amber-700", OPEN: "bg-amber-100 text-amber-700",
      IN_PROGRESS: "bg-blue-100 text-blue-700", REJECTED: "bg-red-100 text-red-700",
      MISSED: "bg-red-100 text-red-700",
    };
    return pill(label || status, map[status] || "bg-gray-100 text-gray-600");
  }
  function severityPill(sev, label) {
    const map = { LOW: "bg-gray-100 text-gray-600", MEDIUM: "bg-blue-100 text-blue-700",
      HIGH: "bg-amber-100 text-amber-700", CRITICAL: "bg-red-100 text-red-700" };
    return pill(label || sev, map[sev] || "bg-gray-100 text-gray-600");
  }

  /** Generic table view with optional per-row actions + action handlers. */
  function tableView(endpoint, columns, actionsFn, handlers) {
    return function (mount) {
      async function load() {
        mount.innerHTML = UI.spinner();
        let rows;
        try { rows = await listFetch(endpoint); }
        catch (e) { mount.innerHTML = UI.errorBox("Could not load data."); return; }
        if (!rows.length) { mount.innerHTML = UI.empty("No records yet."); return; }
        mount.innerHTML = UI.table(columns, rows, actionsFn);
        if (handlers) wireActions(mount, handlers, load);
      }
      load();
    };
  }
  function wireActions(mount, handlers, reload) {
    mount.querySelectorAll("[data-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const fn = handlers[btn.dataset.act];
        if (!fn) return;
        btn.disabled = true;
        try { await fn(btn.dataset.id); await reload(); }
        catch (e) { Toast.error(e.message || "Action failed"); btn.disabled = false; }
      });
    });
  }

  // ── Column sets ──
  const COLS = {
    emissionFactors: [
      { label: "Name", key: "name" },
      { label: "Source", render: (r) => UI.escapeHtml(r.source_type_label) },
      { label: "Unit", render: (r) => UI.escapeHtml(r.unit_label) },
      { label: "Factor (kg CO₂e)", render: (r) => UI.fmtNum(r.factor_value) },
      { label: "Effective", render: (r) => UI.fmtDate(r.effective_from) },
      { label: "Active", render: (r) => UI.boolPill(r.is_active) },
    ],
    products: [
      { label: "Name", key: "name" }, { label: "SKU", key: "sku" },
      { label: "Carbon (kg)", render: (r) => UI.fmtNum(r.carbon_footprint_kg) },
      { label: "Recyclable", render: (r) => UI.boolPill(r.recyclable) },
      { label: "Ethics", render: (r) => `${r.ethical_sourcing_score}/100` },
    ],
    carbon: [
      { label: "Date", render: (r) => UI.fmtDate(r.occurred_on) },
      { label: "Department", key: "department_name" },
      { label: "Source", render: (r) => UI.escapeHtml(r.source_type_label) },
      { label: "Quantity", render: (r) => UI.fmtNum(r.quantity) },
      { label: "CO₂e (kg)", render: (r) => `<span class="font-medium text-green-600">${UI.fmtNum(r.co2e_kg)}</span>` },
    ],
    goals: [
      { label: "Title", key: "title" }, { label: "Department", key: "department_name" },
      { label: "Metric", render: (r) => UI.escapeHtml(r.metric_label) },
      { label: "Target", render: (r) => UI.fmtNum(r.target_value) },
      { label: "Target Date", render: (r) => UI.fmtDate(r.target_date) },
      { label: "Status", render: (r) => statusPill(r.status, r.status_label) },
    ],
    policies: [
      { label: "Title", key: "title" },
      { label: "Pillar", render: (r) => UI.escapeHtml(r.pillar_label) },
      { label: "Version", key: "version" },
      { label: "Effective", render: (r) => UI.fmtDate(r.effective_date) },
      { label: "Active", render: (r) => UI.boolPill(r.is_active) },
    ],
    audits: [
      { label: "Title", key: "title" }, { label: "Department", key: "department_name" },
      { label: "Type", render: (r) => UI.escapeHtml(r.audit_type_label) },
      { label: "Scheduled", render: (r) => UI.fmtDate(r.scheduled_date) },
      { label: "Status", render: (r) => statusPill(r.status, r.status_label) },
    ],
    issues: [
      { label: "Title", key: "title" }, { label: "Audit", key: "audit_title" },
      { label: "Owner", key: "owner_name" },
      { label: "Severity", render: (r) => severityPill(r.severity, r.severity_label) },
      { label: "Due", render: (r) => UI.fmtDate(r.due_date) },
      { label: "Status", render: (r) => r.is_overdue
          ? pill("OVERDUE", "bg-red-100 text-red-700 font-semibold")
          : statusPill(r.status, r.status_label) },
    ],
    challenges: [
      { label: "Title", key: "title" },
      { label: "Difficulty", render: (r) => UI.escapeHtml(r.difficulty_label) },
      { label: "XP", key: "xp_reward" },
      { label: "Deadline", render: (r) => UI.fmtDate(r.deadline) },
      { label: "Status", render: (r) => statusPill(r.status, r.status_label) },
    ],
    challengeParticipation: [
      { label: "Challenge", key: "challenge_title" }, { label: "Employee", key: "employee_name" },
      { label: "Progress", render: (r) => `${r.progress}%` },
      { label: "Status", render: (r) => statusPill(r.status, r.status_label) },
    ],
    departments: [
      { label: "Name", key: "name" }, { label: "Code", key: "code" },
      { label: "Manager", key: "manager_name" },
      { label: "CO₂e (kg)", render: (r) => UI.fmtNum(r.total_co2e_kg) },
      { label: "Active", render: (r) => UI.boolPill(r.is_active) },
    ],
    categories: [
      { label: "Name", key: "name" },
      { label: "Type", render: (r) => UI.escapeHtml(r.type_label) },
      { label: "Description", key: "description" },
      { label: "Active", render: (r) => UI.boolPill(r.is_active) },
    ],
  };

  // ── Special views ──
  function csrView(mount) {
    async function load() {
      mount.innerHTML = UI.spinner();
      let acts;
      try { acts = await listFetch("/social/activities/"); }
      catch (e) { mount.innerHTML = UI.errorBox("Could not load activities."); return; }
      if (!acts.length) { mount.innerHTML = UI.empty("No active CSR activities."); return; }
      mount.innerHTML = `<div class="grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3">${acts.map(csrCard).join("")}</div>`;
      mount.querySelectorAll("[data-join]").forEach((b) =>
        b.addEventListener("click", () => openJoin(b.dataset.join, b.dataset.title)));
    }
    load();
  }
  function csrCard(a) {
    return `<div class="rounded-xl border border-odoo-border bg-white p-5 shadow-sm">
      <h3 class="font-semibold text-odoo-text">${UI.escapeHtml(a.title)}</h3>
      <p class="mt-1 text-xs font-medium text-odoo-teal">${UI.escapeHtml(a.category_label)} · ${a.xp_reward} XP</p>
      <p class="mt-2 text-sm text-odoo-muted">${a.participant_count} joined · Evidence required</p>
      <button data-join="${a.id}" data-title="${UI.escapeHtml(a.title)}"
        class="mt-4 rounded-lg bg-odoo-teal px-3 py-1.5 text-sm font-medium text-white hover:bg-odoo-teal-dark">Join</button>
    </div>`;
  }
  function openJoin(activityId, title) {
    const m = UI.modal(`Join: ${title}`, `
      <form data-form class="space-y-4">
        <div>
          <label class="block text-sm text-odoo-muted">Evidence (image or PDF)</label>
          <input type="file" name="proof_file" accept="image/*,application/pdf"
            class="mt-1 block w-full text-sm text-odoo-text file:mr-3 file:rounded-lg file:border-0 file:bg-gray-100 file:px-3 file:py-2 file:text-odoo-text">
        </div>
        <div data-err class="hidden text-sm text-red-600"></div>
        <button type="submit" class="w-full rounded-lg bg-odoo-teal px-4 py-2 text-sm font-semibold text-white hover:bg-odoo-teal-dark">Submit participation</button>
      </form>`);
    const form = m.body.querySelector("[data-form]");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData();
      fd.append("activity", activityId);
      const file = form.proof_file.files[0];
      if (file) fd.append("proof_file", file);
      const res = await API.request("/social/participation/", { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (res.ok) { m.close(); Toast.success("Participation submitted for approval."); }
      else {
        const err = m.body.querySelector("[data-err]");
        err.textContent = firstErr(data) || "Submission failed.";
        err.classList.remove("hidden");
      }
    });
  }

  function participationView(mount) {
    return tableView(
      "/social/participation/",
      [
        { label: "Employee", key: "employee_name" },
        { label: "Activity", key: "activity_title" },
        { label: "Status", render: (r) => statusPill(r.status, r.status_label) },
        { label: "Evidence", render: (r) => r.proof_url
            ? `<a href="${r.proof_url}" target="_blank" class="text-odoo-teal underline">View</a>` : "—" },
      ],
      (r) => r.status === "PENDING"
        ? `<button data-act="approve" data-id="${r.id}" class="rounded bg-green-600 px-2 py-1 text-xs font-medium text-white hover:bg-green-700">Approve</button>
           <button data-act="reject" data-id="${r.id}" class="ml-1 rounded bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700">Reject</button>`
        : "—",
      {
        approve: (id) => post(`/social/participation/${id}/approve/`).then(() => Toast.success("Approved — XP awarded.")),
        reject: (id) => post(`/social/participation/${id}/reject/`).then(() => Toast.info("Participation rejected.")),
      }
    )(mount);
  }

  function acksView(mount) {
    return tableView(
      "/governance/acknowledgements/",
      [
        { label: "Policy", key: "policy_title" },
        { label: "Employee", key: "employee_name" },
        { label: "Acknowledged", render: (r) => r.is_acknowledged
            ? `<span class="text-green-600">${UI.fmtDate(r.acknowledged_at)}</span>` : "Pending" },
      ],
      (r) => r.is_acknowledged
        ? '<span class="text-xs text-green-600">✓ Acknowledged</span>'
        : `<button data-act="ack" data-id="${r.id}" class="rounded bg-odoo-purple px-2.5 py-1 text-xs font-medium text-white hover:bg-odoo-purple-dark">Acknowledge</button>`,
      { ack: (id) => post(`/governance/acknowledgements/${id}/acknowledge/`).then(() => Toast.success("Policy acknowledged.")) }
    )(mount);
  }

  function rewardsView(mount) {
    async function load() {
      mount.innerHTML = UI.spinner();
      let rewards;
      try { rewards = await listFetch("/gamification/rewards/"); }
      catch (e) { mount.innerHTML = UI.errorBox("Could not load rewards."); return; }
      if (!rewards.length) { mount.innerHTML = UI.empty("No rewards available."); return; }
      mount.innerHTML = `<div class="grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3">${rewards.map(rewardCard).join("")}</div>`;
      mount.querySelectorAll("[data-act='redeem']").forEach((b) =>
        b.addEventListener("click", async () => {
          b.disabled = true;
          try {
            const d = await post(`/gamification/rewards/${b.dataset.id}/redeem/`);
            Toast.success(d.detail || "Redeemed!");
            document.dispatchEvent(new CustomEvent("ecosphere:xp", { detail: d.xp_balance }));
            await load();
          } catch (e) { Toast.error(e.message); b.disabled = false; }
        }));
    }
    load();
  }
  function rewardCard(r) {
    const out = r.stock_count < 1;
    return `<div class="rounded-xl border border-odoo-border bg-white p-5 shadow-sm">
      <h3 class="font-semibold text-odoo-text">${UI.escapeHtml(r.name)}</h3>
      <p class="mt-1 text-sm text-odoo-muted">${UI.escapeHtml(r.description || "")}</p>
      <p class="mt-3 text-lg font-bold text-odoo-purple">${r.points_required} XP</p>
      <p class="text-xs text-odoo-muted">${r.stock_count} in stock</p>
      <button data-act="redeem" data-id="${r.id}" ${out ? "disabled" : ""}
        class="mt-3 w-full rounded-lg bg-odoo-teal px-3 py-1.5 text-sm font-medium text-white hover:bg-odoo-teal-dark disabled:opacity-50 disabled:cursor-not-allowed">
        ${out ? "Out of stock" : "Redeem"}</button>
    </div>`;
  }

  function badgesView(mount) {
    async function load() {
      mount.innerHTML = UI.spinner();
      let badges;
      try { badges = await listFetch("/gamification/badges/"); }
      catch (e) { mount.innerHTML = UI.errorBox("Could not load badges."); return; }
      if (!badges.length) { mount.innerHTML = UI.empty("No badges defined yet."); return; }
      const tierColor = { BRONZE: "text-amber-700", SILVER: "text-gray-500", GOLD: "text-amber-500" };
      mount.innerHTML = `<div class="grid gap-4 grid-cols-2 p-4 sm:grid-cols-3 lg:grid-cols-4">${badges.map((b) =>
        `<div class="rounded-xl border border-odoo-border bg-white p-5 text-center shadow-sm">
          <div class="text-3xl">${UI.escapeHtml(b.icon || "🏅")}</div>
          <p class="mt-2 font-semibold text-odoo-text">${UI.escapeHtml(b.name)}</p>
          <p class="text-xs ${tierColor[b.tier] || "text-odoo-muted"}">${UI.escapeHtml(b.tier_label)}</p>
        </div>`).join("")}</div>`;
    }
    load();
  }

  function leaderboardView(mount) {
    async function load() {
      mount.innerHTML = UI.spinner();
      let rows;
      try { rows = await listFetch("/gamification/leaderboard/"); }
      catch (e) { mount.innerHTML = UI.errorBox("Could not load leaderboard."); return; }
      if (!rows.length) { mount.innerHTML = UI.empty("No ranked employees yet."); return; }
      mount.innerHTML = UI.table([
        { label: "Rank", render: (r) => `<span class="font-bold text-odoo-purple">#${r.rank}</span>` },
        { label: "Name", key: "name" },
        { label: "Department", key: "department" },
        { label: "Total XP", render: (r) => `<span class="font-medium text-odoo-text">${UI.fmtNum(r.total_xp)}</span>` },
        { label: "Level", key: "level" },
        { label: "Badges", key: "badges" },
      ], rows);
    }
    load();
  }

  function exportView(reportType) {
    return function (mount) {
      const label = { ENVIRONMENTAL: "Environmental", SOCIAL: "Social",
        GOVERNANCE: "Governance", ESG_SUMMARY: "ESG Summary" }[reportType];
      mount.innerHTML = `<div class="px-6 py-10">
        <p class="text-sm text-odoo-muted">Download the <span class="font-semibold text-odoo-text">${label}</span> report (data is scoped to your permissions):</p>
        <div class="mt-4 flex flex-wrap gap-2">
          ${["pdf", "xlsx", "csv"].map((f) =>
            `<button data-fmt="${f}" class="rounded-lg border border-odoo-border bg-white px-4 py-2 text-sm font-medium text-odoo-text hover:bg-gray-50">⬇ ${f.toUpperCase()}</button>`).join("")}
        </div></div>`;
      mount.querySelectorAll("[data-fmt]").forEach((b) =>
        b.addEventListener("click", () => downloadReport(reportType, b.dataset.fmt)));
    };
  }

  async function downloadReport(type, fmt) {
    try {
      await UI.downloadFile(`/reports/export/?type=${type}&fmt=${fmt}`, `${type}.${fmt}`);
      Toast.success(`${fmt.toUpperCase()} report downloaded.`);
    } catch (e) { Toast.error("Export failed."); }
  }

  function placeholder(text) {
    return (mount) => { mount.innerHTML = UI.empty(text); };
  }

  // ── Registry: module -> tab -> renderer ──
  const REGISTRY = {
    environmental: {
      "emission-factors": tableView("/environmental/emission-factors/", COLS.emissionFactors),
      products: tableView("/catalog/products/", COLS.products),
      carbon: tableView("/environmental/carbon/", COLS.carbon),
      goals: tableView("/environmental/goals/", COLS.goals),
    },
    social: {
      csr: csrView,
      participation: participationView,
      diversity: placeholder("Diversity metrics dashboard — coming soon."),
    },
    governance: {
      policies: tableView("/governance/policies/", COLS.policies),
      acks: acksView,
      audits: tableView("/governance/audits/", COLS.audits),
      issues: tableView("/governance/issues/", COLS.issues),
    },
    gamification: {
      challenges: tableView("/gamification/challenges/", COLS.challenges),
      "challenge-participation": tableView("/gamification/challenge-participation/", COLS.challengeParticipation),
      badges: badgesView,
      rewards: rewardsView,
      leaderboard: leaderboardView,
    },
    reports: {
      environmental: exportView("ENVIRONMENTAL"), social: exportView("SOCIAL"),
      governance: exportView("GOVERNANCE"), esg: exportView("ESG_SUMMARY"),
      custom: exportView("ESG_SUMMARY"),
    },
    settings: {
      departments: tableView("/catalog/departments/", COLS.departments),
      categories: tableView("/catalog/categories/", COLS.categories),
      esg: placeholder("ESG configuration is managed in Django admin for now."),
      notifications: placeholder("Notification settings — coming soon."),
    },
  };

  // ── Orchestrator ──
  document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("module-data-root");
    const mount = document.getElementById("module-data");
    if (!root || !mount) return;
    const module = root.dataset.module;
    const tabs = REGISTRY[module] || {};
    const params = new URLSearchParams(window.location.search);
    const firstLink = document.querySelector("[data-tab]");
    const tab = params.get("tab") || (firstLink ? firstLink.dataset.tab : null);

    const render = tabs[tab];
    if (render) render(mount);
    else mount.innerHTML = UI.empty("This section is not available yet.");

    // Wire the top toolbar Export button to this module's report.
    const exportBtn = document.getElementById("export-btn");
    if (exportBtn) exportBtn.addEventListener("click", () =>
      downloadReport(MODULE_REPORT[module] || "ESG_SUMMARY", "pdf"));

    const newBtn = document.getElementById("new-btn");
    if (newBtn) newBtn.addEventListener("click", () =>
      Toast.info("Create forms are available in Django admin; inline forms coming soon."));
  });
})();
