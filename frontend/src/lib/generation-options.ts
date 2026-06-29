/** Shared generation option catalogs. Mirrors backend generator params. */

export const VIDEO_MODELS = [
  { value: "ltx-video", label: "LTX-Video (fast, default)" },
  { value: "cogvideox-5b", label: "CogVideoX-5B (higher quality)" },
  { value: "wan-2.1", label: "Wan 2.1" },
] as const;

export const RESOLUTIONS = [
  { value: "512x512", label: "512 × 512 (square)" },
  { value: "768x512", label: "768 × 512 (landscape)" },
  { value: "512x768", label: "512 × 768 (portrait)" },
  { value: "1024x576", label: "1024 × 576 (16:9)" },
] as const;

export const DURATIONS = [
  { value: "2", label: "2 seconds" },
  { value: "4", label: "4 seconds" },
  { value: "6", label: "6 seconds" },
] as const;

/**
 * Style presets append descriptive cues to the prompt (and optionally seed a
 * negative prompt). They make it easy to get a consistent look without prompt
 * engineering.
 */
export interface StylePreset {
  id: string;
  label: string;
  emoji: string;
  promptSuffix: string;
  negativePrompt?: string;
}

export const STYLE_PRESETS: StylePreset[] = [
  {
    id: "cinematic",
    label: "Cinematic",
    emoji: "🎬",
    promptSuffix:
      "cinematic film still, shallow depth of field, dramatic lighting, 35mm",
  },
  {
    id: "photoreal",
    label: "Photoreal",
    emoji: "📷",
    promptSuffix: "photorealistic, ultra detailed, natural lighting, 4k",
    negativePrompt: "cartoon, illustration, painting, low quality",
  },
  {
    id: "anime",
    label: "Anime",
    emoji: "🌸",
    promptSuffix: "anime style, vibrant colors, cel shaded, studio quality",
  },
  {
    id: "3d",
    label: "3D Render",
    emoji: "🧊",
    promptSuffix: "3d render, octane, soft global illumination, highly detailed",
  },
  {
    id: "watercolor",
    label: "Watercolor",
    emoji: "🎨",
    promptSuffix: "watercolor painting, soft washes, textured paper, artistic",
  },
  {
    id: "noir",
    label: "Noir",
    emoji: "🕶️",
    promptSuffix: "film noir, high contrast black and white, moody shadows",
  },
];

export interface GenerationDefaults {
  default_model: string;
  default_resolution: string;
  default_duration: string;
}

export const DEFAULT_GENERATION: GenerationDefaults = {
  default_model: "ltx-video",
  default_resolution: "768x512",
  default_duration: "4",
};
