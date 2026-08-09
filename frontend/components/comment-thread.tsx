"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ClientApiError, call } from "@/lib/client";
import { formatDateTime, initial } from "@/lib/format";
import type { Comment } from "@/lib/types";

export function CommentThread({
  requestId,
  comments,
  canComment,
}: {
  requestId: number;
  comments: Comment[];
  canComment: boolean;
}) {
  const router = useRouter();
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function post(event: React.FormEvent) {
    event.preventDefault();
    if (!body.trim()) return;
    setPending(true);
    setError(null);
    try {
      await call(`requests/${requestId}/comments`, {
        method: "POST",
        body: JSON.stringify({ body: body.trim() }),
      });
      setBody("");
      router.refresh();
    } catch (caught) {
      setError(caught instanceof ClientApiError ? caught.message : "投稿できませんでした");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="p-5">
      {comments.length === 0 ? (
        <p className="text-sm text-slate-500">まだコメントはありません。</p>
      ) : (
        <ul className="space-y-4">
          {comments.map((comment) => (
            <li key={comment.id} data-testid="comment" className="flex gap-3">
              <span className="grid size-8 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                {initial(comment.user.name)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="flex flex-wrap items-baseline gap-x-2">
                  <span className="text-sm font-medium text-slate-900">{comment.user.name}</span>
                  <span className="text-xs text-slate-400">{comment.user.department}</span>
                  <span className="ml-auto text-xs text-slate-400">
                    {formatDateTime(comment.created_at)}
                  </span>
                </p>
                <p className="mt-1 text-sm leading-relaxed break-words whitespace-pre-wrap text-slate-700">
                  {comment.body}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}

      {canComment ? (
        <form onSubmit={post} className="mt-5 border-t border-slate-100 pt-4">
          {error ? <p className="mb-2 text-sm text-rose-600">{error}</p> : null}
          <label className="sr-only" htmlFor="comment-body">
            コメント
          </label>
          <textarea
            id="comment-body"
            data-testid="comment-input"
            className="input"
            rows={3}
            placeholder="確認事項や申し送りを記入してください"
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />
          <div className="mt-2 flex justify-end">
            <Button type="submit" size="sm" data-testid="comment-submit" disabled={pending || !body.trim()}>
              {pending ? "送信中…" : "コメントする"}
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
