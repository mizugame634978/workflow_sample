import { expect, test } from "@playwright/test";

import { USERS, fileExpenseRequest, login, logout, openRequest } from "./helpers";

test.describe("差戻しと却下", () => {
  test("差し戻された申請は修正して再提出できる", async ({ page }) => {
    await login(page, USERS.applicant.email);
    const requestNumber = await fileExpenseRequest(page, "E2E 差戻しテスト用の精算");
    await logout(page);

    await login(page, USERS.manager.email);
    await openRequest(page, requestNumber);
    await page.getByTestId("action-send-back").click();
    await page.getByTestId("action-comment").fill("金額の内訳を利用目的に追記してください");
    await page.getByTestId("action-confirm").click();
    await expect(page.getByTestId("status-badge").first()).toHaveAttribute("data-status", "draft");
    await logout(page);

    await login(page, USERS.applicant.email);
    await page.goto("/requests?scope=mine");
    await page.getByRole("row", { name: new RegExp(requestNumber) }).getByRole("link").click();

    await expect(page.getByTestId("send-back-notice")).toContainText("内訳");
    await page.getByTestId("edit-request").click();
    await page.getByLabel("利用目的").fill("名古屋支社での定例会議（新幹線往復 18,400 円）");
    await page.getByTestId("submit-request").click();

    await page.waitForURL(/\/requests\/\d+$/);
    await expect(page.getByTestId("status-badge").first()).toHaveAttribute("data-status", "pending");
    await expect(page.getByText("再提出 2 回目")).toBeVisible();
  });

  test("却下には理由が必須で、却下すると申請が終了する", async ({ page }) => {
    await login(page, USERS.applicant.email);
    const requestNumber = await fileExpenseRequest(page, "E2E 却下テスト用の精算");
    await logout(page);

    await login(page, USERS.manager.email);
    await openRequest(page, requestNumber);
    await page.getByTestId("action-reject").click();

    await expect(page.getByTestId("action-confirm")).toBeDisabled();
    await page.getByTestId("action-comment").fill("今期の予算枠を超過しているため却下します");
    await page.getByTestId("action-confirm").click();

    await expect(page.getByTestId("status-badge").first()).toHaveAttribute(
      "data-status",
      "rejected",
    );
    await expect(page.getByText("今期の予算枠を超過しているため却下します").first()).toBeVisible();
  });

  test("入力に不備があると申請できない", async ({ page }) => {
    await login(page, USERS.applicant.email);
    await page.goto("/requests/new");
    await page.getByTestId("template-card-EXPENSE").click();
    await page.getByTestId("submit-request").click();

    await expect(page.getByTestId("form-error")).toBeVisible();
    await expect(page.getByText("件名は必須項目です")).toBeVisible();
    await expect(page.getByText("金額（円）は必須項目です")).toBeVisible();
    await expect(page).toHaveURL(/\/requests\/new\/\d+/);
  });
});
