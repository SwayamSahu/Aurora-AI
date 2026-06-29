"use client";

import * as React from "react";
import { Mic, Captions, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { type Asset, assetContentUrl } from "@/lib/api/assets";
import { useAssets } from "@/lib/query/assets";
import { useCreateJob } from "@/lib/query/jobs";
import { useVoices } from "@/lib/query/audio";
import { useEditorStore } from "@/lib/editor/store";
import { parseSrt } from "@/lib/editor/srt";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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

const TERMINAL = ["succeeded", "failed", "cancelled"];

export function AiPanel({ projectId }: { projectId: string }) {
  const [voiceOpen, setVoiceOpen] = React.useState(false);
  const [captionOpen, setCaptionOpen] = React.useState(false);

  return (
    <div className="space-y-2">
      <p className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        AI tools
      </p>
      <Button
        variant="outline"
        className="w-full justify-start"
        onClick={() => setVoiceOpen(true)}
      >
        <Mic className="size-4" /> Add voiceover
      </Button>
      <Button
        variant="outline"
        className="w-full justify-start"
        onClick={() => setCaptionOpen(true)}
      >
        <Captions className="size-4" /> Auto-subtitles
      </Button>

      <VoiceoverDialog
        projectId={projectId}
        open={voiceOpen}
        onOpenChange={setVoiceOpen}
      />
      <SubtitlesDialog
        projectId={projectId}
        open={captionOpen}
        onOpenChange={setCaptionOpen}
      />
    </div>
  );
}

function VoiceoverDialog({
  projectId,
  open,
  onOpenChange,
}: {
  projectId: string;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  const [text, setText] = React.useState("");
  const [voice, setVoice] = React.useState("default");
  const create = useCreateJob(projectId);
  const addClipFromAsset = useEditorStore((s) => s.addClipFromAsset);
  const { voices, engine } = useVoices();

  async function run() {
    if (!text.trim()) {
      toast.error("Enter some text to narrate.");
      return;
    }
    try {
      const job = await create.mutateAsync({
        type: "tts",
        params: { text, voice },
      });
      if (job.status === "succeeded" && job.result_asset) {
        addClipFromAsset({
          assetId: job.result_asset.id,
          kind: "audio",
          duration: job.result_asset.duration_seconds ?? 3,
        });
        toast.success("Voiceover added to the timeline.");
        onOpenChange(false);
        setText("");
      } else if (!TERMINAL.includes(job.status)) {
        toast.success("Generating voiceover — it'll appear in Media when ready.");
        onOpenChange(false);
      } else {
        toast.error("Voiceover failed.");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not generate.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add voiceover</DialogTitle>
          <DialogDescription>
            Type a script and Aurora narrates it using{" "}
            <span className="font-medium capitalize">{engine}</span>. The clip
            is added to the audio track.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label htmlFor="vo-text">Script</Label>
            <Textarea
              id="vo-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Welcome to Aurora, the open-source AI video studio…"
              className="min-h-28"
            />
          </div>
          <div className="space-y-1.5">
            <Label>Voice</Label>
            <Select value={voice} onValueChange={setVoice}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {voices.map((v) => (
                  <SelectItem key={v.value} value={v.value}>
                    {v.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={run} loading={create.isPending}>
            <Mic className="size-4" /> Generate voiceover
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function SubtitlesDialog({
  projectId,
  open,
  onOpenChange,
}: {
  projectId: string;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  const { data: assets } = useAssets(projectId);
  const create = useCreateJob(projectId);
  const addCaptionClips = useEditorStore((s) => s.addCaptionClips);
  const [sourceId, setSourceId] = React.useState<string>("");

  const sources: Asset[] = (assets ?? []).filter(
    (a) => a.kind === "video" || a.kind === "audio",
  );

  React.useEffect(() => {
    if (open && !sourceId && sources.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSourceId(sources[0].id);
    }
  }, [open, sourceId, sources]);

  async function run() {
    if (!sourceId) {
      toast.error("Choose a source clip to transcribe.");
      return;
    }
    try {
      const job = await create.mutateAsync({
        type: "transcribe",
        params: { asset_id: sourceId },
      });
      if (job.status === "succeeded" && job.result_asset) {
        const res = await fetch(assetContentUrl(job.result_asset));
        const srt = await res.text();
        const captions = parseSrt(srt);
        addCaptionClips(captions);
        toast.success(`Added ${captions.length} captions to the text track.`);
        onOpenChange(false);
      } else if (!TERMINAL.includes(job.status)) {
        toast.success("Transcribing — captions will be available shortly.");
        onOpenChange(false);
      } else {
        toast.error("Transcription failed.");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not transcribe.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Auto-subtitles</DialogTitle>
          <DialogDescription>
            Transcribe a clip with Whisper and add timed captions to the text
            track.
          </DialogDescription>
        </DialogHeader>
        <div className="py-2">
          {sources.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Add a video or audio clip to the project first.
            </p>
          ) : (
            <div className="space-y-1.5">
              <Label>Source clip</Label>
              <Select value={sourceId} onValueChange={setSourceId}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a clip" />
                </SelectTrigger>
                <SelectContent>
                  {sources.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={run}
            loading={create.isPending}
            disabled={sources.length === 0}
          >
            {create.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Captions className="size-4" />
            )}
            Generate captions
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
