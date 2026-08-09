import { NextResponse } from "next/server";

import { API_BASE, SESSION_COOKIE } from "@/lib/api";

/**
 * Exchanges credentials for a session cookie.
 *
 * The JWT is stored `httpOnly` so that no browser script — including anything
 * injected through an XSS hole — can read it.
 */
export async function POST(request: Request) {
  const credentials = await request.json();

  const upstream = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
    cache: "no-store",
  }).catch(() => null);

  if (!upstream) {
    return NextResponse.json(
      { message: "APIサーバーに接続できません。バックエンドが起動しているか確認してください。" },
      { status: 503 },
    );
  }

  const data = await upstream.json().catch(() => ({ message: "応答を解析できませんでした" }));
  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  const response = NextResponse.json({ user: data.user });
  response.cookies.set(SESSION_COOKIE, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: data.expires_in,
    secure: process.env.NODE_ENV === "production",
  });
  return response;
}
