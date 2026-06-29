import { useQuery } from "@tanstack/react-query";

import { type VoiceOption, listVoices } from "@/lib/api/audio";

/** Static fallback voices if the server call fails or the user is logged out. */
const FALLBACK_VOICES: VoiceOption[] = [
  { value: "default", label: "Default" },
];

export function useVoices() {
  const query = useQuery({
    queryKey: ["audio", "voices"],
    queryFn: listVoices,
    staleTime: 5 * 60 * 1000, // voices don't change at runtime — cache 5 min
    retry: false,              // don't hammer the server if the endpoint is down
  });

  return {
    engine: query.data?.engine ?? "auto",
    voices: query.data?.voices ?? FALLBACK_VOICES,
    isLoading: query.isLoading,
  };
}
