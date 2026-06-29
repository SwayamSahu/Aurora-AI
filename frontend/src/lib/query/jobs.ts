import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  ACTIVE_STATUSES,
  type Job,
  type JobType,
  cancelJob,
  createJob,
  listJobs,
  retryJob,
} from "@/lib/api/jobs";
import { projectKeys } from "@/lib/query/projects";

export const jobKeys = {
  all: ["jobs"] as const,
  list: (projectId?: string) => ["jobs", "list", projectId ?? "all"] as const,
};

/** Lists jobs; auto-refetches while any job is still active. */
export function useJobs(projectId?: string) {
  return useQuery({
    queryKey: jobKeys.list(projectId),
    queryFn: () => listJobs({ projectId, limit: 100 }),
    refetchInterval: (query) => {
      const data = query.state.data as Job[] | undefined;
      const active = data?.some((j) => ACTIVE_STATUSES.includes(j.status));
      return active ? 1200 : false;
    },
  });
}

function invalidateAfterJob(qc: ReturnType<typeof useQueryClient>, projectId: string) {
  qc.invalidateQueries({ queryKey: jobKeys.all });
  qc.invalidateQueries({ queryKey: ["assets", projectId] });
  qc.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
  qc.invalidateQueries({ queryKey: projectKeys.all });
}

export function useCreateJob(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { type: JobType; params: Record<string, unknown> }) =>
      createJob(projectId, vars.type, vars.params),
    onSuccess: () => invalidateAfterJob(qc, projectId),
  });
}

export function useRetryJob(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: retryJob,
    onSuccess: () => invalidateAfterJob(qc, projectId),
  });
}

export function useCancelJob(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: cancelJob,
    onSuccess: () => invalidateAfterJob(qc, projectId),
  });
}
