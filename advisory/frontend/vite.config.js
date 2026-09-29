import { defineConfig } from "vite";

// Advisory runs on its own ports (5180 / 8001) so it can run alongside the watchlist (5173 / 8000).
export default defineConfig({
  server: {
    port: 5180,
    proxy: {
      "/api": "http://127.0.0.1:8001",
    },
  },
});
