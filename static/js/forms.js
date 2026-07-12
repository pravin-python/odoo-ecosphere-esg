/** Schema-driven create forms with client + server validation. window.Forms. */
(function (global) {
  "use strict";
  const API = global.API, UI = global.UI, Toast = global.Toast;

  // ── Static enum choices [value, label] ──
  const E = {
    source: [["DIESEL", "Diesel"], ["PETROL", "Petrol"], ["CNG", "CNG"], ["NATURAL_GAS", "Natural Gas"],
      ["ELECTRICITY", "Electricity"], ["WATER", "Water"], ["WASTE", "Waste"], ["RAW_MATERIAL", "Raw Material"]],
    unit: [["LITER", "Liter"], ["KWH", "kWh"], ["KG", "Kilogram"], ["CUBIC_METER", "Cubic Meter"], ["UNIT", "Unit"]],
    csr: [["ENVIRONMENT", "Environment"], ["COMMUNITY", "Community"], ["EDUCATION", "Education"], ["HEALTH", "Health"]],
    pillar: [["E", "Environmental"], ["S", "Social"], ["G", "Governance"]],
    metric: [["CARBON_REDUCTION", "Carbon Reduction (%)"], ["ENERGY_REDUCTION", "Energy Reduction (%)"], ["WASTE_REDUCTION", "Waste Reduction (%)"]],
    auditType: [["INTERNAL", "Internal"], ["EXTERNAL", "External"]],
    severity: [["LOW", "Low"], ["MEDIUM", "Medium"], ["HIGH", "High"], ["CRITICAL", "Critical"]],
    difficulty: [["EASY", "Easy"], ["MEDIUM", "Medium"], ["HARD", "Hard"]],
    tier: [["BRONZE", "Bronze"], ["SILVER", "Silver"], ["GOLD", "Gold"]],
    catType: [["CSR_ACTIVITY", "CSR Activity"], ["CHALLENGE", "Challenge"]],
  };

  const dateOrder = (v) =>
    (v.start_date && v.end_date && v.end_date < v.start_date)
      ? { end_date: "End date must be on or after the start date." } : {};

  // ── Create-form registry: module -> tab -> config ──
  const FORMS = {
    environmental: {
      "emission-factors": {
        title: "New Emission Factor", endpoint: "/environmental/emission-factors/",
        fields: [
          { name: "name", label: "Name", type: "text", required: true },
          { name: "source_type", label: "Source", type: "select", required: true, options: E.source },
          { name: "unit", label: "Unit", type: "select", required: true, options: E.unit },
          { name: "factor_value", label: "Factor (kg CO₂e / unit)", type: "number", required: true, min: 0, step: "0.0001" },
          { name: "effective_from", label: "Effective from", type: "date", required: true },
          { name: "is_active", label: "Active", type: "checkbox", default: true },
        ],
      },
      products: {
        title: "New Product ESG Profile", endpoint: "/catalog/products/",
        fields: [
          { name: "name", label: "Name", type: "text", required: true },
          { name: "sku", label: "SKU", type: "text", required: true },
          { name: "carbon_footprint_kg", label: "Carbon footprint (kg)", type: "number", required: true, min: 0, step: "0.001" },
          { name: "ethical_sourcing_score", label: "Ethics score (0–100)", type: "number", required: true, min: 0, step: "1" },
          { name: "recyclable", label: "Recyclable", type: "checkbox", default: false },
        ],
      },
      goals: {
        title: "New Environmental Goal", endpoint: "/environmental/goals/",
        fields: [
          { name: "title", label: "Title", type: "text", required: true },
          { name: "department", label: "Department", type: "select", required: true, optionsUrl: "/catalog/departments/", optionValue: "id", optionLabel: "name" },
          { name: "metric", label: "Metric", type: "select", required: true, options: E.metric },
          { name: "baseline_value", label: "Baseline value", type: "number", required: true, step: "0.01" },
          { name: "target_value", label: "Target value", type: "number", required: true, step: "0.01" },
          { name: "target_date", label: "Target date", type: "date", required: true },
        ],
      },
    },
    social: {
      csr: {
        title: "New CSR Activity", endpoint: "/social/activities/", validate: dateOrder,
        fields: [
          { name: "title", label: "Title", type: "text", required: true },
          { name: "description", label: "Description", type: "textarea" },
          { name: "category", label: "Category", type: "select", required: true, options: E.csr },
          { name: "xp_reward", label: "XP reward", type: "number", required: true, min: 0, step: "1" },
          { name: "start_date", label: "Start date", type: "date", required: true },
          { name: "end_date", label: "End date", type: "date", required: true },
        ],
      },
    },
    governance: {
      policies: {
        title: "New ESG Policy", endpoint: "/governance/policies/",
        fields: [
          { name: "title", label: "Title", type: "text", required: true },
          { name: "pillar", label: "Pillar", type: "select", required: true, options: E.pillar },
          { name: "version", label: "Version", type: "text", default: "1.0" },
          { name: "effective_date", label: "Effective date", type: "date", required: true },
        ],
      },
      audits: {
        title: "New Audit", endpoint: "/governance/audits/",
        fields: [
          { name: "title", label: "Title", type: "text", required: true },
          { name: "audit_type", label: "Type", type: "select", required: true, options: E.auditType },
          { name: "department", label: "Department", type: "select", required: true, optionsUrl: "/catalog/departments/", optionValue: "id", optionLabel: "name" },
          { name: "scheduled_date", label: "Scheduled date", type: "date", required: true },
        ],
      },
      issues: {
        title: "New Compliance Issue", endpoint: "/governance/issues/",
        fields: [
          { name: "title", label: "Title", type: "text", required: true },
          { name: "description", label: "Description", type: "textarea" },
          { name: "audit", label: "Audit", type: "select", required: true, optionsUrl: "/governance/audits/", optionValue: "id", optionLabel: "title" },
          { name: "owner", label: "Owner", type: "select", required: true, optionsUrl: "/catalog/users/", optionValue: "id", optionLabel: "name" },
          { name: "severity", label: "Severity", type: "select", required: true, options: E.severity },
          { name: "due_date", label: "Due date", type: "date", required: true },
        ],
      },
    },
    gamification: {
      challenges: {
        title: "New Challenge", endpoint: "/gamification/challenges/", validate: dateOrder,
        fields: [
          { name: "title", label: "Title", type: "text", required: true },
          { name: "description", label: "Description", type: "textarea" },
          { name: "difficulty", label: "Difficulty", type: "select", required: true, options: E.difficulty },
          { name: "xp_reward", label: "XP reward", type: "number", required: true, min: 0, step: "1" },
          { name: "start_date", label: "Start date", type: "date", required: true },
          { name: "end_date", label: "End date", type: "date", required: true },
          { name: "deadline", label: "Deadline (optional)", type: "date" },
        ],
      },
      badges: {
        title: "New Badge", endpoint: "/gamification/badges/",
        fields: [
          { name: "name", label: "Name", type: "text", required: true },
          { name: "description", label: "Description", type: "text" },
          { name: "tier", label: "Tier", type: "select", required: true, options: E.tier },
          { name: "icon", label: "Icon (emoji)", type: "text" },
        ],
      },
      rewards: {
        title: "New Reward", endpoint: "/gamification/rewards/",
        fields: [
          { name: "name", label: "Name", type: "text", required: true },
          { name: "description", label: "Description", type: "text" },
          { name: "points_required", label: "Points required", type: "number", required: true, min: 1, step: "1" },
          { name: "stock_count", label: "Stock count", type: "number", required: true, min: 0, step: "1" },
        ],
      },
    },
    settings: {
      departments: {
        title: "New Department", endpoint: "/catalog/departments/",
        fields: [
          { name: "name", label: "Name", type: "text", required: true },
          { name: "code", label: "Code", type: "text", required: true },
        ],
      },
      categories: {
        title: "New Category", endpoint: "/catalog/categories/",
        fields: [
          { name: "name", label: "Name", type: "text", required: true },
          { name: "type", label: "Type", type: "select", required: true, options: E.catType },
          { name: "description", label: "Description", type: "text" },
        ],
      },
    },
  };

  const INPUT = "mt-1 block w-full rounded-lg border border-odoo-border px-3 py-2 text-sm text-odoo-text focus:border-odoo-teal focus:outline-none focus:ring-2 focus:ring-odoo-teal/30";

  function fieldHtml(f) {
    const req = f.required ? '<span class="text-red-600">*</span>' : "";
    let control;
    if (f.type === "textarea") {
      control = `<textarea name="${f.name}" rows="3" class="${INPUT}"></textarea>`;
    } else if (f.type === "checkbox") {
      control = `<label class="mt-1 inline-flex items-center gap-2 text-sm text-odoo-text">
        <input type="checkbox" name="${f.name}" ${f.default ? "checked" : ""} class="rounded border-odoo-border text-odoo-teal focus:ring-odoo-teal"> Yes</label>`;
    } else if (f.type === "select") {
      const opts = (f.options || []).map(([v, l]) => `<option value="${v}">${UI.escapeHtml(l)}</option>`).join("");
      control = `<select name="${f.name}" class="${INPUT}"><option value="">— select —</option>${opts}</select>`;
    } else {
      const a = [`type="${f.type}"`, `name="${f.name}"`];
      if (f.type === "number") { if (f.min != null) a.push(`min="${f.min}"`); if (f.step) a.push(`step="${f.step}"`); }
      if (f.default != null) a.push(`value="${f.default}"`);
      control = `<input ${a.join(" ")} class="${INPUT}">`;
    }
    return `<div>
      <label class="block text-sm font-medium text-odoo-text">${UI.escapeHtml(f.label)} ${req}</label>
      ${control}
      <p data-err="${f.name}" class="mt-1 hidden text-xs text-red-600"></p>
    </div>`;
  }

  function collect(fields, form) {
    const v = {};
    fields.forEach((f) => {
      const el = form.querySelector(`[name="${f.name}"]`);
      if (!el) return;
      if (f.type === "checkbox") { v[f.name] = el.checked; return; }
      const raw = el.value.trim();
      if (raw === "") { if (f.required) v[f.name] = ""; return; }
      v[f.name] = f.type === "number" ? Number(raw) : raw;
    });
    return v;
  }

  function clientValidate(cfg, values) {
    const errs = {};
    cfg.fields.forEach((f) => {
      if (f.type === "checkbox") return;
      const val = values[f.name];
      if (f.required && (val === undefined || val === "")) errs[f.name] = "This field is required.";
      else if (f.type === "number" && typeof val === "number" && f.min != null && val < f.min)
        errs[f.name] = `Must be at least ${f.min}.`;
    });
    if (cfg.validate) Object.assign(errs, cfg.validate(values) || {});
    return errs;
  }

  function clearErrors(form) {
    form.querySelectorAll("[data-err]").forEach((e) => { e.textContent = ""; e.classList.add("hidden"); });
    const fe = form.querySelector("[data-form-error]");
    fe.textContent = ""; fe.classList.add("hidden");
  }
  function showErrors(form, errs) {
    Object.entries(errs).forEach(([k, msg]) => {
      const e = form.querySelector(`[data-err="${k}"]`);
      if (e) { e.textContent = msg; e.classList.remove("hidden"); }
      else formError(form, `${k}: ${msg}`);
    });
  }
  function formError(form, msg) {
    const fe = form.querySelector("[data-form-error]");
    fe.textContent = msg; fe.classList.remove("hidden");
  }

  async function open(module, tab, onSuccess) {
    const cfg = (FORMS[module] || {})[tab];
    if (!cfg) { Toast.info("Nothing to create on this tab."); return; }

    const body = `<form data-form class="space-y-3">
      ${cfg.fields.map(fieldHtml).join("")}
      <div data-form-error class="hidden rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"></div>
      <button type="submit" class="w-full rounded-lg bg-odoo-teal px-4 py-2 text-sm font-semibold text-white hover:bg-odoo-teal-dark disabled:opacity-60">Save</button>
    </form>`;
    const m = UI.modal(cfg.title, body);
    const form = m.body.querySelector("[data-form]");

    // Populate FK dropdowns from their endpoints.
    for (const f of cfg.fields) {
      if (f.type === "select" && f.optionsUrl) {
        try {
          const r = await API.request(f.optionsUrl);
          const data = await r.json();
          const rows = Array.isArray(data) ? data : (data.results || []);
          const sel = form.querySelector(`[name="${f.name}"]`);
          rows.forEach((row) => {
            const o = document.createElement("option");
            o.value = row[f.optionValue || "id"];
            o.textContent = row[f.optionLabel || "name"];
            sel.appendChild(o);
          });
        } catch (e) { /* leave empty */ }
      }
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearErrors(form);
      const values = collect(cfg.fields, form);
      const errs = clientValidate(cfg, values);
      if (Object.keys(errs).length) { showErrors(form, errs); return; }

      const btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      try {
        const res = await API.request(cfg.endpoint, { method: "POST", body: JSON.stringify(values) });
        if (res.ok) { m.close(); Toast.success("Created successfully."); onSuccess && onSuccess(); return; }
        const data = await res.json().catch(() => ({}));
        if (res.status === 403) formError(form, "You don't have permission to create this.");
        else if (res.status === 400) showErrors(form, serverErrors(data));
        else formError(form, (data && data.detail) || "Could not save.");
      } catch (e2) {
        formError(form, "Network error — please try again.");
      }
      btn.disabled = false;
    });
  }

  function serverErrors(data) {
    const errs = {};
    if (data && typeof data === "object") {
      Object.entries(data).forEach(([k, v]) => { errs[k] = Array.isArray(v) ? v[0] : String(v); });
    }
    return Object.keys(errs).length ? errs : { non_field_errors: "Could not save." };
  }

  global.Forms = { open };
})(window);
