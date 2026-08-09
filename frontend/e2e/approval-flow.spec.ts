import { expect, test } from "@playwright/test";

import { USERS, fileExpenseRequest, login, logout, openRequest } from "./helpers";

test.describe("承認フロー", () => {
  test("申請 → 上長承認 → 経理承認で承認済みになる", async ({ page }) => {
    await login(page, USERS.applicant.email);
    const requestNumber = await fileExpenseRequest(page, "E2E 名古屋出張の交通費精算");

    await expect(page.getByTestId("route-step-0")).toHaveAttribute("data-current", "true");
    await expect(page.getByTestId("route-step-0")).toContainText(USERS.manager.name);
    await logout(page);

    // 1段階目: 上長（課長）が承認する
    await login(page, USERS.manager.email);
    await expect(page.getByTestId("stat-awaiting")).not.toHaveText("0");
    await openRequest(page, requestNumber);
    await page.getByTestId("action-approve").click();
    await page.getByTestId("action-comment").fill("内容を確認しました");
    await page.getByTestId("action-confirm").click();

    await expect(page.getByTestId("status-badge").first()).toHaveAttribute("data-status", "pending");
    await expect(page.getByTestId("route-step-0")).toHaveAttribute("data-status", "approved");
    await expect(page.getByTestId("route-step-1")).toHaveAttribute("data-current", "true");
    await logout(page);

    // 2段階目: 経理（管理者権限）が承認して完了
    await login(page, USERS.finance.email);
    await openRequest(page, requestNumber);
    await page.getByTestId("action-approve").click();
    await page.getByTestId("action-confirm").click();

    await expect(page.getByTestId("status-badge").first()).toHaveAttribute(
      "data-status",
      "approved",
    );
    await expect(page.getByTestId("route-step-1")).toHaveAttribute("data-status", "approved");
    await expect(page.getByText("承認", { exact: true }).first()).toBeVisible();
  });

  test("承認順序を飛ばした承認はできない", async ({ page }) => {
    await login(page, USERS.applicant.email);
    const requestNumber = await fileExpenseRequest(page, "E2E 順序チェック用の精算");
    await logout(page);

    // 2段階目の承認者（経理）にはまだ操作ボタンが出ない
    await login(page, USERS.finance.email);
    await page.goto("/requests?scope=all");
    await page.getByRole("row", { name: new RegExp(requestNumber) }).getByRole("link").click();

    await expect(page.getByTestId("action-approve")).toHaveCount(0);
    await expect(page.getByText("実行できる操作はありません")).toBeVisible();
  });

  test("申請者は自分の申請を取り下げられる", async ({ page }) => {
    await login(page, USERS.colleague.email);
    await page.goto("/requests/new");
    await page.getByTestId("template-card-LEAVE").click();
    await page.getByLabel("件名").fill("E2E 取り下げテスト用の休暇申請");
    await page.getByLabel("休暇区分").selectOption("有給休暇");
    await page.getByLabel("開始日").fill("2026-09-01");
    await page.getByLabel("終了日").fill("2026-09-02");
    await page.getByTestId("submit-request").click();
    await page.waitForURL(/\/requests\/\d+$/);

    page.on("dialog", (dialog) => dialog.accept());
    await page.getByTestId("action-cancel").click();

    await expect(page.getByTestId("status-badge").first()).toHaveAttribute(
      "data-status",
      "cancelled",
    );
  });
});
