import { defineConfig } from "vite";

// Forward /api/* to FastAPI so the browser only ever talks to one origin (no CORS needed).
export default defineConfig({
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
