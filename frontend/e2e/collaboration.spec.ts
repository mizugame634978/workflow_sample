import { expect, test } from "@playwright/test";

import { USERS, fileExpenseRequest, login, logout, openRequest } from "./helpers";

test.describe("通知とコメント", () => {
  test("承認依頼が承認者に通知され、コメントでやり取りできる", async ({ page }) => {
    await login(page, USERS.applicant.email);
    const requestNumber = await fileExpenseRequest(page, "E2E 通知テスト用の精算");
    await logout(page);

    await login(page, USERS.manager.email);
    await expect(page.getByTestId("notification-count")).toBeVisible();
    await page.getByTestId("notification-bell").click();
    await expect(page.getByTestId("notification-panel")).toContainText("承認を待っています");

    await page.getByTestId("notification-panel").getByRole("link").first().click();
    await page.waitForURL(/\/requests\/\d+$/);

    await page.getByTestId("comment-input").fill("領収書の原本を経理部へ提出してください");
    await page.getByTestId("comment-submit").click();
    await expect(page.getByTestId("comment")).toContainText("領収書の原本");
    await logout(page);

    await login(page, USERS.applicant.email);
    await page.goto("/requests?scope=mine");
    await page.getByRole("row", { name: new RegExp(requestNumber) }).getByRole("link").click();
    await expect(page.getByTestId("comment")).toContainText("領収書の原本");
  });

  test("通知をすべて既読にできる", async ({ page }) => {
    await login(page, USERS.applicant.email);
    await fileExpenseRequest(page, "E2E 既読テスト用の精算");
    await logout(page);

    await login(page, USERS.manager.email);
    await page.getByTestId("notification-bell").click();
    await page.getByRole("button", { name: "すべて既読にする" }).click();

    await expect(page.getByTestId("notification-count")).toHaveCount(0);
  });

  test("関係のない申請は閲覧できない", async ({ page }) => {
    await login(page, USERS.applicant.email);
    const requestNumber = await fileExpenseRequest(page, "E2E 権限テスト用の精算");
    const url = page.url();
    await logout(page);

    await login(page, USERS.colleague.email);
    await page.goto(url);

    await expect(page.getByText("閲覧する権限がありません")).toBeVisible();
    expect(requestNumber).toMatch(/^REQ-/);
  });
});
