/** Login page: submit credentials over AJAX, store JWTs, redirect. */
document.addEventListener("DOMContentLoaded", () => {
  // Already signed in? Skip the form.
  if (window.API.isAuthenticated()) {
    window.location.replace("/dashboard/");
    return;
  }

  const form = document.getElementById("login-form");
  const errorBox = document.getElementById("login-error");
  const submit = document.getElementById("login-submit");
  const spinner = document.getElementById("login-spinner");
  const label = document.getElementById("login-label");
  const password = document.getElementById("password");
  const toggle = document.getElementById("toggle-password");

  toggle.addEventListener("click", () => {
    password.type = password.type === "password" ? "text" : "password";
  });

  function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
  }

  function setLoading(loading) {
    submit.disabled = loading;
    spinner.classList.toggle("hidden", !loading);
    label.textContent = loading ? "Signing in…" : "Sign in";
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.classList.add("hidden");
    setLoading(true);

    try {
      await window.API.login(form.username.value.trim(), form.password.value);
      window.location.replace("/dashboard/");
    } catch (err) {
      showError(err.message);
      setLoading(false);
    }
  });
});
