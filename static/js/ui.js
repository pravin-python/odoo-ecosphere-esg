/** Shared UI helpers: tables, cards, badges, modal, blob download. window.UI. */
(function (global) {
  "use strict";

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  function spinner() {
    return `<div class="flex justify-center py-16">
      <svg class="h-7 w-7 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg></div>`;
  }

  function empty(text) {
    return `<div class="px-6 py-16 text-center text-sm text-slate-500">${escapeHtml(text)}</div>`;
  }

  function errorBox(text) {
    return `<div class="px-6 py-16 text-center text-sm text-red-400">${escapeHtml(text)}</div>`;
  }

  function fmtDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleDateString();
  }

  function fmtNum(n) {
    if (n == null || n === "") return "—";
    return Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 });
  }

  function boolPill(v) {
    return v
      ? '<span class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-400">Yes</span>'
      : '<span class="rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-400">No</span>';
  }

  /** columns: [{label, key, render?(row)}]. actions?: (row)=>html string. */
  function table(columns, rows, actions) {
    const head = columns.map((c) => `<th class="px-4 py-3 text-left font-medium">${escapeHtml(c.label)}</th>`).join("");
    const actionHead = actions ? '<th class="px-4 py-3 text-right font-medium">Actions</th>' : "";
    const body = rows.map((row) => {
      const cells = columns.map((c) => {
        const val = c.render ? c.render(row) : escapeHtml(row[c.key]);
        return `<td class="px-4 py-3 text-slate-300">${val == null ? "—" : val}</td>`;
      }).join("");
      const act = actions ? `<td class="px-4 py-3 text-right">${actions(row)}</td>` : "";
      return `<tr class="border-t border-slate-800 hover:bg-slate-800/40">${cells}${act}</tr>`;
    }).join("");
    return `<div class="overflow-x-auto"><table class="min-w-full text-sm">
      <thead class="bg-slate-800/60 text-slate-400"><tr>${head}${actionHead}</tr></thead>
      <tbody>${body}</tbody></table></div>`;
  }

  /** Simple centered modal. Returns { root, close }. */
  function modal(title, contentHtml) {
    const root = document.createElement("div");
    root.className = "fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4";
    root.innerHTML = `
      <div class="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-base font-semibold text-white">${escapeHtml(title)}</h3>
          <button data-close class="rounded-lg p-1 text-slate-400 hover:bg-slate-800">✕</button>
        </div>
        <div data-body>${contentHtml}</div>
      </div>`;
    function close() { root.remove(); }
    root.addEventListener("click", (e) => { if (e.target === root) close(); });
    root.querySelector("[data-close]").addEventListener("click", close);
    document.body.appendChild(root);
    return { root, close, body: root.querySelector("[data-body]") };
  }

  /** Download an authenticated file (JWT header) as an attachment. */
  async function downloadFile(path, fallbackName) {
    const res = await global.API.request(path);
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const disp = res.headers.get("Content-Disposition") || "";
    const match = disp.match(/filename="?([^"]+)"?/);
    const name = match ? match[1] : fallbackName;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  global.UI = { escapeHtml, spinner, empty, errorBox, fmtDate, fmtNum, boolPill, table, modal, downloadFile };
})(window);
