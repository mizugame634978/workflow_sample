import { expect, test } from "@playwright/test";

import { USERS, login, logout } from "./helpers";

test.describe("管理機能", () => {
  test("管理者は申請フォームを作成でき、すぐに申請できる", async ({ page }) => {
    await login(page, USERS.admin.email);
    await page.goto("/templates");
    await page.getByTestId("new-template").click();

    await page.getByLabel("フォームコード").fill("EQUIPMENT");
    await page.getByLabel("フォーム名").fill("備品貸出申請");
    await page.getByLabel("カテゴリ").fill("総務");
    await page.getByLabel("説明").fill("社内備品の貸出を申請します。");

    await page.getByTestId("add-field").click();
    const field = page.getByTestId("field-row").first();
    await field.getByLabel("項目名").fill("備品名");
    await field.getByLabel("キー").fill("equipment");
    await field.getByLabel("必須").check();

    await page.getByTestId("save-template").click();
    await page.waitForURL("**/templates");
    await expect(page.getByTestId("template-row").filter({ hasText: "備品貸出申請" })).toBeVisible();

    await page.goto("/requests/new");
    await expect(page.getByTestId("template-card-EQUIPMENT")).toBeVisible();
  });

  test("フォームを停止すると新規申請の一覧から消える", async ({ page }) => {
    await login(page, USERS.admin.email);
    await page.goto("/templates");
    await page.getByTestId("template-row").filter({ hasText: "出張申請" }).getByRole("link").click();
    await page.getByTestId("toggle-activation").click();

    await expect(page.getByTestId("toggle-activation")).toContainText("再開");

    await page.goto("/requests/new");
    await expect(page.getByTestId("template-card-TRIP")).toHaveCount(0);

    // 後続テストのために元へ戻す
    await page.goto("/templates");
    await page.getByTestId("template-row").filter({ hasText: "出張申請" }).getByRole("link").click();
    await page.getByTestId("toggle-activation").click();
    await expect(page.getByTestId("toggle-activation")).toContainText("停止");
  });

  test("管理者はユーザーを登録でき、登録したユーザーはログインできる", async ({ page }) => {
    await login(page, USERS.admin.email);
    await page.goto("/users");

    await page.getByLabel("氏名").fill("新人 七海");
    await page.getByLabel("メールアドレス").fill("shinjin@acme.co.jp");
    await page.getByLabel("初期パスワード").fill("Password123!");
    await page.getByLabel("部署").fill("営業部");
    await page.getByLabel("上長").selectOption({ label: "鈴木 健一（プロダクト開発部）" });
    await page.getByTestId("invite-user").click();

    await expect(page.getByTestId("invite-success")).toBeVisible();
    await expect(page.getByTestId("user-row").filter({ hasText: "新人 七海" })).toBeVisible();

    await logout(page);
    await login(page, "shinjin@acme.co.jp");
    await expect(page.getByTestId("user-menu")).toContainText("新人 七海");
  });

  test("管理者は組織全体の申請を横断して確認できる", async ({ page }) => {
    await login(page, USERS.admin.email);
    await page.goto("/requests?scope=all");

    await expect(page.getByRole("tab", { name: "組織全体" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(page.getByTestId("request-row").first()).toBeVisible();
  });
});
