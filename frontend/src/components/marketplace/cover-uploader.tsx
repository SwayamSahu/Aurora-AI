"use client";

import * as React from "react";
import { ImagePlus, X, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { uploadListingMedia, absoluteMediaUrl } from "@/lib/marketplace/api";

export function CoverUploader({
  mediaId,
  coverUrl,
  onChange,
}: {
  mediaId: string | null;
  coverUrl: string | null;
  onChange: (mediaId: string | null, url: string | null) => void;
}) {
  const [uploading, setUploading] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setUploading(true);
    try {
      const media = await uploadListingMedia(file);
      onChange(media.id, absoluteMediaUrl(media.url));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Preview upload failed.");
    } finally {
      setUploading(false);
    }
  }

  if (mediaId && coverUrl) {
    return (
      <div className="relative overflow-hidden rounded-xl border border-[var(--mk-border)]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={coverUrl} alt="" className="h-56 w-full object-cover" />
        <button
          type="button"
          aria-label="Remove preview"
          onClick={() => onChange(null, null)}
          className="absolute right-3 top-3 grid size-8 place-items-center rounded-full bg-black/70 text-white transition-colors hover:bg-black"
        >
          <X className="size-4" />
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      disabled={uploading}
      onClick={() => inputRef.current?.click()}
      className="flex h-56 w-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-[var(--mk-border-strong)] bg-[var(--mk-surface-1)] text-muted-foreground transition-colors hover:bg-[var(--mk-surface-hover)] hover:text-foreground"
    >
      {uploading ? (
        <Loader2 className="size-6 animate-spin" />
      ) : (
        <ImagePlus className="size-6" />
      )}
      <span className="text-sm">
        {uploading ? "Uploading…" : "Add a preview image (required to publish)"}
      </span>
      <input
        ref={inputRef}
        type="file"
        accept="image/*,video/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFile(file);
          e.target.value = "";
        }}
      />
    </button>
  );
}
