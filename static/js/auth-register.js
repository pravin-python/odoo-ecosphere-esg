/** Register page: create an account over AJAX, then auto-login and redirect. */
document.addEventListener("DOMContentLoaded", () => {
  const API = window.API;

  if (API.isAuthenticated()) {
    window.location.replace("/dashboard/");
    return;
  }

  const form = document.getElementById("register-form");
  const errorBox = document.getElementById("register-error");
  const submit = document.getElementById("register-submit");
  const spinner = document.getElementById("register-spinner");
  const label = document.getElementById("register-label");

  function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
  }

  function setLoading(loading) {
    submit.disabled = loading;
    spinner.classList.toggle("hidden", !loading);
    label.textContent = loading ? "Creating account…" : "Create account";
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.classList.add("hidden");

    const payload = {
      username: form.username.value.trim(),
      email: form.email.value.trim(),
      first_name: form.first_name.value.trim(),
      last_name: form.last_name.value.trim(),
      password: form.password.value,
      password_confirm: form.password_confirm.value,
    };

    if (payload.password !== payload.password_confirm) {
      showError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await API.register(payload);
      // Seamless: log the new user straight in.
      await API.login(payload.username, payload.password);
      window.location.replace("/dashboard/");
    } catch (err) {
      showError(err.message);
      setLoading(false);
    }
  });
});
