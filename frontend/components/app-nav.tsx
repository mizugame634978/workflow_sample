"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";

type Item = { href: string; label: string; icon: keyof typeof ICONS; adminOnly?: boolean };

const ITEMS: Item[] = [
  { href: "/dashboard", label: "ダッシュボード", icon: "home" },
  { href: "/inbox", label: "承認待ち", icon: "inbox" },
  { href: "/requests", label: "申請一覧", icon: "list" },
  { href: "/requests/new", label: "新規申請", icon: "plus" },
  { href: "/templates", label: "フォーム管理", icon: "settings", adminOnly: true },
  { href: "/users", label: "ユーザー管理", icon: "users", adminOnly: true },
];

export function AppNav({
  isAdmin,
  variant = "vertical",
}: {
  isAdmin: boolean;
  variant?: "vertical" | "horizontal";
}) {
  const pathname = usePathname();
  const items = ITEMS.filter((item) => !item.adminOnly || isAdmin);

  return (
    <nav
      aria-label="メインナビゲーション"
      className={cn(
        variant === "vertical"
          ? "flex flex-col gap-0.5 px-3"
          : "flex gap-1 overflow-x-auto px-3 py-2",
      )}
    >
      {items.map((item) => {
        const active =
          item.href === "/requests/new"
            ? pathname.startsWith("/requests/new")
            : pathname === item.href ||
              (item.href !== "/dashboard" &&
                pathname.startsWith(item.href) &&
                !pathname.startsWith("/requests/new"));
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors",
              active
                ? "bg-brand-50 text-brand-700"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
            )}
          >
            <span className={cn(active ? "text-brand-600" : "text-slate-400")}>
              {ICONS[item.icon]}
            </span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

const ICONS = {
  home: (
    <svg viewBox="0 0 24 24" fill="none" className="size-4.5" aria-hidden>
      <path
        d="M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4v-5H9v5H5a1 1 0 0 1-1-1v-8.5Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  ),
  inbox: (
    <svg viewBox="0 0 24 24" fill="none" className="size-4.5" aria-hidden>
      <path
        d="M4 13h4l1.5 3h5L16 13h4M4 13l2-7h12l2 7v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-5Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  ),
  list: (
    <svg viewBox="0 0 24 24" fill="none" className="size-4.5" aria-hidden>
      <path
        d="M8 7h12M8 12h12M8 17h12M4 7h.01M4 12h.01M4 17h.01"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  ),
  plus: (
    <svg viewBox="0 0 24 24" fill="none" className="size-4.5" aria-hidden>
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" className="size-4.5" aria-hidden>
      <path
        d="M7 4h10v4H7zM5 10h14v10H5z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  ),
  users: (
    <svg viewBox="0 0 24 24" fill="none" className="size-4.5" aria-hidden>
      <circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M3.5 19a5.5 5.5 0 0 1 11 0M16 6.2a3 3 0 0 1 0 5.6M17.5 19a5.4 5.4 0 0 0-2-4.2"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  ),
} as const;
