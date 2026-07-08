import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  type CreateEditInput,
  type EditLayer,
  createEdit,
  deleteEdit,
  listEdits,
  patchEdit,
} from "@/lib/editor/ai-edit/api";

function editsKey(projectId: string, clipId: string) {
  return ["edit-layers", projectId, clipId] as const;
}

/** List a clip's edit layers, polling while any are still processing. */
export function useEditLayers(projectId: string, clipId: string | undefined) {
  return useQuery({
    queryKey: editsKey(projectId, clipId ?? ""),
    queryFn: () => listEdits(projectId, clipId as string),
    enabled: !!clipId,
    refetchInterval: (query) => {
      const data = query.state.data as EditLayer[] | undefined;
      const pending = data?.some(
        (e) => e.status === "queued" || e.status === "running",
      );
      return pending ? 1200 : false;
    },
  });
}

export function useCreateEdit(projectId: string, clipId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateEditInput) => createEdit(projectId, input),
    onSuccess: () => {
      if (clipId)
        qc.invalidateQueries({ queryKey: editsKey(projectId, clipId) });
    },
  });
}

export function usePatchEdit(projectId: string, clipId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      patch,
    }: {
      id: string;
      patch: { enabled?: boolean; position?: number; prompt?: string };
    }) => patchEdit(id, patch),
    onSuccess: () => {
      if (clipId)
        qc.invalidateQueries({ queryKey: editsKey(projectId, clipId) });
    },
  });
}

export function useDeleteEdit(projectId: string, clipId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteEdit(id),
    onSuccess: () => {
      if (clipId)
        qc.invalidateQueries({ queryKey: editsKey(projectId, clipId) });
    },
  });
}
