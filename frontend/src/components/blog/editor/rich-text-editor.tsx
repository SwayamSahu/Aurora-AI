"use client";

import * as React from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import ImageExt from "@tiptap/extension-image";
import LinkExt from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import { toast } from "sonner";

import { uploadBlogMedia, absoluteMediaUrl } from "@/lib/blog/api";
import { EditorToolbar } from "@/components/blog/editor/editor-toolbar";

export interface RichTextEditorHandle {
  getHTML: () => string;
  getJSON: () => Record<string, unknown>;
}

/**
 * The blog writing surface: TipTap rich text with a formatting toolbar,
 * image upload (toolbar button, paste, and drag-drop), and links. Emits
 * the current HTML on every change via `onChange` (debounced by the caller
 * for autosave).
 */
export const RichTextEditor = React.forwardRef<
  RichTextEditorHandle,
  {
    initialContent?: Record<string, unknown> | string;
    onChange?: (html: string) => void;
  }
>(function RichTextEditor({ initialContent, onChange }, ref) {
  const [uploading, setUploading] = React.useState(false);

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({ heading: { levels: [2, 3] } }),
      ImageExt.configure({ HTMLAttributes: { class: "rounded-xl" } }),
      LinkExt.configure({ openOnClick: false, autolink: true }),
      Placeholder.configure({
        placeholder: "Tell your story… (select text for formatting, or type “/” )",
      }),
    ],
    content: initialContent && Object.keys(initialContent).length ? initialContent : "",
    editorProps: {
      attributes: {
        class: "blog-prose min-h-[400px] px-4 py-4 focus:outline-none",
      },
    },
    onUpdate: ({ editor: ed }) => onChange?.(ed.getHTML()),
  });

  React.useImperativeHandle(ref, () => ({
    getHTML: () => editor?.getHTML() ?? "",
    getJSON: () => (editor?.getJSON() as Record<string, unknown>) ?? {},
  }));

  const insertImage = React.useCallback(
    async (file: File) => {
      if (!editor) return;
      setUploading(true);
      try {
        const media = await uploadBlogMedia(file);
        editor.chain().focus().setImage({ src: absoluteMediaUrl(media.url) }).run();
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Image upload failed.");
      } finally {
        setUploading(false);
      }
    },
    [editor],
  );

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Paste / drag-drop image support.
  React.useEffect(() => {
    if (!editor) return;
    const dom = editor.view.dom;

    function onPaste(e: ClipboardEvent) {
      const file = Array.from(e.clipboardData?.files ?? []).find((f) =>
        f.type.startsWith("image/"),
      );
      if (file) {
        e.preventDefault();
        void insertImage(file);
      }
    }
    function onDrop(e: DragEvent) {
      const file = Array.from(e.dataTransfer?.files ?? []).find((f) =>
        f.type.startsWith("image/"),
      );
      if (file) {
        e.preventDefault();
        void insertImage(file);
      }
    }
    dom.addEventListener("paste", onPaste);
    dom.addEventListener("drop", onDrop);
    return () => {
      dom.removeEventListener("paste", onPaste);
      dom.removeEventListener("drop", onDrop);
    };
  }, [editor, insertImage]);

  if (!editor) return null;

  return (
    <div>
      <EditorToolbar
        editor={editor}
        uploading={uploading}
        onRequestImage={() => fileInputRef.current?.click()}
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void insertImage(file);
          e.target.value = "";
        }}
      />
      <div className="rounded-b-lg border border-[var(--mk-border)] bg-[var(--mk-surface-1)]">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
});
