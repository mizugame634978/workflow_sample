import type { Metadata } from "next";

import { PageHeader } from "@/components/page-header";
import { TemplateEditor } from "@/components/template-editor";
import { apiFetch } from "@/lib/api";
import type { ItemList, User } from "@/lib/types";

export const metadata: Metadata = { title: "フォームの作成" };

export default async function NewTemplatePage() {
  const users = await apiFetch<ItemList<User>>("/api/v1/users");

  return (
    <>
      <PageHeader
        title="フォームの作成"
        description="入力項目と承認ルートを定義すると、すぐに申請できるようになります。"
      />
      <TemplateEditor users={users.items} />
    </>
  );
}
