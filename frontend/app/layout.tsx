import type { Metadata, Viewport } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Nagare Workflow — 社内申請・承認プラットフォーム",
    template: "%s | Nagare Workflow",
  },
  description:
    "申請フォームと承認ルートを一元管理し、稟議・経費精算・休暇申請をペーパーレスで処理する社内ワークフロー SaaS。",
};

export const viewport: Viewport = {
  themeColor: "#1e293b",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
