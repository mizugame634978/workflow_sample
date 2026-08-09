"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ClientApiError, call } from "@/lib/client";
import type { RequestDetail } from "@/lib/types";

type Action = "approve" | "reject" | "send-back" | "cancel" | "submit";

const PROMPTS: Record<string, { title: string; label: string; required: boolean; cta: string }> = {
  approve: { title: "この申請を承認します", label: "コメント（任意）", required: false, cta: "承認する" },
  reject: { title: "この申請を却下します", label: "却下理由", required: true, cta: "却下する" },
  "send-back": {
    title: "この申請を差し戻します",
    label: "差戻し理由",
    required: true,
    cta: "差し戻す",
  },
};

export function RequestActions({ request }: { request: RequestDetail }) {
  const router = useRouter();
  const [dialog, setDialog] = useState<Action | null>(null);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const { permissions } = request;
  const hasAction =
    permissions.can_approve || permissions.can_submit || permissions.can_cancel;

  async function run(action: Action, body?: Record<string, unknown>) {
    setPending(true);
    setError(null);
    try {
      await call(`requests/${request.id}/${action}`, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      });
      setDialog(null);
      setComment("");
      router.refresh();
    } catch (caught) {
      setError(caught instanceof ClientApiError ? caught.message : "処理できませんでした");
    } finally {
      setPending(false);
    }
  }

  if (!hasAction) {
    return (
      <p className="px-5 py-4 text-sm text-slate-500">
        現在この申請に対して実行できる操作はありません。
      </p>
    );
  }

  const prompt = dialog ? PROMPTS[dialog] : undefined;

  return (
    <div className="space-y-2 p-4">
      {error ? (
        <p role="alert" data-testid="action-error" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </p>
      ) : null}

      {permissions.can_approve ? (
        <>
          <Button
            className="w-full"
            variant="success"
            data-testid="action-approve"
            onClick={() => setDialog("approve")}
          >
            承認する
          </Button>
          <Button
            className="w-full"
            variant="warning"
            data-testid="action-send-back"
            onClick={() => setDialog("send-back")}
          >
            差し戻す
          </Button>
          <Button
            className="w-full"
            variant="danger"
            data-testid="action-reject"
            onClick={() => setDialog("reject")}
          >
            却下する
          </Button>
        </>
      ) : null}

      {permissions.can_submit ? (
        <Button
          className="w-full"
          data-testid="action-submit"
          disabled={pending}
          onClick={() => void run("submit")}
        >
          この内容で提出する
        </Button>
      ) : null}

      {permissions.can_cancel ? (
        <Button
          className="w-full"
          variant="secondary"
          data-testid="action-cancel"
          disabled={pending}
          onClick={() => {
            if (confirm("この申請を取り下げます。よろしいですか？")) void run("cancel");
          }}
        >
          申請を取り下げる
        </Button>
      ) : null}

      {dialog && prompt ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-slate-900/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-label={prompt.title}
          data-testid="action-dialog"
        >
          <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
            <h2 className="text-base font-semibold text-slate-900">{prompt.title}</h2>
            <p className="mt-1 text-sm text-slate-500">
              {request.request_number}／{request.title}
            </p>

            <label className="label mt-4" htmlFor="action-comment">
              {prompt.label}
            </label>
            <textarea
              id="action-comment"
              data-testid="action-comment"
              className="input"
              rows={4}
              value={comment}
              placeholder={prompt.required ? "理由を具体的に記入してください" : "申し送り事項があれば入力"}
              onChange={(event) => setComment(event.target.value)}
            />
            {prompt.required && !comment.trim() ? (
              <p className="mt-1.5 text-xs text-slate-500">理由の入力が必要です。</p>
            ) : null}

            <div className="mt-5 flex justify-end gap-2">
              <Button
                variant="secondary"
                onClick={() => {
                  setDialog(null);
                  setComment("");
                  setError(null);
                }}
              >
                閉じる
              </Button>
              <Button
                data-testid="action-confirm"
                variant={dialog === "approve" ? "success" : dialog === "reject" ? "danger" : "warning"}
                disabled={pending || (prompt.required && !comment.trim())}
                onClick={() => void run(dialog, { comment })}
              >
                {pending ? "処理中…" : prompt.cta}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
