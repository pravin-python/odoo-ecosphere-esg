/** Dashboard: guard the route, load the profile over AJAX, wire sign-out. */
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

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  try {
    const me = await API.me();
    const displayName = me.first_name || me.username;
    const roleLabel = roleLabels[me.role] || me.role;

    setText("greeting-name", displayName);
    setText("profile-username", me.username);
    setText("profile-email", me.email || "—");
    setText("profile-role", roleLabel);
    setText("profile-department", me.department ? `Department #${me.department}` : "Unassigned");
    setText("nav-user-name", displayName);
    setText("nav-user-role", roleLabel);

    const content = document.getElementById("dashboard-content");
    const loader = document.getElementById("dashboard-loader");
    if (loader) loader.classList.add("hidden");
    if (content) content.classList.remove("hidden");
  } catch (err) {
    API.clear();
    window.location.replace("/login/");
    return;
  }

  const logout = document.getElementById("logout-btn");
  if (logout) {
    logout.addEventListener("click", async () => {
      await API.logout();
      window.location.replace("/login/");
    });
  }
});
