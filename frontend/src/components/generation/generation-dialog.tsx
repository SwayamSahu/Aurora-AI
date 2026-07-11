"use client";

import * as React from "react";
import { toast } from "sonner";
import { Sparkles, Wand2, Image as ImageIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Job, JobType } from "@/lib/api/jobs";
import { useCreateJob } from "@/lib/query/jobs";
import { useJobProgress } from "@/lib/ws/use-job-progress";
import { useProjects } from "@/lib/query/projects";
import {
  ASPECT_RATIOS,
  DEFAULT_ASPECT_RATIO,
  DURATIONS,
  resolutionForAspect,
  VIDEO_MODELS,
} from "@/lib/generation-options";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Fixed project. If omitted, the dialog shows a project picker. */
  projectId?: string;
  onJobCreated?: (job: Job) => void;
}

const TYPES: { value: Extract<JobType, "generate_video" | "generate_image">; label: string; icon: typeof Wand2 }[] = [
  { value: "generate_video", label: "Text → Video", icon: Wand2 },
  { value: "generate_image", label: "Text → Image", icon: ImageIcon },
];

export function GenerationDialog({
  open,
  onOpenChange,
  projectId,
  onJobCreated,
}: Props) {
  const projectsQuery = useProjects("", "recent");
  const [selectedProject, setSelectedProject] = React.useState(projectId ?? "");
  const targetProject = projectId ?? selectedProject;

  const [type, setType] = React.useState<(typeof TYPES)[number]["value"]>(
    "generate_video",
  );
  const [prompt, setPrompt] = React.useState("");
  const [model, setModel] = React.useState<string>(VIDEO_MODELS[0].value);
  const [aspect, setAspect] = React.useState(DEFAULT_ASPECT_RATIO);
  const [duration, setDuration] = React.useState("4");

  const [activeJobId, setActiveJobId] = React.useState<string | null>(null);
  const create = useCreateJob(targetProject || "_");

  const progress = useJobProgress(activeJobId, (event) => {
    if (event.status === "succeeded") toast.success("Generation complete!");
    else if (event.status === "failed") toast.error("Generation failed.");
    onJobCreated?.({ id: event.id } as Job);
    setActiveJobId(null);
    onOpenChange(false);
    reset();
  });

  function reset() {
    setPrompt("");
    setActiveJobId(null);
  }

  async function handleGenerate() {
    if (!targetProject) {
      toast.error("Choose a project first.");
      return;
    }
    if (!prompt.trim()) {
      toast.error("Enter a prompt.");
      return;
    }
    const size = resolutionForAspect(aspect);
    const params =
      type === "generate_video"
        ? {
            prompt,
            model,
            width: size?.width,
            height: size?.height,
            duration_seconds: Number(duration),
          }
        : { prompt, width: size?.width, height: size?.height };
    try {
      const job = await create.mutateAsync({ type, params });
      if (["succeeded", "failed", "cancelled"].includes(job.status)) {
        // Eager backend: already done.
        if (job.status === "succeeded") toast.success("Generation complete!");
        else toast.error("Generation failed.");
        onJobCreated?.(job);
        onOpenChange(false);
        reset();
      } else {
        setActiveJobId(job.id); // stream progress over WS
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not start generation.");
    }
  }

  const generating = create.isPending || activeJobId !== null;
  const pct = Math.round((progress?.progress ?? (create.isPending ? 0.05 : 0)) * 100);

  return (
    <Dialog open={open} onOpenChange={(o) => !generating && onOpenChange(o)}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="size-5 text-primary" /> New generation
          </DialogTitle>
          <DialogDescription>
            Describe what you want. A short clip is generated and added to your
            project library.
          </DialogDescription>
        </DialogHeader>

        {generating ? (
          <div className="space-y-3 py-6">
            <p className="text-sm font-medium">Generating…</p>
            <Progress value={pct} />
            <p className="text-xs text-muted-foreground">{pct}%</p>
          </div>
        ) : (
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-2">
              {TYPES.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setType(t.value)}
                  className={cn(
                    "flex items-center gap-2 rounded-lg border p-3 text-sm transition-colors",
                    type === t.value
                      ? "border-primary bg-accent/40"
                      : "border-border hover:bg-accent/30",
                  )}
                >
                  <t.icon className="size-4" />
                  {t.label}
                </button>
              ))}
            </div>

            {!projectId ? (
              <div className="space-y-1.5">
                <Label>Project</Label>
                <Select value={selectedProject} onValueChange={setSelectedProject}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a project" />
                  </SelectTrigger>
                  <SelectContent>
                    {(projectsQuery.data ?? []).map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}

            <div className="space-y-1.5">
              <Label htmlFor="gen-prompt">Prompt</Label>
              <Textarea
                id="gen-prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="A cinematic drone shot over a misty forest at dawn…"
                className="min-h-24"
              />
            </div>

            {type === "generate_video" ? (
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1.5">
                  <Label>Model</Label>
                  <Select value={model} onValueChange={setModel}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VIDEO_MODELS.map((m) => (
                        <SelectItem key={m.value} value={m.value}>
                          {m.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Aspect ratio</Label>
                  <Select value={aspect} onValueChange={setAspect}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ASPECT_RATIOS.map((a) => (
                        <SelectItem key={a.id} value={a.id}>
                          {a.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Duration</Label>
                  <Select value={duration} onValueChange={setDuration}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DURATIONS.map((d) => (
                        <SelectItem key={d.value} value={d.value}>
                          {d.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {!generating ? (
          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleGenerate} loading={create.isPending}>
              <Sparkles className="size-4" /> Generate
            </Button>
          </DialogFooter>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
