import type { Metadata } from "next";

import { PageHeader } from "@/components/page-header";
import { UserInviteForm } from "@/components/user-invite-form";
import { apiFetch } from "@/lib/api";
import { initial } from "@/lib/format";
import { ROLE_LABEL } from "@/lib/status";
import type { ItemList, User } from "@/lib/types";

export const metadata: Metadata = { title: "ユーザー管理" };

export default async function UsersPage() {
  const users = await apiFetch<ItemList<User>>("/api/v1/users");

  return (
    <>
      <PageHeader
        title="ユーザー管理"
        description="社員アカウントと上長（承認ライン）を管理します。"
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card overflow-hidden lg:col-span-2">
          <div className="card-header">
            <h2 className="card-title">社員一覧（{users.items.length}名）</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[38rem] border-collapse">
              <thead className="border-b border-slate-100 bg-slate-50/60">
                <tr>
                  <th className="th">氏名</th>
                  <th className="th">部署 / 役職</th>
                  <th className="th">上長</th>
                  <th className="th">権限</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.items.map((user) => (
                  <tr key={user.id} data-testid="user-row" className="hover:bg-slate-50/70">
                    <td className="td">
                      <span className="flex items-center gap-2.5">
                        <span className="grid size-7 place-items-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                          {initial(user.name)}
                        </span>
                        <span>
                          <span className="block font-medium text-slate-900">{user.name}</span>
                          <span className="block text-xs text-slate-400">{user.email}</span>
                        </span>
                      </span>
                    </td>
                    <td className="td">
                      {user.department}
                      <span className="mt-0.5 block text-xs text-slate-400">{user.job_title}</span>
                    </td>
                    <td className="td text-slate-600">{user.manager?.name ?? "—"}</td>
                    <td className="td">
                      <span
                        className={
                          user.role === "admin"
                            ? "inline-flex rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700 ring-1 ring-brand-100 ring-inset"
                            : "inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 ring-inset"
                        }
                      >
                        {ROLE_LABEL[user.role]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-900">ユーザーを追加</h2>
          <p className="mt-1 text-xs text-slate-500">
            上長を設定すると「申請者の上長」ステップが自動で解決されます。
          </p>
          <UserInviteForm users={users.items} />
        </div>
      </div>
    </>
  );
}
