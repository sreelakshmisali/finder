/**
 * API Client
 *
 * A pre-configured Axios instance that all API calls go through.
 */

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,

  (error) => {
    if (error.response) {
      const status = error.response.status;

      if (status === 401) {
        console.warn("Unauthorized — clearing token & redirecting to login");
        localStorage.removeItem("finder_token");
        delete api.defaults.headers.common["Authorization"];
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }

      if (status >= 500) {
        console.error("Server error:", error.response.data);
      }
    } else if (error.request) {
      console.error("Network error — is the backend running?");
    }

    return Promise.reject(error);
  }
);

export default api;
