import { expect, test } from "@playwright/test";

import { USERS, login, logout } from "./helpers";

test.describe("認証", () => {
  test("未ログインでアクセスするとログイン画面へ誘導される", async ({ page }) => {
    await page.goto("/requests");
    await expect(page).toHaveURL(/\/login\?next=%2Frequests/);
  });

  test("誤ったパスワードではログインできない", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill(USERS.applicant.email);
    await page.getByLabel("パスワード").fill("wrong-password");
    await page.getByRole("button", { name: "ログイン" }).click();

    await expect(page.getByTestId("login-error")).toContainText("正しくありません");
    await expect(page).toHaveURL(/\/login/);
  });

  test("ログインするとダッシュボードが表示される", async ({ page }) => {
    await login(page, USERS.applicant.email);

    await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
    await expect(page.getByTestId("user-menu")).toContainText(USERS.applicant.name);
  });

  test("ログアウトするとログイン画面に戻る", async ({ page }) => {
    await login(page, USERS.applicant.email);
    await logout(page);

    await expect(page.getByRole("heading", { name: "ログイン" })).toBeVisible();
  });

  test("一般ユーザーには管理メニューが表示されない", async ({ page }) => {
    await login(page, USERS.applicant.email);

    await expect(page.getByRole("link", { name: "フォーム管理" })).toHaveCount(0);
  });

  test("管理者には管理メニューが表示される", async ({ page }) => {
    await login(page, USERS.admin.email);

    await expect(page.getByRole("link", { name: "フォーム管理" }).first()).toBeVisible();
  });
});
