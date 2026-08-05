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
    } else if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
      console.error("Request timed out — search job taking longer than 60 seconds.");
    } else if (error.request) {
      console.error("Network error — unable to reach backend at " + API_BASE_URL);
    }

    return Promise.reject(error);
  }
);

export default api;
