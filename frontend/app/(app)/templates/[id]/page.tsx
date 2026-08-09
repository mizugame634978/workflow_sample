import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { TemplateActivation } from "@/components/template-activation";
import { TemplateEditor } from "@/components/template-editor";
import { apiFetch, apiFetchOrNull } from "@/lib/api";
import type { ItemList, TemplateDetail, User } from "@/lib/types";

export const metadata: Metadata = { title: "フォームの編集" };

export default async function EditTemplatePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [template, users] = await Promise.all([
    apiFetchOrNull<TemplateDetail>(`/api/v1/templates/${id}`),
    apiFetch<ItemList<User>>("/api/v1/users"),
  ]);
  if (!template) notFound();

  return (
    <>
      <PageHeader
        title={template.name}
        description={`コード: ${template.code}`}
        actions={<TemplateActivation templateId={template.id} isActive={template.is_active} />}
      />
      <TemplateEditor users={users.items} template={template} />
    </>
  );
}
