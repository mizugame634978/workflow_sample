"use client";

import { useEffect, useRef, useState } from "react";

import { logout } from "@/lib/client";
import { initial } from "@/lib/format";
import { ROLE_LABEL } from "@/lib/status";
import type { Profile } from "@/lib/types";

export function UserMenu({ profile }: { profile: Profile }) {
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(event: MouseEvent) {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <div className="relative" ref={container}>
      <button
        type="button"
        data-testid="user-menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="flex items-center gap-2 rounded-lg py-1 pr-2 pl-1 hover:bg-slate-100"
      >
        <span className="grid size-8 place-items-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
          {initial(profile.name)}
        </span>
        <span className="hidden text-left sm:block">
          <span className="block text-sm leading-tight font-medium text-slate-800">
            {profile.name}
          </span>
          <span className="block text-[11px] leading-tight text-slate-500">
            {profile.department}
          </span>
        </span>
      </button>

      {open ? (
        <div className="absolute right-0 z-40 mt-2 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          <div className="border-b border-slate-100 px-4 py-3">
            <p className="text-sm font-semibold text-slate-900">{profile.name}</p>
            <p className="mt-0.5 text-xs text-slate-500">{profile.email}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600">
                {profile.job_title || profile.department}
              </span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600">
                {ROLE_LABEL[profile.role]}
              </span>
            </div>
            {profile.manager ? (
              <p className="mt-2 text-[11px] text-slate-500">上長: {profile.manager.name}</p>
            ) : null}
          </div>
          <button
            type="button"
            data-testid="logout"
            onClick={() => void logout()}
            className="block w-full px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50"
          >
            ログアウト
          </button>
        </div>
      ) : null}
    </div>
  );
}
