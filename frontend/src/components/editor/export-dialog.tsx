"use client";

import * as React from "react";
import { Download, Film, Loader2, CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";

import { startExport, type ExportOptions } from "@/lib/api/export";
import { assetContentUrl } from "@/lib/api/assets";
import { useJobProgress } from "@/lib/ws/use-job-progress";
import { useQueryClient } from "@tanstack/react-query";
import { projectKeys } from "@/lib/query/projects";
import { jobKeys } from "@/lib/query/jobs";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Job } from "@/lib/api/jobs";

type Phase = "settings" | "rendering" | "done" | "error";

const RESOLUTIONS = [
  { label: "1080p (1920×1080)", w: 1920, h: 1080 },
  { label: "720p (1280×720) — default", w: 1280, h: 720 },
  { label: "480p (854×480)", w: 854, h: 480 },
  { label: "Square 1:1 (1080×1080)", w: 1080, h: 1080 },
] as const;

const QUALITY = [
  { label: "High (CRF 18)", crf: 18 },
  { label: "Good (CRF 23) — default", crf: 23 },
  { label: "Draft (CRF 30 — smaller file)", crf: 30 },
] as const;

interface Props {
  projectId: string;
  projectName: string;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}

export function ExportDialog({
  projectId,
  projectName,
  open,
  onOpenChange,
}: Props) {
  const qc = useQueryClient();
  const [phase, setPhase] = React.useState<Phase>("settings");
  const [resolution, setResolution] = React.useState("1280x720");
  const [crf, setCrf] = React.useState(23);
  const [activeJobId, setActiveJobId] = React.useState<string | null>(null);
  const [resultJob, setResultJob] = React.useState<Job | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const progress = useJobProgress(activeJobId, (event) => {
    setActiveJobId(null);
    if (event.status === "succeeded") {
      qc.invalidateQueries({ queryKey: projectKeys.all });
      qc.invalidateQueries({ queryKey: jobKeys.all });
      setPhase("done");
    } else {
      setError(event.error ?? "Export failed.");
      setPhase("error");
      toast.error("Export failed.");
    }
  });

  const pct = Math.round((progress?.progress ?? 0) * 100);

  function reset() {
    setPhase("settings");
    setActiveJobId(null);
    setResultJob(null);
    setError(null);
  }

  async function handleExport() {
    const [w, h] = resolution.split("x").map(Number);
    const opts: ExportOptions = { width: w, height: h, crf };
    setPhase("rendering");
    setError(null);
    try {
      const job = await startExport(projectId, opts);
      if (job.status === "succeeded") {
        setResultJob(job);
        qc.invalidateQueries({ queryKey: projectKeys.all });
        qc.invalidateQueries({ queryKey: jobKeys.all });
        setPhase("done");
      } else if (job.status === "failed") {
        setError(job.error ?? "Export failed.");
        setPhase("error");
      } else {
        setActiveJobId(job.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start export.");
      setPhase("error");
      toast.error("Export failed to start.");
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Film className="size-5 text-primary" /> Export video
          </DialogTitle>
          <DialogDescription>
            Render &ldquo;{projectName}&rdquo; to an MP4 file.
          </DialogDescription>
        </DialogHeader>

        {/* ── Settings ── */}
        {phase === "settings" && (
          <>
            <div className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label>Resolution</Label>
                <Select value={resolution} onValueChange={setResolution}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RESOLUTIONS.map((r) => (
                      <SelectItem key={r.label} value={`${r.w}x${r.h}`}>
                        {r.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Quality</Label>
                <Select
                  value={String(crf)}
                  onValueChange={(v) => setCrf(Number(v))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {QUALITY.map((q) => (
                      <SelectItem key={q.crf} value={String(q.crf)}>
                        {q.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <p className="text-xs text-muted-foreground">
                Audio and captions (if any) are included automatically. The
                exported MP4 is added to the project asset library.
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button onClick={handleExport}>
                <Film className="size-4" /> Export
              </Button>
            </DialogFooter>
          </>
        )}

        {/* ── Rendering ── */}
        {phase === "rendering" && (
          <div className="space-y-4 py-6">
            <div className="flex items-center gap-3">
              <Loader2 className="size-5 animate-spin text-primary" />
              <p className="text-sm font-medium">Rendering…</p>
            </div>
            <Progress value={pct} />
            <p className="text-xs text-muted-foreground">{pct}% — this may take a moment for longer timelines.</p>
          </div>
        )}

        {/* ── Done ── */}
        {phase === "done" && (
          <>
            <div className="space-y-3 py-4">
              <div className="flex items-center gap-2 text-success">
                <CheckCircle className="size-5" />
                <p className="font-medium">Export complete!</p>
              </div>
              <p className="text-sm text-muted-foreground">
                The MP4 has been added to your project library.
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { reset(); onOpenChange(false); }}>
                Close
              </Button>
              {resultJob?.result_asset ? (
                <Button asChild>
                  <a
                    href={assetContentUrl(resultJob.result_asset)}
                    download={`${projectName}.mp4`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Download className="size-4" /> Download MP4
                  </a>
                </Button>
              ) : null}
            </DialogFooter>
          </>
        )}

        {/* ── Error ── */}
        {phase === "error" && (
          <>
            <div className="space-y-3 py-4">
              <div className="flex items-center gap-2 text-destructive">
                <XCircle className="size-5" />
                <p className="font-medium">Export failed</p>
              </div>
              {error ? (
                <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 font-mono text-xs text-destructive">
                  {error}
                </p>
              ) : null}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { reset(); onOpenChange(false); }}>
                Close
              </Button>
              <Button variant="outline" onClick={reset}>
                Try again
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
