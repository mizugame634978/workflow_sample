import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApprovalRoute } from "@/components/approval-route";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/status-badge";
import { Timeline } from "@/components/timeline";
import type { RequestStep, TimelineEntry } from "@/lib/types";

const approver = (id: number, name: string) => ({
  id,
  name,
  email: `user${id}@acme.co.jp`,
  department: "プロダクト開発部",
  job_title: "課長",
});

const steps: RequestStep[] = [
  {
    id: 1,
    order_index: 0,
    name: "上長承認",
    status: "approved",
    approver: approver(3, "鈴木 健一"),
    approver_role: null,
    comment: "問題ありません",
    acted_by: approver(3, "鈴木 健一"),
    acted_at: "2026-08-08T01:00:00Z",
  },
  {
    id: 2,
    order_index: 1,
    name: "経理承認",
    status: "pending",
    approver: null,
    approver_role: "admin",
    comment: null,
    acted_by: null,
    acted_at: null,
  },
  {
    id: 3,
    order_index: 2,
    name: "最終決裁",
    status: "waiting",
    approver: approver(1, "高橋 誠"),
    approver_role: null,
    comment: null,
    acted_by: null,
    acted_at: null,
  },
];

describe("StatusBadge", () => {
  it.each([
    ["draft", "下書き"],
    ["pending", "承認待ち"],
    ["approved", "承認済み"],
    ["rejected", "却下"],
    ["cancelled", "取り下げ"],
  ] as const)("renders %s as %s", (status, label) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("exposes the status for assistive technology and tests", () => {
    render(<StatusBadge status="pending" />);
    expect(screen.getByTestId("status-badge")).toHaveAttribute("data-status", "pending");
  });
});

describe("ApprovalRoute", () => {
  it("lists every step in order", () => {
    render(<ApprovalRoute steps={steps} currentStepIndex={1} />);
    const names = screen.getAllByTestId("route-step-name").map((node) => node.textContent);
    expect(names).toEqual(["上長承認", "経理承認", "最終決裁"]);
  });

  it("marks the step that is waiting for a decision", () => {
    render(<ApprovalRoute steps={steps} currentStepIndex={1} />);
    expect(screen.getByTestId("route-step-1")).toHaveAttribute("data-current", "true");
    expect(screen.getByTestId("route-step-0")).toHaveAttribute("data-current", "false");
  });

  it("names the approver, falling back to the role for role based steps", () => {
    render(<ApprovalRoute steps={steps} currentStepIndex={1} />);
    expect(within(screen.getByTestId("route-step-0")).getByText("鈴木 健一")).toBeInTheDocument();
    expect(within(screen.getByTestId("route-step-1")).getByText("管理者権限を持つ担当者")).toBeInTheDocument();
  });

  it("shows the comment left by an approver", () => {
    render(<ApprovalRoute steps={steps} currentStepIndex={1} />);
    expect(screen.getByText("問題ありません")).toBeInTheDocument();
  });

  it("renders nothing but a hint when the route has not started", () => {
    render(<ApprovalRoute steps={[]} currentStepIndex={0} />);
    expect(screen.getByText(/提出すると承認ルートが確定します/)).toBeInTheDocument();
  });
});

describe("Timeline", () => {
  const entries: TimelineEntry[] = [
    {
      id: 1,
      action: "created",
      actor: approver(4, "田中 美咲"),
      from_status: null,
      to_status: "draft",
      step_name: null,
      comment: null,
      created_at: "2026-08-07T00:00:00Z",
    },
    {
      id: 2,
      action: "sent_back",
      actor: approver(3, "鈴木 健一"),
      from_status: "pending",
      to_status: "draft",
      step_name: "上長承認",
      comment: "内訳を追記してください",
      created_at: "2026-08-08T00:00:00Z",
    },
  ];

  it("translates each action into Japanese", () => {
    render(<Timeline entries={entries} />);
    expect(screen.getByText("申請を作成")).toBeInTheDocument();
    expect(screen.getByText("差戻し")).toBeInTheDocument();
  });

  it("shows the actor and any comment", () => {
    render(<Timeline entries={entries} />);
    expect(screen.getByText("鈴木 健一")).toBeInTheDocument();
    expect(screen.getByText("内訳を追記してください")).toBeInTheDocument();
  });

  it("renders newest first", () => {
    render(<Timeline entries={entries} />);
    const rows = screen.getAllByTestId("timeline-entry");
    expect(rows[0]).toHaveTextContent("差戻し");
  });
});

describe("EmptyState", () => {
  it("shows the title and description", () => {
    render(<EmptyState title="申請はありません" description="新しい申請を作成しましょう" />);
    expect(screen.getByText("申請はありません")).toBeInTheDocument();
    expect(screen.getByText("新しい申請を作成しましょう")).toBeInTheDocument();
  });
});
