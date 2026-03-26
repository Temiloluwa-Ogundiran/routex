import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  webServer: [
    {
      command: "node ../mintlify-docs/stub-server.mjs",
      url: "http://127.0.0.1:3001",
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command:
        "cmd /c \"set NEXT_PUBLIC_POSTHOG_KEY=ph_test_key&& set NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com&& set MINTLIFY_DOCS_ORIGIN=http://127.0.0.1:3001&& set NEXT_PUBLIC_DOCS_URL=http://127.0.0.1:3001&& npm run build && npx next start --hostname 127.0.0.1 --port 3000\"",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
      timeout: 240000,
    },
  ],
  use: {
    ...devices["Desktop Chrome"],
    channel: "chrome",
    headless: true,
  },
});
