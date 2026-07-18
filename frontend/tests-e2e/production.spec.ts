import { expect, test } from "@playwright/test";

const title = "How independent teams evaluate reliable AI systems";
const body = `## Evaluation starts with evidence

Independent teams document sources, define measurable acceptance criteria and reproduce every benchmark before release. They also record limitations so readers can distinguish observed results from assumptions.

## Production monitoring matters

Reliable artificial intelligence systems require ongoing monitoring, incident review and clear human ownership. A strong process connects model behavior to user outcomes without hiding uncertainty.

## Conclusion

Evidence, transparent reporting and continuous monitoring help teams improve artificial intelligence systems responsibly.`;

test("reader and editor production journeys", async ({ page, request }) => {
  const browserErrors: string[] = [];
  page.on("console", (message) => { if (message.type() === "error") browserErrors.push(message.text()); });
  page.on("pageerror", (error) => browserErrors.push(error.message));
  await page.addInitScript(() => {
    (window as any).__aionCLS = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as any) {
        if (!entry.hadRecentInput) (window as any).__aionCLS += entry.value;
      }
    }).observe({ type: "layout-shift", buffered: true });
  });
  await page.goto("/signup");
  await page.getByLabel("Name").fill("AION Owner");
  await page.getByLabel("Email").fill("owner-e2e@example.com");
  await page.getByLabel("Password").fill("StrongPassword123!");
  await page.getByLabel(/Owner setup token/).fill("playwright-owner-setup-token");
  await expect(page.getByLabel("Email")).toHaveValue("owner-e2e@example.com");
  await page.getByLabel(/Owner setup token/).press("Enter");
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: /Hello, AION/ })).toBeVisible();

  await page.getByRole("link", { name: "Administration" }).click();
  await page.getByRole("tab", { name: "Content" }).click();
  await page.getByRole("link", { name: "New article" }).click();
  await page.getByLabel("Title", { exact: true }).fill(title);
  await page.getByLabel("Summary").fill("An evidence-based guide to evaluating and operating reliable artificial intelligence systems.");
  await page.getByLabel(/^Body/).fill(body);

  const cover = await request.get("http://127.0.0.1:8000/og-cover.png");
  expect(cover.ok()).toBeTruthy();
  await page.getByLabel("Upload image").setInputFiles({
    name: "aion-cover.png",
    mimeType: "image/png",
    buffer: await cover.body(),
  });
  await expect(page.getByText("Image uploaded, optimized and verified")).toBeVisible();
  await page.getByLabel("Alt text").fill("Editors reviewing an independent artificial intelligence evaluation");
  await page.getByLabel(/Featured/).check();
  await page.getByLabel(/Breaking news/).check();
  await page.getByRole("button", { name: "Publish" }).click();
  await expect(page.getByText("Article published")).toBeVisible();

  await page.goto("/articles");
  await expect(page.getByRole("heading", { name: "Articles" })).toBeVisible();
  await expect(page.getByRole("link", { name: title }).first()).toBeVisible();
  await page.getByLabel("Search articles").fill("independent teams");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByRole("link", { name: title }).first()).toBeVisible();
  await page.getByRole("link", { name: title }).first().click();
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/article\/how-independent-teams/);
  await expect(page.locator("article img").first()).toHaveAttribute("src", /^http:\/\/127\.0\.0\.1:8000\/api\/public\/images\//);

  await page.route("**/api/public/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (["/api/public/hero", "/api/public/articles", "/api/public/tags"].includes(path)) {
      await new Promise((resolve) => setTimeout(resolve, 350));
    }
    await route.continue();
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  await page.waitForTimeout(500);
  expect(await page.evaluate(() => (window as any).__aionCLS)).toBeLessThan(0.1);
  await page.unroute("**/api/public/**");
  await page.getByLabel("Newsletter email").fill("reader-e2e@example.com");
  await page.getByRole("button", { name: "Subscribe" }).last().click();
  await expect(page.getByText("Subscribed!")).toBeVisible();

  for (const path of ["/categories", "/tags", "/about", "/privacy", "/terms", "/contact"]) {
    await page.goto(path);
    await expect(page.locator("main h1")).toBeVisible();
  }
  await page.goto("/does-not-exist");
  await expect(page.getByRole("heading", { name: /Page not found/ })).toBeVisible();
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", "noindex,nofollow");

  const rss = await request.get("http://127.0.0.1:8000/rss.xml");
  expect(rss.ok()).toBeTruthy();
  expect(await rss.text()).toContain("<rss version=\"2.0\">");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/articles");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();

  await page.goto("/admin");
  await page.getByRole("tab", { name: "Content" }).click();
  await page.getByRole("row").filter({ hasText: title }).getByRole("link", { name: "Edit" }).click();
  await page.getByRole("button", { name: "Unpublish" }).click();
  await expect(page.getByText("Unpublished (draft)")).toBeVisible();
  await page.goto("/articles");
  await expect(page.getByRole("link", { name: title })).toHaveCount(0);
  expect(browserErrors).toEqual([]);
});
