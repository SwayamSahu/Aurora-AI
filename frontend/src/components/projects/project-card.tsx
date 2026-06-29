"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Film, MoreVertical, Pencil, Copy, Trash2 } from "lucide-react";
import { toast } from "sonner";

import type { Project } from "@/lib/api/projects";
import { useDeleteProject, useDuplicateProject } from "@/lib/query/projects";
import { timeAgo } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { ProjectFormDialog } from "@/components/projects/project-form-dialog";

export function ProjectCard({ project }: { project: Project }) {
  const router = useRouter();
  const [editing, setEditing] = React.useState(false);
  const [confirmingDelete, setConfirmingDelete] = React.useState(false);
  const del = useDeleteProject();
  const duplicate = useDuplicateProject();

  async function handleDuplicate() {
    try {
      const copy = await duplicate.mutateAsync(project.id);
      toast.success("Project duplicated.");
      router.push(`/projects/${copy.id}`);
    } catch {
      toast.error("Could not duplicate project.");
    }
  }

  async function handleDelete() {
    try {
      await del.mutateAsync(project.id);
      toast.success("Project deleted.");
      setConfirmingDelete(false);
    } catch {
      toast.error("Could not delete project.");
    }
  }

  return (
    <>
      <Card className="group relative overflow-hidden transition-colors hover:border-primary/40">
        <Link
          href={`/projects/${project.id}`}
          className="block focus:outline-none"
        >
          <div className="flex aspect-video items-center justify-center bg-gradient-to-br from-accent/40 to-muted">
            <Film className="size-8 text-muted-foreground/60" />
          </div>
          <div className="p-4">
            <h3 className="truncate font-medium">{project.name}</h3>
            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              <span>Updated {timeAgo(project.updated_at)}</span>
              <span aria-hidden>·</span>
              <Badge variant="secondary" className="px-1.5 py-0">
                {project.asset_count ?? 0} assets
              </Badge>
            </div>
          </div>
        </Link>

        <div className="absolute right-2 top-2 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                size="icon"
                variant="secondary"
                className="size-8 shadow-sm"
                aria-label="Project actions"
              >
                <MoreVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setEditing(true)}>
                <Pencil /> Rename
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleDuplicate}>
                <Copy /> Duplicate
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => setConfirmingDelete(true)}
              >
                <Trash2 /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </Card>

      <ProjectFormDialog
        open={editing}
        onOpenChange={setEditing}
        project={project}
      />
      <ConfirmDialog
        open={confirmingDelete}
        onOpenChange={setConfirmingDelete}
        title="Delete project?"
        description={`"${project.name}" and all its assets will be permanently removed. This cannot be undone.`}
        confirmLabel="Delete"
        destructive
        loading={del.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}
