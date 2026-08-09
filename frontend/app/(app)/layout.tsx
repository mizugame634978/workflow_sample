import { redirect } from "next/navigation";

import { AppNav } from "@/components/app-nav";
import { Logo } from "@/components/logo";
import { NotificationBell } from "@/components/notification-bell";
import { UserMenu } from "@/components/user-menu";
import { ApiRequestError, apiFetch } from "@/lib/api";
import type { Profile } from "@/lib/types";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let profile: Profile;
  try {
    profile = await apiFetch<Profile>("/api/v1/auth/me");
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) redirect("/login");
    throw error;
  }

  return (
    <div className="min-h-dvh lg:flex">
      <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="px-5 py-4">
          <Logo />
        </div>
        <AppNav isAdmin={profile.role === "admin"} />
        <div className="mt-auto border-t border-slate-100 p-4">
          <p className="text-xs font-medium text-slate-500">{profile.organization.name}</p>
          <p className="mt-0.5 text-[11px] text-slate-400">Nagare Workflow v1.0</p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur">
          <div className="flex h-14 items-center gap-3 px-4 sm:px-6">
            <div className="lg:hidden">
              <Logo />
            </div>
            <div className="ml-auto flex items-center gap-1.5">
              <NotificationBell />
              <UserMenu profile={profile} />
            </div>
          </div>
          <div className="border-t border-slate-100 lg:hidden">
            <AppNav isAdmin={profile.role === "admin"} variant="horizontal" />
          </div>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
