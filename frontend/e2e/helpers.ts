import { expect, type Page } from "@playwright/test";

export const PASSWORD = "Password123!";

export const USERS = {
  applicant: { email: "tanaka@acme.co.jp", name: "田中 美咲" },
  colleague: { email: "yamamoto@acme.co.jp", name: "山本 拓也" },
  manager: { email: "suzuki@acme.co.jp", name: "鈴木 健一" },
  director: { email: "sato@acme.co.jp", name: "佐藤 直子" },
  finance: { email: "nakamura@acme.co.jp", name: "中村 彩" },
  admin: { email: "admin@acme.co.jp", name: "管理 太郎" },
} as const;

export async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill(email);
  await page.getByLabel("パスワード").fill(PASSWORD);
  await page.getByRole("button", { name: "ログイン" }).click();
  await page.waitForURL("**/dashboard");
}

export async function logout(page: Page) {
  await page.getByTestId("user-menu").click();
  await page.getByTestId("logout").click();
  await page.waitForURL("**/login");
}

/** Files an expense request through the UI and returns the request number. */
export async function fileExpenseRequest(page: Page, title: string): Promise<string> {
  await page.goto("/requests/new");
  await page.getByTestId("template-card-EXPENSE").click();

  await page.getByLabel("件名").fill(title);
  await page.getByLabel("利用日").fill("2026-08-03");
  await page.getByLabel("費目").selectOption("交通費");
  await page.getByLabel("金額（円）").fill("18400");
  await page.getByLabel("利用目的").fill("名古屋支社での定例会議に伴う交通費");
  await page.getByTestId("submit-request").click();

  await page.waitForURL(/\/requests\/\d+$/);
  await expect(page.getByTestId("status-badge").first()).toHaveAttribute("data-status", "pending");
  return (await page.locator("nav[aria-label='パンくず'] span.font-mono").innerText()).trim();
}

export async function openRequest(page: Page, requestNumber: string) {
  await page.goto("/requests?scope=inbox");
  await page.getByRole("row", { name: new RegExp(requestNumber) }).getByRole("link").click();
  await page.waitForURL(/\/requests\/\d+$/);
}
