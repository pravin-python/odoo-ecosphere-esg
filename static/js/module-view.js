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
  const TAB_REPORT = {
    environmental: "ENVIRONMENTAL", social: "SOCIAL",
    governance: "GOVERNANCE", esg: "ESG_SUMMARY", custom: "ESG_SUMMARY",
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
    return `<span class="rounded-full px-2 py-0.5 text-xs ${cls}">${UI.escapeHtml(text)}</span>`;
  }
  function statusPill(status, label) {
    const map = {
      APPROVED: "bg-emerald-500/15 text-emerald-400", ACHIEVED: "bg-emerald-500/15 text-emerald-400",
      RESOLVED: "bg-emerald-500/15 text-emerald-400", ACTIVE: "bg-sky-500/15 text-sky-400",
      PENDING: "bg-amber-500/15 text-amber-400", OPEN: "bg-amber-500/15 text-amber-400",
      IN_PROGRESS: "bg-sky-500/15 text-sky-400", REJECTED: "bg-red-500/15 text-red-400",
      MISSED: "bg-red-500/15 text-red-400",
    };
    return pill(label || status, map[status] || "bg-slate-700 text-slate-300");
  }
  function severityPill(sev, label) {
    const map = { LOW: "bg-slate-700 text-slate-300", MEDIUM: "bg-sky-500/15 text-sky-400",
      HIGH: "bg-amber-500/15 text-amber-400", CRITICAL: "bg-red-500/15 text-red-400" };
    return pill(label || sev, map[sev] || "bg-slate-700 text-slate-300");
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
      { label: "CO₂e (kg)", render: (r) => `<span class="font-medium text-emerald-400">${UI.fmtNum(r.co2e_kg)}</span>` },
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
          ? pill("OVERDUE", "bg-red-500/20 text-red-400 font-semibold")
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
      mount.innerHTML = `<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">${acts.map(csrCard).join("")}</div>`;
      mount.querySelectorAll("[data-join]").forEach((b) =>
        b.addEventListener("click", () => openJoin(b.dataset.join, b.dataset.title)));
    }
    load();
  }
  function csrCard(a) {
    return `<div class="rounded-2xl border border-sky-500/40 bg-slate-900 p-5">
      <h3 class="font-semibold text-white">${UI.escapeHtml(a.title)}</h3>
      <p class="mt-1 text-xs text-sky-400">${UI.escapeHtml(a.category_label)} · ${a.xp_reward} XP</p>
      <p class="mt-2 text-sm text-slate-400">${a.participant_count} joined · Evidence required</p>
      <button data-join="${a.id}" data-title="${UI.escapeHtml(a.title)}"
        class="mt-4 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700">Join</button>
    </div>`;
  }
  function openJoin(activityId, title) {
    const m = UI.modal(`Join: ${title}`, `
      <form data-form class="space-y-4">
        <div>
          <label class="block text-sm text-slate-300">Evidence (image or PDF)</label>
          <input type="file" name="proof_file" accept="image/*,application/pdf"
            class="mt-1 block w-full text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-200">
        </div>
        <div data-err class="hidden text-sm text-red-400"></div>
        <button type="submit" class="w-full rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700">Submit participation</button>
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
            ? `<a href="${r.proof_url}" target="_blank" class="text-sky-400 underline">View</a>` : "—" },
      ],
      (r) => r.status === "PENDING"
        ? `<button data-act="approve" data-id="${r.id}" class="rounded bg-emerald-600/80 px-2 py-1 text-xs font-medium text-white hover:bg-emerald-600">Approve</button>
           <button data-act="reject" data-id="${r.id}" class="ml-1 rounded bg-red-600/80 px-2 py-1 text-xs font-medium text-white hover:bg-red-600">Reject</button>`
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
            ? `<span class="text-emerald-400">${UI.fmtDate(r.acknowledged_at)}</span>` : "Pending" },
      ],
      (r) => r.is_acknowledged
        ? '<span class="text-xs text-emerald-400">✓ Acknowledged</span>'
        : `<button data-act="ack" data-id="${r.id}" class="rounded bg-violet-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-violet-700">Acknowledge</button>`,
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
      mount.innerHTML = `<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">${rewards.map(rewardCard).join("")}</div>`;
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
    return `<div class="rounded-2xl border border-amber-500/40 bg-slate-900 p-5">
      <h3 class="font-semibold text-white">${UI.escapeHtml(r.name)}</h3>
      <p class="mt-1 text-sm text-slate-400">${UI.escapeHtml(r.description || "")}</p>
      <p class="mt-3 text-lg font-bold text-amber-400">${r.points_required} XP</p>
      <p class="text-xs text-slate-500">${r.stock_count} in stock</p>
      <button data-act="redeem" data-id="${r.id}" ${out ? "disabled" : ""}
        class="mt-3 w-full rounded-lg bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed">
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
      const tierColor = { BRONZE: "text-amber-600", SILVER: "text-slate-300", GOLD: "text-amber-400" };
      mount.innerHTML = `<div class="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">${badges.map((b) =>
        `<div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 text-center">
          <div class="text-3xl">${UI.escapeHtml(b.icon || "🏅")}</div>
          <p class="mt-2 font-semibold text-white">${UI.escapeHtml(b.name)}</p>
          <p class="text-xs ${tierColor[b.tier] || "text-slate-400"}">${UI.escapeHtml(b.tier_label)}</p>
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
        { label: "Rank", render: (r) => `<span class="font-bold text-amber-400">#${r.rank}</span>` },
        { label: "Name", key: "name" },
        { label: "Department", key: "department" },
        { label: "Total XP", render: (r) => `<span class="font-medium text-white">${UI.fmtNum(r.total_xp)}</span>` },
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
        <p class="text-sm text-slate-300">Download the <span class="font-semibold text-white">${label}</span> report (data is scoped to your permissions):</p>
        <div class="mt-4 flex flex-wrap gap-2">
          ${["pdf", "xlsx", "csv"].map((f) =>
            `<button data-fmt="${f}" class="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700">⬇ ${f.toUpperCase()}</button>`).join("")}
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
