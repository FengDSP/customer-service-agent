import { expect, test } from "@playwright/test";

/**
 * CS Worker Chat UI e2e tests.
 *
 * Prerequisites:
 * - Backend running on :8000 (uvicorn agent.api:app)
 * - Frontend running on :3000 (npm run dev)
 * - beauty_lab business config exists
 *
 * Tests use a unique customer ID per run to avoid interference.
 */

const BIZ = "beauty_lab";
const CUST = `e2e-chat-${Date.now()}`;
const API = "http://localhost:8000";

async function postMessage(customerId: string, message: string) {
  const resp = await fetch(`${API}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_id: BIZ, customer_id: customerId, message }),
  });
  if (!resp.ok) throw new Error(`POST /messages failed: ${resp.status}`);
}

test.describe("CS Chat — Navigation", () => {
  test("Chat With Customers nav item is visible", async ({ page }) => {
    await page.goto(`/admin/chat?biz=${BIZ}`);
    await expect(page.getByText("Chat With Customers")).toBeVisible();
  });

  test("chat page renders customer conversations heading", async ({ page }) => {
    await page.goto(`/admin/chat?biz=${BIZ}`);
    await expect(page.getByText("Customer Conversations")).toBeVisible();
  });
});

test.describe("CS Chat — Customer List", () => {
  test("shows no conversations initially for fresh business", async ({ page }) => {
    await page.goto(`/admin/chat?biz=${BIZ}`);
    // Either shows existing conversations or "No conversations yet."
    const table = page.locator("table");
    const empty = page.getByText("No conversations yet.");
    await expect(table.or(empty)).toBeVisible({ timeout: 10000 });
  });

  test("shows customer after message is posted", async ({ page }) => {
    await postMessage(CUST, "Hello, I need help");

    await page.goto(`/admin/chat?biz=${BIZ}`);
    await expect(page.getByText(CUST)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Hello, I need help")).toBeVisible();
  });

  test("unreplied indicator is shown", async ({ page }) => {
    await postMessage(CUST, "Another message");

    await page.goto(`/admin/chat?biz=${BIZ}`);
    // The unreplied dot (blue circle) should exist
    const row = page.locator("tr", { hasText: CUST });
    await expect(row).toBeVisible({ timeout: 10000 });
    // Row should have the blue-50 background class for unreplied
    await expect(row).toHaveClass(/bg-blue-50/);
  });
});

test.describe("CS Chat — Chat View", () => {
  const chatCust = `e2e-view-${Date.now()}`;

  test.beforeAll(async () => {
    await postMessage(chatCust, "I have a question about my appointment");
  });

  test("chat view shows conversation history", async ({ page }) => {
    await page.goto(`/admin/chat/${chatCust}?biz=${BIZ}`);
    await expect(
      page.getByText("I have a question about my appointment")
    ).toBeVisible({ timeout: 10000 });
  });

  test("back button navigates to customer list", async ({ page }) => {
    await page.goto(`/admin/chat/${chatCust}?biz=${BIZ}`);
    await page.getByText("Back").click();
    await expect(page.getByText("Customer Conversations")).toBeVisible();
  });

  test("draft area is visible", async ({ page }) => {
    await page.goto(`/admin/chat/${chatCust}?biz=${BIZ}`);
    await expect(page.locator("textarea")).toBeVisible({ timeout: 10000 });
  });

  test("send button exists and is initially disabled without draft", async ({ page }) => {
    // Post + send so there's no unreplied message (no auto-draft)
    const repliedCust = `e2e-replied-${Date.now()}`;
    await postMessage(repliedCust, "test");
    await fetch(`${API}/conversations/${BIZ}/${repliedCust}/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reply: "done" }),
    });

    await page.goto(`/admin/chat/${repliedCust}?biz=${BIZ}`);
    const sendBtn = page.getByRole("button", { name: "Send" });
    await expect(sendBtn).toBeVisible({ timeout: 10000 });
    await expect(sendBtn).toBeDisabled();
  });
});

test.describe("CS Chat — Context Sidebar", () => {
  test("shows customer context for known customer", async ({ page }) => {
    // CUS-001 exists in beauty_lab CSV data
    await postMessage("CUS-001", "context test");

    await page.goto(`/admin/chat/CUS-001?biz=${BIZ}`);
    await expect(page.getByText("Customer Context")).toBeVisible({ timeout: 10000 });
    // Should show at least one data source table
    await expect(page.getByText("customers")).toBeVisible({ timeout: 10000 });
  });
});
