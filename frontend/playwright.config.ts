import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  webServer: {
    command:
      "cmd /c \"npm run build && npx next start --hostname 127.0.0.1 --port 3000\"",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: false,
    timeout: 240000,
  },
  use: {
    ...devices["Desktop Chrome"],
    channel: "chrome",
    headless: true,
  },
});
