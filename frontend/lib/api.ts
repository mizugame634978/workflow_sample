import "server-only";

import { cookies } from "next/headers";

import type { ApiError } from "@/lib/types";

export const API_BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
export const SESSION_COOKIE = "wf_session";

export class ApiRequestError extends Error {
  constructor(
    readonly status: number,
    readonly payload: ApiError,
  ) {
    super(payload.message);
    this.name = "ApiRequestError";
  }
}

/** Server-side call to the workflow API, authenticated with the session cookie. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (response.status === 204) return undefined as T;

  const body = await response.json().catch(() => ({ message: "サーバーに接続できませんでした" }));
  if (!response.ok) {
    throw new ApiRequestError(response.status, {
      message: body.message ?? "エラーが発生しました",
      errors: body.errors ?? {},
    });
  }
  return body as T;
}

/** Returns `null` instead of throwing for the given status codes. */
export async function apiFetchOrNull<T>(
  path: string,
  statuses: number[] = [403, 404],
): Promise<T | null> {
  try {
    return await apiFetch<T>(path);
  } catch (error) {
    if (error instanceof ApiRequestError && statuses.includes(error.status)) return null;
    throw error;
  }
}
