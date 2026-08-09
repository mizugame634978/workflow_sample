import Link from "next/link";

import { cn } from "@/lib/cn";

export function Pagination({
  page,
  pages,
  total,
  perPage,
  buildHref,
}: {
  page: number;
  pages: number;
  total: number;
  perPage: number;
  buildHref: (page: number) => string;
}) {
  const from = total === 0 ? 0 : (page - 1) * perPage + 1;
  const to = Math.min(page * perPage, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-5 py-3">
      <p className="text-xs text-slate-500">
        全 {total.toLocaleString("ja-JP")} 件中 {from}–{to} 件を表示
      </p>
      <div className="flex items-center gap-1">
        <PageLink href={buildHref(page - 1)} disabled={page <= 1}>
          前へ
        </PageLink>
        <span className="px-2 text-xs text-slate-500 tabular-nums">
          {page} / {Math.max(pages, 1)}
        </span>
        <PageLink href={buildHref(page + 1)} disabled={page >= pages}>
          次へ
        </PageLink>
      </div>
    </div>
  );
}

function PageLink({
  href,
  disabled,
  children,
}: {
  href: string;
  disabled: boolean;
  children: React.ReactNode;
}) {
  const className = cn(
    "rounded-lg px-2.5 py-1.5 text-xs font-medium ring-1 ring-inset",
    disabled
      ? "pointer-events-none text-slate-300 ring-slate-100"
      : "text-slate-700 ring-slate-300 hover:bg-slate-50",
  );
  if (disabled) {
    return (
      <span className={className} aria-disabled>
        {children}
      </span>
    );
  }
  return (
    <Link href={href} className={className}>
      {children}
    </Link>
  );
}
