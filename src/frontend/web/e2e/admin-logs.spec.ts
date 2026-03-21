import { expect, test } from "@playwright/test";

/**
 * Admin UI e2e tests.
 *
 * Prerequisites:
 * - Backend running on :8000 (uvicorn agent.api:app)
 * - Frontend running on :3000 (npm run dev)
 * - At least one business config exists (beauty_lab)
 * - At least one JSONL log file exists in logs/llm/
 *
 * Generate test logs by running a CLI conversation first:
 *   python -m cli --business beauty_lab --customer CUS-001 --auto-approve
 */

test.describe("Admin UI — Layout", () => {
  test("homepage redirects to admin logs", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL(/\/admin\/logs/);
    expect(page.url()).toContain("/admin/logs");
  });

  test("admin layout shows business selector and nav", async ({ page }) => {
    await page.goto("/admin/logs?biz=beauty_lab");

    // Business selector exists
    const selector = page.locator("select");
    await expect(selector).toBeVisible();

    // Left nav shows LLM Log Viewer
    await expect(page.getByText("LLM Log Viewer")).toBeVisible();

    // Header shows CS Admin
    await expect(page.getByText("CS Admin")).toBeVisible();
  });

  test("customer sessions page renders", async ({ page }) => {
    await page.goto("/admin/logs?biz=beauty_lab");
    await expect(page.getByText("Customer Sessions")).toBeVisible();
  });
});

test.describe("Admin UI — Log Viewer Drill-down", () => {
  test("customer sessions table loads data", async ({ page }) => {
    await page.goto("/admin/logs?biz=beauty_lab");
    await expect(page.getByText("Customer Sessions")).toBeVisible();

    // Wait for table to have at least one row or show "No log files"
    const hasData = page.locator("table tbody tr").first();
    const noData = page.getByText("No log files found");
    await expect(hasData.or(noData)).toBeVisible({ timeout: 10000 });
  });

  test("clicking customer navigates to draft replies", async ({ page }) => {
    await page.goto("/admin/logs?biz=beauty_lab");
    await expect(page.getByText("Customer Sessions")).toBeVisible();

    // Try to click first customer link in the table
    const firstLink = page.locator("table tbody tr a").first();
    const noData = page.getByText("No log files found");

    // Skip if no data
    if (await noData.isVisible().catch(() => false)) {
      test.skip();
      return;
    }

    await firstLink.click({ timeout: 10000 });

    // Should navigate to draft replies page with breadcrumb
    await expect(page.getByText("Draft Replies")).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("link", { name: "Sessions" })).toBeVisible();
  });

  test("draft replies page shows entries or empty state", async ({ page }) => {
    // Navigate directly to a customer's logs
    await page.goto("/admin/logs/CUS-001?biz=beauty_lab");

    // Should show either entries or empty state
    const table = page.locator("table");
    const noEntries = page.getByText("No log entries found");
    await expect(table.or(noEntries)).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Admin UI — Replay Page", () => {
  test("replay page renders editable fields", async ({ page }) => {
    // Go to replay page — even if the entry doesn't exist, the page should render
    await page.goto("/admin/logs/CUS-001/0/replay?biz=beauty_lab&call=0");

    // Wait for either the replay form or "not found" message
    const replayHeading = page.getByText("Replay LLM Call");
    const notFound = page.getByText("not found");
    await expect(replayHeading.or(notFound)).toBeVisible({ timeout: 10000 });

    // If replay page loaded, check for key elements
    if (await replayHeading.isVisible().catch(() => false)) {
      await expect(page.getByText("Send Replay")).toBeVisible();
      await expect(page.locator("textarea").first()).toBeVisible();
      await expect(page.getByText("Model")).toBeVisible();
    }
  });
});

test.describe("Admin UI — Navigation", () => {
  test("breadcrumb Sessions link navigates back", async ({ page }) => {
    await page.goto("/admin/logs/CUS-001?biz=beauty_lab");

    const sessionsLink = page.getByRole("link", { name: "Sessions" });
    await expect(sessionsLink).toBeVisible();
    await sessionsLink.click();

    await expect(page.getByText("Customer Sessions")).toBeVisible();
  });

  test("left nav link navigates to log viewer", async ({ page }) => {
    await page.goto("/admin/logs/CUS-001?biz=beauty_lab");

    await page.getByText("LLM Log Viewer").click();
    await expect(page.getByText("Customer Sessions")).toBeVisible();
  });
});
