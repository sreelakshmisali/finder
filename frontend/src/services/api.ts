/**
 * API Client
 *
 * A pre-configured Axios instance that all API calls go through.
 *
 * Why a centralized client?
 * - Base URL is set once, not repeated in every call
 * - Auth token injection happens automatically (Step 10)
 * - Error handling is consistent across the app
 * - Easy to add request/response interceptors later
 */

import axios from "axios";

/**
 * The base URL for all API requests.
 *
 * In development: Vite's proxy forwards /api → FastAPI at localhost:8000
 * In production: This would be the actual API domain
 *
 * We use import.meta.env (Vite's way to access env vars)
 * and fall back to "/api/v1" which works with the Vite proxy.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

/**
 * Pre-configured Axios instance.
 *
 * Every API function in the services/ folder uses this
 * instead of raw `axios.get(...)` calls.
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  /* 15 second timeout — if the server doesn't respond, fail fast */
  timeout: 15000,
});

/**
 * Response interceptor — handles errors globally.
 *
 * Instead of writing try/catch in every component,
 * we catch common errors here (401, 500, network) and
 * handle them in one place.
 */
api.interceptors.response.use(
  /* Success — pass the response through unchanged */
  (response) => response,

  /* Error — handle common cases */
  (error) => {
    if (error.response) {
      const status = error.response.status;

      if (status === 401) {
        /*
         * 401 = Unauthorized (token expired or missing)
         * In Step 10, this will redirect to the login page.
         * For now, just log it.
         */
        console.warn("Unauthorized — authentication required");
      }

      if (status >= 500) {
        console.error("Server error:", error.response.data);
      }
    } else if (error.request) {
      /* Network error — the server didn't respond at all */
      console.error("Network error — is the backend running?");
    }

    /* Re-throw so React Query can handle it in the UI */
    return Promise.reject(error);
  }
);

export default api;
