/** Dashboard: fetch the summary and render tiles, charts, and activity. */
document.addEventListener("DOMContentLoaded", async () => {
  const API = window.API;
  if (!API.isAuthenticated()) return; // app-shell.js handles the redirect

  function set(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  const gridColor = "rgba(148,163,184,0.12)";
  const tickColor = "#94a3b8";

  let data;
  try {
    const res = await API.request("/dashboard/summary/");
    if (!res.ok) throw new Error("summary failed");
    data = await res.json();
  } catch (err) {
    document.getElementById("recent-activity").innerHTML =
      '<li class="text-red-400">Could not load dashboard data.</li>';
    return;
  }

  // Scores
  set("score-environmental", Math.round(data.scores.environmental));
  set("score-social", Math.round(data.scores.social));
  set("score-governance", Math.round(data.scores.governance));
  set("score-overall", Math.round(data.scores.overall));

  // Counts
  const c = data.counts;
  set("stat-carbon", fmt(c.carbon_30d_kg));
  set("stat-compliance", c.open_compliance);
  set("stat-csr", c.csr_pending);
  set("stat-xp", c.my_xp);

  // Emissions trend (line)
  new Chart(document.getElementById("chart-emissions"), {
    type: "line",
    data: {
      labels: data.emissions_trend.map((p) => p.label),
      datasets: [{
        data: data.emissions_trend.map((p) => p.value),
        borderColor: "#10b981",
        backgroundColor: "rgba(16,185,129,0.15)",
        fill: true,
        tension: 0.35,
        pointRadius: 2,
      }],
    },
    options: baseOptions(gridColor, tickColor),
  });

  // Department ranking (bar)
  const ranking = data.department_ranking;
  new Chart(document.getElementById("chart-ranking"), {
    type: "bar",
    data: {
      labels: ranking.map((d) => d.name),
      datasets: [{
        data: ranking.map((d) => d.co2e),
        backgroundColor: "#0ea5e9",
        borderRadius: 6,
      }],
    },
    options: baseOptions(gridColor, tickColor),
  });

  // Recent activity
  const list = document.getElementById("recent-activity");
  if (!data.recent_activity.length) {
    list.innerHTML = '<li class="text-slate-500">No recent activity yet.</li>';
  } else {
    list.innerHTML = data.recent_activity
      .map((a) => `<li class="flex items-start gap-2 border-b border-slate-800 pb-2 last:border-0">
          <span class="mt-0.5">${badge(a.category)}</span>
          <span>${escapeHtml(a.title)}</span>
        </li>`)
      .join("");
  }

  function baseOptions(grid, tick) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: grid }, ticks: { color: tick } },
        y: { grid: { color: grid }, ticks: { color: tick }, beginAtZero: true },
      },
    };
  }
});

function fmt(n) {
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
}
function badge(category) {
  return { COMPLIANCE: "⚠️", CSR: "🤝", GAMIFICATION: "🏆", SYSTEM: "🔔" }[category] || "•";
}
function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
