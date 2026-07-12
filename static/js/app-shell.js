/** App shell: auth guard, load user into the top bar, sidebar toggle, logout. */
document.addEventListener("DOMContentLoaded", async () => {
  const API = window.API;

  if (!API.isAuthenticated()) {
    window.location.replace("/login/");
    return;
  }

  const roleLabels = {
    ADMIN: "Administrator",
    MANAGER: "Manager",
    GOVERNANCE_OFFICER: "Governance Officer",
    EMPLOYEE: "Employee",
  };

  // Populate the top-bar identity (also validates the session).
  try {
    const me = await API.me();
    const name = me.first_name || me.username;
    const nameEl = document.getElementById("nav-user-name");
    const roleEl = document.getElementById("nav-user-role");
    if (nameEl) nameEl.textContent = name;
    if (roleEl) roleEl.textContent = roleLabels[me.role] || me.role;
    window.CURRENT_USER = me;
    document.dispatchEvent(new CustomEvent("ecosphere:user", { detail: me }));
  } catch (err) {
    API.clear();
    window.location.replace("/login/");
    return;
  }

  // Sidebar toggle (mobile).
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const toggle = document.getElementById("sidebar-toggle");
  function openSidebar() {
    sidebar.classList.remove("-translate-x-full");
    backdrop.classList.remove("hidden");
  }
  function closeSidebar() {
    sidebar.classList.add("-translate-x-full");
    backdrop.classList.add("hidden");
  }
  if (toggle) toggle.addEventListener("click", openSidebar);
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  // Logout.
  const logout = document.getElementById("logout-btn");
  if (logout) {
    logout.addEventListener("click", async () => {
      await API.logout();
      window.location.replace("/login/");
    });
  }
});
