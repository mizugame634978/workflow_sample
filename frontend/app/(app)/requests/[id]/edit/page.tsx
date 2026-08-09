import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { RequestForm } from "@/components/request-form";
import { apiFetchOrNull } from "@/lib/api";
import type { RequestDetail } from "@/lib/types";

export const metadata: Metadata = { title: "申請の編集" };

export default async function EditRequestPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const request = await apiFetchOrNull<RequestDetail>(`/api/v1/requests/${id}`);
  if (!request) notFound();
  if (!request.permissions.can_edit) redirect(`/requests/${id}`);

  return (
    <>
      <PageHeader
        title="申請の編集"
        description={`${request.request_number}／${request.template_name}`}
        actions={
          <Link href={`/requests/${id}`} className="text-sm text-slate-500 hover:underline">
            詳細に戻る
          </Link>
        }
      />

      {request.last_send_back_comment ? (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
          <p className="text-sm font-semibold text-amber-900">差戻しコメント</p>
          <p className="mt-1 text-sm text-amber-800">{request.last_send_back_comment}</p>
        </div>
      ) : null}

      <div className="card p-5">
        <RequestForm
          template={{
            id: request.template.id,
            name: request.template.name,
            form_fields: request.template.form_fields,
          }}
          requestId={request.id}
          initialTitle={request.title}
          initialValues={request.form_data}
        />
      </div>
    </>
  );
}
