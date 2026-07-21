/**
 * Vite Configuration for Finder
 *
 * Vite is the build tool that bundles our React app.
 * We add two plugins:
 *   1. react()       — Enables React Fast Refresh (hot reloading)
 *   2. tailwindcss() — Processes TailwindCSS v4 styles at build time
 *
 * The server proxy forwards /api requests to our FastAPI backend
 * so we don't hit CORS issues during development.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],

  server: {
    port: 5173,
    /* Proxy API calls to FastAPI backend during development */
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
