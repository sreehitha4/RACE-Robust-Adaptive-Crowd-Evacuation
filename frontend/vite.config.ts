import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The FastAPI backend (workstream 4). Override when it runs elsewhere, e.g.
// RACE_BACKEND=http://192.168.1.20:8000 npm run dev
const backend = process.env.RACE_BACKEND ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": backend,
      "/ws": { target: backend.replace(/^http/, "ws"), ws: true },
    },
  },
});
