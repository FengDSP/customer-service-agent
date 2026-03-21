import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  use: {
    baseURL: "http://localhost:3000",
    headless: true,
  },
  webServer: [
    {
      command: "cd ../../.. && uvicorn agent.api:app --port 8000",
      port: 8000,
      cwd: __dirname,
      reuseExistingServer: true,
      timeout: 15000,
    },
    {
      command: "npm run dev -- --port 3000",
      port: 3000,
      cwd: __dirname,
      reuseExistingServer: true,
      timeout: 30000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
