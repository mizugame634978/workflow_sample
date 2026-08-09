import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { RequestForm } from "@/components/request-form";
import { RoutePreview } from "@/components/route-preview";
import { apiFetchOrNull } from "@/lib/api";
import type { TemplateDetail } from "@/lib/types";

export const metadata: Metadata = { title: "申請の作成" };

export default async function NewRequestFormPage({
  params,
}: {
  params: Promise<{ templateId: string }>;
}) {
  const { templateId } = await params;
  const template = await apiFetchOrNull<TemplateDetail>(`/api/v1/templates/${templateId}`);
  if (!template) notFound();

  return (
    <>
      <PageHeader
        title={template.name}
        description={template.description}
        actions={
          <Link href="/requests/new" className="text-sm text-slate-500 hover:underline">
            フォームを選び直す
          </Link>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <RequestForm template={template} />
        </div>
        <aside className="space-y-4">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">承認ルート</h2>
            </div>
            <RoutePreview steps={template.steps} />
          </div>
          <div className="card p-4">
            <h2 className="text-sm font-semibold text-slate-900">提出前の確認</h2>
            <ul className="mt-2 space-y-1.5 text-xs leading-relaxed text-slate-600">
              <li>・必須項目がすべて入力されているか</li>
              <li>・金額や日付に誤りがないか</li>
              <li>・添付が必要な資料は共有先を本文に記載したか</li>
            </ul>
            <p className="mt-3 text-xs text-slate-400">
              下書き保存しておけば、あとから修正して提出できます。
            </p>
          </div>
        </aside>
      </div>
    </>
  );
}
