/**
 * EcoSphere API client — JWT token storage + fetch wrapper with auto-refresh.
 * Exposed globally as `window.API`.
 */
(function (global) {
  "use strict";

  const ACCESS_KEY = "ecosphere.access";
  const REFRESH_KEY = "ecosphere.refresh";

  const API = {
    base: "/api/v1",

    get access() {
      return localStorage.getItem(ACCESS_KEY);
    },
    get refresh() {
      return localStorage.getItem(REFRESH_KEY);
    },
    setTokens(access, refresh) {
      if (access) localStorage.setItem(ACCESS_KEY, access);
      if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    },
    clear() {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    },
    isAuthenticated() {
      return Boolean(this.access);
    },

    /** Exchange credentials for tokens. Throws Error(message) on failure. */
    async login(username, password) {
      const res = await fetch(`${this.base}/auth/login/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Invalid username or password.");
      }
      this.setTokens(data.access, data.refresh);
      return data;
    },

    /** Register a new account. Throws Error(message) with the first field error. */
    async register(payload) {
      const res = await fetch(`${this.base}/auth/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(firstError(data));
      }
      return data;
    },

    /** Try to refresh the access token. Returns true on success. */
    async _refreshTokens() {
      if (!this.refresh) return false;
      const res = await fetch(`${this.base}/auth/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: this.refresh }),
      });
      if (!res.ok) {
        this.clear();
        return false;
      }
      const data = await res.json();
      this.setTokens(data.access, data.refresh);
      return true;
    },

    /** Authenticated fetch. Retries once after a 401 by refreshing the token. */
    async request(path, options = {}, retry = true) {
      const headers = Object.assign(
        { "Content-Type": "application/json" },
        options.headers || {}
      );
      if (this.access) headers["Authorization"] = `Bearer ${this.access}`;

      const res = await fetch(`${this.base}${path}`, { ...options, headers });
      if (res.status === 401 && retry && (await this._refreshTokens())) {
        return this.request(path, options, false);
      }
      return res;
    },

    /** Current user profile (/me/). Throws if not authenticated. */
    async me() {
      const res = await this.request("/me/");
      if (!res.ok) throw new Error("Not authenticated");
      return res.json();
    },

    /** Blacklist the refresh token server-side and clear local tokens. */
    async logout() {
      if (this.refresh) {
        await this.request("/auth/logout/", {
          method: "POST",
          body: JSON.stringify({ refresh: this.refresh }),
        }).catch(() => {});
      }
      this.clear();
    },
  };

  function firstError(data) {
    if (!data || typeof data !== "object") return "Registration failed.";
    if (data.detail) return data.detail;
    const firstKey = Object.keys(data)[0];
    if (!firstKey) return "Registration failed.";
    const val = data[firstKey];
    const msg = Array.isArray(val) ? val[0] : val;
    return firstKey === "non_field_errors" ? msg : `${firstKey}: ${msg}`;
  }

  global.API = API;
})(window);
