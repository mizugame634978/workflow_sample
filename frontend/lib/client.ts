"use client";

import type { ApiError } from "@/lib/types";

export class ClientApiError extends Error {
  constructor(
    readonly status: number,
    readonly fieldErrors: Record<string, string>,
    message: string,
  ) {
    super(message);
    this.name = "ClientApiError";
  }
}

/** Calls the workflow API through the BFF proxy (`/api/wf/...`). */
export async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/wf/${path.replace(/^\//, "")}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });

  if (response.status === 204) return undefined as T;

  const body: Partial<ApiError> & Record<string, unknown> = await response
    .json()
    .catch(() => ({ message: "サーバーからの応答を解析できませんでした" }));

  if (!response.ok) {
    if (response.status === 401) window.location.href = "/login";
    throw new ClientApiError(
      response.status,
      (body.errors as Record<string, string>) ?? {},
      body.message ?? "エラーが発生しました",
    );
  }
  return body as T;
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.href = "/login";
}
