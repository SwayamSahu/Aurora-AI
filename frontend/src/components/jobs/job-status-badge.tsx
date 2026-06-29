import { Loader2 } from "lucide-react";

import type { JobStatus } from "@/lib/api/jobs";
import { Badge } from "@/components/ui/badge";

const MAP: Record<
  JobStatus,
  { label: string; variant: "default" | "secondary" | "success" | "destructive" | "warning" | "outline" }
> = {
  queued: { label: "Queued", variant: "secondary" },
  running: { label: "Running", variant: "warning" },
  succeeded: { label: "Succeeded", variant: "success" },
  failed: { label: "Failed", variant: "destructive" },
  cancelled: { label: "Cancelled", variant: "outline" },
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const { label, variant } = MAP[status];
  const active = status === "running" || status === "queued";
  return (
    <Badge variant={variant}>
      {active ? <Loader2 className="size-3 animate-spin" /> : null}
      {label}
    </Badge>
  );
}
