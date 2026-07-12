/** Minimal toast notifications (Tailwind classes only). window.Toast. */
(function (global) {
  "use strict";

  const STYLES = {
    success: "border-green-200 bg-green-50 text-green-800",
    error: "border-red-200 bg-red-50 text-red-800",
    info: "border-odoo-border bg-white text-odoo-text",
  };

  function container() {
    let el = document.getElementById("toast-container");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast-container";
      el.className = "fixed bottom-6 right-6 z-50 flex flex-col gap-2";
      document.body.appendChild(el);
    }
    return el;
  }

  const Toast = {
    show(message, type = "success") {
      const el = document.createElement("div");
      el.className =
        `pointer-events-auto rounded-lg border px-4 py-3 text-sm shadow-lg transition ` +
        `duration-300 opacity-0 translate-y-2 ${STYLES[type] || STYLES.info}`;
      el.textContent = message;
      container().appendChild(el);
      requestAnimationFrame(() => el.classList.remove("opacity-0", "translate-y-2"));
      setTimeout(() => {
        el.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => el.remove(), 300);
      }, 3500);
    },
    success(m) { this.show(m, "success"); },
    error(m) { this.show(m, "error"); },
    info(m) { this.show(m, "info"); },
  };

  global.Toast = Toast;
})(window);
