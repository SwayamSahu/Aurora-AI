"use client";

import * as React from "react";
import { UploadCloud, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import { useUploadAsset } from "@/lib/query/assets";

export function AssetUploader({ projectId }: { projectId: string }) {
  const upload = useUploadAsset(projectId);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = React.useState(false);
  const [pending, setPending] = React.useState(0);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const list = Array.from(files);
    setPending((n) => n + list.length);
    for (const file of list) {
      try {
        await upload.mutateAsync(file);
      } catch (err) {
        toast.error(
          `Couldn't upload ${file.name}: ${
            err instanceof Error ? err.message : "error"
          }`,
        );
      } finally {
        setPending((n) => n - 1);
      }
    }
    toast.success(
      list.length === 1 ? "Asset uploaded." : `${list.length} assets uploaded.`,
    );
  }

  const busy = pending > 0;

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
        dragging
          ? "border-primary bg-accent/40"
          : "border-border hover:border-primary/50 hover:bg-accent/20",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="video/*,image/*,audio/*,.srt,.vtt"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className="mb-3 flex size-11 items-center justify-center rounded-full bg-accent text-accent-foreground">
        {busy ? (
          <Loader2 className="size-5 animate-spin" />
        ) : (
          <UploadCloud className="size-5" />
        )}
      </div>
      <p className="text-sm font-medium">
        {busy ? `Uploading ${pending}…` : "Drop files or click to upload"}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        Video, image, audio or subtitles · up to 200MB each
      </p>
    </div>
  );
}
