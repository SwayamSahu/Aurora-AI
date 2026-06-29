import { apiFetch } from "@/lib/api/client";

export interface VoiceOption {
  value: string;
  label: string;
}

export interface VoicesResponse {
  engine: string;
  voices: VoiceOption[];
}

export function listVoices() {
  return apiFetch<VoicesResponse>("/audio/voices");
}
