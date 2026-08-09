import { defineConfig, devices } from "@playwright/test";

const FRONTEND = "http://127.0.0.1:3100";
const BACKEND_PORT = 8100;
/** The E2E run owns its own database file, reset by `e2e/global-setup.ts`. */
const E2E_DATABASE = "sqlite:///./workflow-e2e.db";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  // The suite mutates a single shared database, so it runs serially by design.
  workers: 1,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  timeout: 45_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: FRONTEND,
    locale: "ja-JP",
    timezoneId: "Asia/Tokyo",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
        // Allows running against a pre-installed Chromium (CI images, sandboxes).
        launchOptions: process.env.CHROMIUM_PATH
          ? { executablePath: process.env.CHROMIUM_PATH }
          : {},
      },
    },
  ],
  webServer: [
    {
      command: `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port ${BACKEND_PORT}`,
      cwd: "../backend",
      env: { WF_DATABASE_URL: E2E_DATABASE, WF_CORS_ORIGINS: `["${FRONTEND}"]` },
      url: `http://127.0.0.1:${BACKEND_PORT}/healthz`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      stdout: "ignore",
    },
    {
      // A production build keeps page loads predictable; `next dev` compiles
      // routes on first hit, which makes the first navigation of a spec flaky.
      command: "npm run build && npm run start -- --port 3100",
      env: { API_BASE_URL: `http://127.0.0.1:${BACKEND_PORT}` },
      url: `${FRONTEND}/login`,
      reuseExistingServer: !process.env.CI,
      timeout: 240_000,
      stdout: "ignore",
    },
  ],
});
