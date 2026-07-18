import { defineConfig } from "@playwright/test";

const runId = `${process.pid}-${Date.now()}`;
const python = process.env.PLAYWRIGHT_PYTHON || "python";

export default defineConfig({
  testDir: "./tests-e2e",
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? {
          executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
          args: ["--no-sandbox"],
        }
      : undefined,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `${python} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "../backend",
      url: "http://127.0.0.1:8000/api/health",
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        ENV: "test",
        DATABASE_URL: `sqlite:////tmp/aion-playwright-${runId}.db`,
        UPLOAD_DIR: `/tmp/aion-playwright-uploads-${runId}`,
        PUBLIC_API_URL: "http://127.0.0.1:8000",
        SITE_URL: "https://aion-news-os.vercel.app",
        IMAGE_PROVIDER: "none",
        SECRET_KEY: "playwright-secret-key-with-at-least-32-characters",
        ADMIN_SETUP_TOKEN: "playwright-owner-setup-token",
        CORS_ORIGINS: "http://127.0.0.1:4173",
      },
    },
    {
      command: "npm run preview -- --host 127.0.0.1 --port 4173",
      url: "http://127.0.0.1:4173",
      timeout: 30_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
