/**
 * Captures every screen so the UI can be reviewed as images.
 * Run with: npx playwright test screenshots
 */
import { expect, test } from "@playwright/test";

import { USERS, login } from "./helpers";

const DIR = "screenshots";

test.describe("画面キャプチャ", () => {
  test("ログイン画面", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
    await page.screenshot({ path: `${DIR}/01-login.png`, fullPage: true });
  });

  test("申請者の画面", async ({ page }) => {
    await login(page, USERS.applicant.email);
    await expect(page.getByTestId("stat-open")).toBeVisible();
    await page.screenshot({ path: `${DIR}/02-dashboard.png`, fullPage: true });

    await page.goto("/requests?scope=mine");
    await expect(page.getByTestId("request-row").first()).toBeVisible();
    await page.screenshot({ path: `${DIR}/03-request-list.png`, fullPage: true });

    await page.goto("/requests/new");
    await expect(page.getByTestId("template-card-EXPENSE")).toBeVisible();
    await page.screenshot({ path: `${DIR}/04-template-picker.png`, fullPage: true });

    await page.getByTestId("template-card-EXPENSE").click();
    await page.getByLabel("件名").fill("11月度 交通費精算");
    await page.getByLabel("金額（円）").fill("24800");
    await expect(page.getByLabel("利用目的")).toBeVisible();
    await page.screenshot({ path: `${DIR}/05-request-form.png`, fullPage: true });

    await page.goto("/requests?scope=mine");
    await page.getByTestId("request-row").first().getByRole("link").first().click();
    await page.waitForURL(/\/requests\/\d+$/);
    await expect(page.getByTestId("request-title")).toBeVisible();
    await page.screenshot({ path: `${DIR}/06-request-detail.png`, fullPage: true });
  });

  test("承認者の画面", async ({ page }) => {
    await login(page, USERS.manager.email);
    await page.goto("/inbox");
    await expect(page.getByTestId("inbox-count")).toBeVisible();
    await page.screenshot({ path: `${DIR}/07-inbox.png`, fullPage: true });

    await page.getByTestId("notification-bell").click();
    await expect(page.getByTestId("notification-panel")).toBeVisible();
    await page.screenshot({ path: `${DIR}/08-notifications.png` });

    await page.goto("/inbox");
    const row = page.getByTestId("request-row").first();
    if (await row.isVisible()) {
      await row.getByRole("link").first().click();
      await page.waitForURL(/\/requests\/\d+$/);
      await page.getByTestId("action-approve").click();
      await expect(page.getByTestId("action-dialog")).toBeVisible();
      await page.screenshot({ path: `${DIR}/09-approve-dialog.png` });
    }
  });

  test("管理者の画面", async ({ page }) => {
    await login(page, USERS.admin.email);
    await page.goto("/templates");
    await expect(page.getByTestId("template-row").first()).toBeVisible();
    await page.screenshot({ path: `${DIR}/10-templates.png`, fullPage: true });

    await page.getByTestId("template-row").first().getByRole("link").click();
    await expect(page.getByTestId("save-template")).toBeVisible();
    await page.screenshot({ path: `${DIR}/11-template-editor.png`, fullPage: true });

    await page.goto("/users");
    await expect(page.getByTestId("user-row").first()).toBeVisible();
    await page.screenshot({ path: `${DIR}/12-users.png`, fullPage: true });

    await page.goto("/dashboard");
    await expect(page.getByTestId("stat-approved")).toBeVisible();
    await page.screenshot({ path: `${DIR}/13-admin-dashboard.png`, fullPage: true });
  });

  test("モバイル表示", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await login(page, USERS.applicant.email);
    await expect(page.getByTestId("stat-open")).toBeVisible();
    await page.screenshot({ path: `${DIR}/14-mobile-dashboard.png`, fullPage: true });

    await page.goto("/requests?scope=mine");
    await page.getByTestId("request-row").first().getByRole("link").first().click();
    await page.waitForURL(/\/requests\/\d+$/);
    await page.screenshot({ path: `${DIR}/15-mobile-detail.png`, fullPage: true });
  });
});
