"use client";

import * as React from "react";
import { Flag } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { createReport, type ReportReason, type ReportTargetType } from "@/lib/reports";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const REASONS: { value: ReportReason; label: string }[] = [
  { value: "spam", label: "Spam" },
  { value: "abuse", label: "Abuse or harassment" },
  { value: "inappropriate", label: "Inappropriate content" },
  { value: "copyright", label: "Copyright infringement" },
  { value: "other", label: "Other" },
];

/** A small "Report" trigger + dialog, reusable for any reportable content
 * (blog posts/comments, marketplace listings/comments). Hidden entirely
 * for signed-out visitors — reporting requires an account. */
export function ReportButton({
  targetType,
  targetId,
  className,
  label = "Report",
}: {
  targetType: ReportTargetType;
  targetId: string;
  className?: string;
  label?: string;
}) {
  const { status } = useAuth();
  const [open, setOpen] = React.useState(false);
  const [reason, setReason] = React.useState<ReportReason>("spam");
  const [note, setNote] = React.useState("");

  const submit = useMutation({
    mutationFn: () =>
      createReport({
        target_type: targetType,
        target_id: targetId,
        reason,
        note: note.trim() || undefined,
      }),
    onSuccess: () => {
      toast.success("Thanks — we'll take a look.");
      setOpen(false);
      setNote("");
      setReason("spam");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Couldn't submit the report.");
    },
  });

  if (status !== "authenticated") return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={label || "Report"}
        className={
          className ??
          "inline-flex items-center gap-1.5 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
        }
      >
        <Flag className="size-3.5" />
        {label ? <span>{label}</span> : null}
      </button>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Report this content</DialogTitle>
          <DialogDescription>
            Let moderators know what&apos;s wrong — they&apos;ll review it.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <Select value={reason} onValueChange={(v) => setReason(v as ReportReason)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {REASONS.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Textarea
            placeholder="Optional details…"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="min-h-20"
          />
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button onClick={() => submit.mutate()} loading={submit.isPending}>
            Submit report
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
