"use client";

import type { Editor } from "@tiptap/react";
import {
  Bold,
  Italic,
  Strikethrough,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  Quote,
  Code,
  Link as LinkIcon,
  ImagePlus,
  Undo2,
  Redo2,
} from "lucide-react";

import { cn } from "@/lib/utils";

function ToolBtn({
  active,
  disabled,
  label,
  onClick,
  children,
}: {
  active?: boolean;
  disabled?: boolean;
  label: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "grid size-8 place-items-center rounded-md transition-colors disabled:opacity-30",
        active
          ? "bg-mk-lavender text-black"
          : "text-muted-foreground hover:bg-[var(--mk-surface-hover)] hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}

export function EditorToolbar({
  editor,
  onRequestImage,
  uploading,
}: {
  editor: Editor;
  onRequestImage: () => void;
  uploading: boolean;
}) {
  function setLink() {
    const prev = editor.getAttributes("link").href as string | undefined;
    const url = window.prompt("Link URL", prev ?? "https://");
    if (url === null) return;
    if (url === "") {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
      return;
    }
    editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
  }

  return (
    <div className="sticky top-0 z-10 flex flex-wrap items-center gap-0.5 rounded-t-lg border border-b-0 border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-1.5">
      <ToolBtn
        label="Heading 2"
        active={editor.isActive("heading", { level: 2 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
      >
        <Heading2 className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Heading 3"
        active={editor.isActive("heading", { level: 3 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
      >
        <Heading3 className="size-4" />
      </ToolBtn>
      <div className="mx-1 h-5 w-px bg-[var(--mk-border)]" />
      <ToolBtn
        label="Bold"
        active={editor.isActive("bold")}
        onClick={() => editor.chain().focus().toggleBold().run()}
      >
        <Bold className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Italic"
        active={editor.isActive("italic")}
        onClick={() => editor.chain().focus().toggleItalic().run()}
      >
        <Italic className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Strikethrough"
        active={editor.isActive("strike")}
        onClick={() => editor.chain().focus().toggleStrike().run()}
      >
        <Strikethrough className="size-4" />
      </ToolBtn>
      <div className="mx-1 h-5 w-px bg-[var(--mk-border)]" />
      <ToolBtn
        label="Bullet list"
        active={editor.isActive("bulletList")}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      >
        <List className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Numbered list"
        active={editor.isActive("orderedList")}
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
      >
        <ListOrdered className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Quote"
        active={editor.isActive("blockquote")}
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
      >
        <Quote className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Code block"
        active={editor.isActive("codeBlock")}
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
      >
        <Code className="size-4" />
      </ToolBtn>
      <div className="mx-1 h-5 w-px bg-[var(--mk-border)]" />
      <ToolBtn label="Link" active={editor.isActive("link")} onClick={setLink}>
        <LinkIcon className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Insert image"
        disabled={uploading}
        onClick={onRequestImage}
      >
        <ImagePlus className="size-4" />
      </ToolBtn>
      <div className="mx-1 h-5 w-px bg-[var(--mk-border)]" />
      <ToolBtn
        label="Undo"
        disabled={!editor.can().undo()}
        onClick={() => editor.chain().focus().undo().run()}
      >
        <Undo2 className="size-4" />
      </ToolBtn>
      <ToolBtn
        label="Redo"
        disabled={!editor.can().redo()}
        onClick={() => editor.chain().focus().redo().run()}
      >
        <Redo2 className="size-4" />
      </ToolBtn>
      {uploading ? (
        <span className="ml-2 text-xs text-muted-foreground">Uploading…</span>
      ) : null}
    </div>
  );
}
