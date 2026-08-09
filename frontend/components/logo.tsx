import { cn } from "@/lib/cn";

export function Logo({ tone = "dark" }: { tone?: "dark" | "light" }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="grid size-9 place-items-center rounded-lg bg-brand-600 text-white shadow-sm">
        <svg viewBox="0 0 24 24" fill="none" className="size-5" aria-hidden>
          <path
            d="M4 6h9M4 12h16M11 18h9"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <circle cx="18.5" cy="6" r="2.2" stroke="currentColor" strokeWidth="2" />
          <circle cx="6.5" cy="18" r="2.2" stroke="currentColor" strokeWidth="2" />
        </svg>
      </span>
      <span className="leading-tight">
        <span
          className={cn(
            "block text-[15px] font-bold tracking-tight",
            tone === "dark" ? "text-slate-900" : "text-white",
          )}
        >
          Nagare Workflow
        </span>
        <span
          className={cn(
            "block text-[10px] whitespace-nowrap",
            tone === "dark" ? "text-slate-500" : "text-slate-400",
          )}
        >
          社内申請・承認プラットフォーム
        </span>
      </span>
    </div>
  );
}
