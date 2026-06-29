"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import { ApiError } from "@/lib/api/client";
import { useCreateProject, useUpdateProject } from "@/lib/query/projects";
import type { Project } from "@/lib/api/projects";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const schema = z.object({
  name: z.string().min(1, "Enter a project name."),
  description: z.string().optional(),
});
type Values = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When set, the dialog edits this project; otherwise it creates one. */
  project?: Project;
  onCreated?: (project: Project) => void;
}

export function ProjectFormDialog({
  open,
  onOpenChange,
  project,
  onCreated,
}: Props) {
  const isEdit = !!project;
  const create = useCreateProject();
  const update = useUpdateProject();

  const form = useForm<Values>({
    resolver: zodResolver(schema),
    values: {
      name: project?.name ?? "",
      description: project?.description ?? "",
    },
  });

  async function onSubmit(values: Values) {
    try {
      if (isEdit) {
        await update.mutateAsync({ id: project!.id, ...values });
        toast.success("Project updated.");
      } else {
        const created = await create.mutateAsync(values);
        toast.success("Project created.");
        onCreated?.(created);
      }
      onOpenChange(false);
      form.reset();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>
                {isEdit ? "Edit project" : "New project"}
              </DialogTitle>
              <DialogDescription>
                {isEdit
                  ? "Update your project details."
                  : "Give your project a name to get started."}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input
                        autoFocus
                        placeholder="My awesome video"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description (optional)</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="What is this project about?"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit" loading={form.formState.isSubmitting}>
                {isEdit ? "Save changes" : "Create project"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
