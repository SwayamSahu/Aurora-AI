import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  type Project,
  type ProjectSort,
  createProject,
  deleteProject,
  duplicateProject,
  getProject,
  listProjects,
  updateProject,
} from "@/lib/api/projects";

export const projectKeys = {
  all: ["projects"] as const,
  list: (search: string, sort: ProjectSort) =>
    ["projects", "list", { search, sort }] as const,
  detail: (id: string) => ["projects", "detail", id] as const,
};

export function useProjects(search: string, sort: ProjectSort) {
  return useQuery({
    queryKey: projectKeys.list(search, sort),
    queryFn: () => listProjects({ search: search || undefined, sort }),
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => getProject(id),
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => qc.invalidateQueries({ queryKey: projectKeys.all }),
  });
}

export function useUpdateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; name?: string; description?: string }) =>
      updateProject(vars.id, { name: vars.name, description: vars.description }),
    onSuccess: (p: Project) => {
      qc.invalidateQueries({ queryKey: projectKeys.all });
      qc.invalidateQueries({ queryKey: projectKeys.detail(p.id) });
    },
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => qc.invalidateQueries({ queryKey: projectKeys.all }),
  });
}

export function useDuplicateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: duplicateProject,
    onSuccess: () => qc.invalidateQueries({ queryKey: projectKeys.all }),
  });
}
