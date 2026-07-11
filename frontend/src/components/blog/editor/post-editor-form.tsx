"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";

import { BLOG_CATEGORIES } from "@/lib/blog/content";
import { absoluteMediaUrl, type BlogPostDetail } from "@/lib/blog/api";
import {
  useCreatePost,
  useDeletePost,
  useUpdatePost,
} from "@/lib/blog/queries";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CoverUploader } from "@/components/blog/editor/cover-uploader";
import {
  RichTextEditor,
  type RichTextEditorHandle,
} from "@/components/blog/editor/rich-text-editor";

/**
 * Shared write/edit surface. In "create" mode it saves a draft on first
 * publish/save; in "edit" mode it patches the existing post (author-only —
 * enforced server-side; this page assumes the caller already checked
 * ownership before rendering it).
 */
export function PostEditorForm({ existing }: { existing?: BlogPostDetail }) {
  const router = useRouter();
  const isEdit = !!existing;

  const [title, setTitle] = React.useState(existing?.title ?? "");
  const [subtitle, setSubtitle] = React.useState(existing?.subtitle ?? "");
  const [category, setCategory] = React.useState(
    existing?.category ?? BLOG_CATEGORIES[0].id,
  );
  const [tagsInput, setTagsInput] = React.useState(
    (existing?.tags ?? []).join(", "),
  );
  const [coverMediaId, setCoverMediaId] = React.useState<string | null>(
    existing?.cover_media_id ?? null,
  );
  const [coverUrl, setCoverUrl] = React.useState<string | null>(
    existing?.cover_url ? absoluteMediaUrl(existing.cover_url) : null,
  );

  const editorRef = React.useRef<RichTextEditorHandle>(null);
  const bodyHtmlRef = React.useRef(existing?.body_html ?? "");

  const create = useCreatePost();
  const update = useUpdatePost(existing?.slug);
  const remove = useDeletePost();
  const [saving, setSaving] = React.useState(false);

  function buildInput(status: "draft" | "published") {
    return {
      title: title.trim(),
      subtitle: subtitle.trim() || null,
      category,
      tags: tagsInput
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
      body_html: editorRef.current?.getHTML() ?? bodyHtmlRef.current,
      body_json: editorRef.current?.getJSON() ?? {},
      cover_media_id: coverMediaId,
      status,
    };
  }

  async function onSave(status: "draft" | "published") {
    if (!title.trim()) {
      toast.error("Give your post a title first.");
      return;
    }
    const input = buildInput(status);
    setSaving(true);
    try {
      if (isEdit && existing) {
        const updated = await update.mutateAsync({ id: existing.id, input });
        toast.success(status === "published" ? "Post published." : "Draft saved.");
        router.push(`/blog/${updated.slug}`);
      } else {
        const created = await create.mutateAsync(input);
        toast.success(status === "published" ? "Post published." : "Draft saved.");
        router.push(`/blog/${created.slug}`);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't save the post.");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete() {
    if (!existing) return;
    try {
      await remove.mutateAsync(existing.id);
      toast.success("Post deleted.");
      router.push("/blog");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't delete the post.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-[820px] px-4 py-10 md:px-8">
      <CoverUploader
        mediaId={coverMediaId}
        coverUrl={coverUrl}
        onChange={(id, url) => {
          setCoverMediaId(id);
          setCoverUrl(url);
        }}
      />

      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Post title"
        className="mt-6 h-auto border-none bg-transparent px-0 font-serif-display text-4xl italic shadow-none focus-visible:ring-0"
      />
      <Input
        value={subtitle}
        onChange={(e) => setSubtitle(e.target.value)}
        placeholder="Subtitle (optional)"
        className="mt-2 h-auto border-none bg-transparent px-0 text-lg text-muted-foreground shadow-none focus-visible:ring-0"
      />

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {BLOG_CATEGORIES.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          value={tagsInput}
          onChange={(e) => setTagsInput(e.target.value)}
          placeholder="tags, comma, separated"
          className="max-w-xs"
        />
      </div>

      <div className="mt-6">
        <RichTextEditor
          ref={editorRef}
          initialContent={
            existing?.body_json && Object.keys(existing.body_json).length
              ? existing.body_json
              : existing?.body_html
          }
        />
      </div>

      <div className="mt-8 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => onSave("draft")}
            loading={saving}
          >
            Save draft
          </Button>
          <Button onClick={() => onSave("published")} loading={saving}>
            {isEdit ? "Save & publish" : "Publish"}
          </Button>
        </div>

        {isEdit ? (
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="size-4" /> Delete
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete this post?</DialogTitle>
                <DialogDescription>
                  This can&apos;t be undone. The post, its likes and comments
                  will be permanently removed.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <Button variant="destructive" onClick={onDelete}>
                  Delete
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        ) : null}
      </div>
    </div>
  );
}
