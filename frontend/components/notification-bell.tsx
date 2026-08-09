"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { call } from "@/lib/client";
import { cn } from "@/lib/cn";
import { formatRelative } from "@/lib/format";
import { NOTIFICATION_LABEL } from "@/lib/status";
import type { Notification } from "@/lib/types";

const POLL_INTERVAL_MS = 30_000;

export function NotificationBell() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const container = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      const data = await call<{ items: Notification[]; unread_count: number }>(
        "notifications?limit=12",
      );
      setItems(data.items);
      setUnread(data.unread_count);
    } catch {
      /* 通知の取得失敗は画面を壊さない */
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [load]);

  useEffect(() => {
    function onClick(event: MouseEvent) {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  async function markAllRead() {
    await call("notifications/read-all", { method: "POST" });
    setUnread(0);
    setItems((current) => current.map((item) => ({ ...item, is_read: true })));
    router.refresh();
  }

  return (
    <div className="relative" ref={container}>
      <button
        type="button"
        data-testid="notification-bell"
        aria-label={`通知${unread > 0 ? `（未読 ${unread} 件）` : ""}`}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="relative grid size-9 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700"
      >
        <svg viewBox="0 0 24 24" fill="none" className="size-5" aria-hidden>
          <path
            d="M6 9a6 6 0 1 1 12 0c0 3.2.7 4.9 1.4 5.8.4.5 0 1.2-.6 1.2H5.2c-.7 0-1-.7-.6-1.2C5.3 13.9 6 12.2 6 9ZM10 19a2 2 0 0 0 4 0"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinejoin="round"
          />
        </svg>
        {unread > 0 ? (
          <span
            data-testid="notification-count"
            className="absolute top-1 right-1 grid min-w-4 place-items-center rounded-full bg-rose-500 px-1 text-[10px] leading-4 font-semibold text-white"
          >
            {unread > 99 ? "99+" : unread}
          </span>
        ) : null}
      </button>

      {open ? (
        <div
          data-testid="notification-panel"
          className="absolute right-0 z-40 mt-2 w-[22rem] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg"
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
            <p className="text-sm font-semibold text-slate-900">通知</p>
            {unread > 0 ? (
              <button
                type="button"
                onClick={markAllRead}
                className="text-xs font-medium text-brand-600 hover:underline"
              >
                すべて既読にする
              </button>
            ) : null}
          </div>

          {items.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-slate-500">通知はありません</p>
          ) : (
            <ul className="max-h-96 divide-y divide-slate-100 overflow-y-auto">
              {items.map((item) => (
                <li key={item.id}>
                  <Link
                    href={`/requests/${item.request.id}`}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "block px-4 py-3 hover:bg-slate-50",
                      !item.is_read && "bg-brand-50/40",
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-semibold text-brand-700">
                        {NOTIFICATION_LABEL[item.type]}
                      </span>
                      <span className="ml-auto text-[11px] text-slate-400">
                        {formatRelative(item.created_at)}
                      </span>
                    </div>
                    <p className="mt-0.5 text-sm leading-snug text-slate-700">{item.message}</p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
