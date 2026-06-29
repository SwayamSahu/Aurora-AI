import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  type AssetKind,
  deleteAsset,
  listAssets,
  renameAsset,
  uploadAsset,
} from "@/lib/api/assets";
import { projectKeys } from "@/lib/query/projects";

export const assetKeys = {
  list: (projectId: string, kind?: AssetKind) =>
    ["assets", projectId, kind ?? "all"] as const,
};

export function useAssets(projectId: string, kind?: AssetKind) {
  return useQuery({
    queryKey: assetKeys.list(projectId, kind),
    queryFn: () => listAssets(projectId, kind),
  });
}

export function useUploadAsset(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadAsset(projectId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets", projectId] });
      qc.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
      qc.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}

export function useRenameAsset(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; name: string }) =>
      renameAsset(vars.id, vars.name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assets", projectId] }),
  });
}

export function useDeleteAsset(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteAsset,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets", projectId] });
      qc.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
      qc.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}
