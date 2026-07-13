import { useQuery } from "@tanstack/react-query";

import { listVideoModels } from "@/lib/api/generation";

export const generationKeys = {
  models: ["generation", "models"] as const,
};

/** The video-model catalog. It rarely changes within a session, so cache it
 * aggressively and don't refetch on focus. */
export function useVideoModels() {
  return useQuery({
    queryKey: generationKeys.models,
    queryFn: listVideoModels,
    staleTime: 60 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}
