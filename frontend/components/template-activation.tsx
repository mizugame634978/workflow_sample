"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { call } from "@/lib/client";

export function TemplateActivation({
  templateId,
  isActive,
}: {
  templateId: number;
  isActive: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function toggle() {
    setPending(true);
    await call(`templates/${templateId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !isActive }),
    }).catch(() => undefined);
    setPending(false);
    router.refresh();
  }

  return (
    <Button
      variant={isActive ? "secondary" : "primary"}
      data-testid="toggle-activation"
      disabled={pending}
      onClick={() => void toggle()}
    >
      {isActive ? "このフォームを停止する" : "このフォームを再開する"}
    </Button>
  );
}
