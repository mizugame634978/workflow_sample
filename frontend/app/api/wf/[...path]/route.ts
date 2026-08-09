import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { API_BASE, SESSION_COOKIE } from "@/lib/api";

type Context = { params: Promise<{ path: string[] }> };

/**
 * Thin BFF proxy so client components can call the API without ever seeing the
 * bearer token. Only the workflow API surface is reachable through it.
 */
async function forward(request: Request, context: Context): Promise<Response> {
  const { path } = await context.params;
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ message: "セッションが切れました", errors: {} }, { status: 401 });
  }

  const search = new URL(request.url).search;
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();

  const upstream = await fetch(`${API_BASE}/api/v1/${path.join("/")}${search}`, {
    method: request.method,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: body || undefined,
    cache: "no-store",
  }).catch(() => null);

  if (!upstream) {
    return NextResponse.json(
      { message: "APIサーバーに接続できませんでした", errors: {} },
      { status: 503 },
    );
  }
  if (upstream.status === 204) return new NextResponse(null, { status: 204 });

  const payload = await upstream.text();
  return new NextResponse(payload, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const PUT = forward;
export const DELETE = forward;
