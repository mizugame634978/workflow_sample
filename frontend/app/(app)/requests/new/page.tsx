import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { apiFetch } from "@/lib/api";
import type { ItemList, TemplateSummary } from "@/lib/types";

export const metadata: Metadata = { title: "新規申請" };

export default async function NewRequestPage() {
  const templates = await apiFetch<ItemList<TemplateSummary>>("/api/v1/templates");
  const categories = [...new Set(templates.items.map((template) => template.category))];

  return (
    <>
      <PageHeader
        title="新規申請"
        description="申請フォームを選択してください。フォームごとに承認ルートが決まっています。"
      />

      {templates.items.length === 0 ? (
        <div className="card">
          <EmptyState
            title="利用できる申請フォームがありません"
            description="管理者にフォームの作成を依頼してください。"
          />
        </div>
      ) : (
        categories.map((category) => (
          <section key={category} className="mb-6">
            <h2 className="mb-3 text-sm font-semibold text-slate-900">{category}</h2>
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {templates.items
                .filter((template) => template.category === category)
                .map((template) => (
                  <li key={template.id}>
                    <Link
                      href={`/requests/new/${template.id}`}
                      data-testid={`template-card-${template.code}`}
                      className="card flex h-full flex-col p-4 transition-shadow hover:shadow-md"
                    >
                      <p className="text-sm font-semibold text-slate-900">{template.name}</p>
                      <p className="mt-1.5 flex-1 text-xs leading-relaxed text-slate-500">
                        {template.description}
                      </p>
                      <p className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-400">
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-slate-500">
                          {template.code}
                        </span>
                        承認 {template.step_count} 段階
                      </p>
                    </Link>
                  </li>
                ))}
            </ul>
          </section>
        ))
      )}
    </>
  );
}
