/** Shared generation option catalogs. Mirrors backend generator params. */

import type { VideoModelSpec } from "@/lib/api/generation";

/** Static fallback used for the initial default model id and before the live
 * catalog (`GET /generation/models`) has loaded. The authoritative, full list
 * with capabilities comes from the backend. */
export const VIDEO_MODELS = [
  { value: "ltx-video", label: "LTX-Video (fast, default)" },
  { value: "cogvideox-5b", label: "CogVideoX-5B (higher quality)" },
  { value: "wan-2.1", label: "Wan 2.1" },
] as const;

/** The model selected before the user picks one (must exist in the catalog). */
export const DEFAULT_VIDEO_MODEL_ID = "ltx-video";

/**
 * Aspect ratio picker — the primary way users choose output shape (mirrors
 * the Auto/16:9/9:16/… pattern used by leading AI video platforms).
 * `ratio` is undefined for "auto" (let the generator pick its own default).
 */
export interface AspectRatio {
  id: string;
  label: string;
  /** width / height, e.g. 16/9. Omitted for "auto". */
  ratio?: number;
}

export const ASPECT_RATIOS: AspectRatio[] = [
  { id: "auto", label: "Auto" },
  { id: "16:9", label: "16:9", ratio: 16 / 9 },
  { id: "9:16", label: "9:16", ratio: 9 / 16 },
  { id: "4:3", label: "4:3", ratio: 4 / 3 },
  { id: "3:4", label: "3:4", ratio: 3 / 4 },
  { id: "1:1", label: "1:1", ratio: 1 },
  { id: "21:9", label: "21:9", ratio: 21 / 9 },
];

export const DEFAULT_ASPECT_RATIO = "16:9";

/** Long side (px) used to derive concrete dimensions from an aspect ratio.
 * Kept modest for the CPU/mock backend; real CUDA models may clamp further
 * to their own supported sizes once Phase 9 is active. */
const ASPECT_BASE_SIZE = 768;

/** Round to the nearest multiple of 8 — required by most diffusion models. */
function roundTo8(n: number): number {
  return Math.max(8, Math.round(n / 8) * 8);
}

/**
 * Derive concrete width/height for an aspect ratio id. Returns null for
 * "auto" (or an unknown id) so callers omit width/height and let the
 * generator use its own default.
 */
export function resolutionForAspect(
  aspectId: string,
): { width: number; height: number } | null {
  const aspect = ASPECT_RATIOS.find((a) => a.id === aspectId);
  if (!aspect?.ratio) return null;
  if (aspect.ratio >= 1) {
    return {
      width: roundTo8(ASPECT_BASE_SIZE),
      height: roundTo8(ASPECT_BASE_SIZE / aspect.ratio),
    };
  }
  return {
    width: roundTo8(ASPECT_BASE_SIZE * aspect.ratio),
    height: roundTo8(ASPECT_BASE_SIZE),
  };
}

/** Back-compat: map an old stored "WxH" resolution string to the closest
 * aspect ratio id, so existing saved preferences keep working. */
export function aspectFromLegacyResolution(resolution: string | undefined): string {
  if (!resolution) return DEFAULT_ASPECT_RATIO;
  const [w, h] = resolution.split("x").map(Number);
  if (!w || !h) return DEFAULT_ASPECT_RATIO;
  const target = w / h;
  let best = ASPECT_RATIOS[0];
  let bestDiff = Infinity;
  for (const a of ASPECT_RATIOS) {
    if (!a.ratio) continue;
    const diff = Math.abs(a.ratio - target);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = a;
    }
  }
  return best.id;
}

export const DURATIONS = [
  { value: "2", label: "2 seconds" },
  { value: "4", label: "4 seconds" },
  { value: "6", label: "6 seconds" },
] as const;

/** The discrete duration ladder offered across models; each model exposes the
 * subset that falls within its own [min, max] envelope (plus its endpoints). */
const DURATION_LADDER = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30];

/**
 * Duration options for a model, constrained to its capability envelope. Falls
 * back to the static `DURATIONS` when the model spec isn't known yet.
 */
export function durationOptionsFor(
  spec: VideoModelSpec | undefined,
): { value: string; label: string }[] {
  if (!spec) return DURATIONS.map((d) => ({ value: d.value, label: d.label }));
  const secs = new Set<number>([spec.min_duration, spec.max_duration]);
  for (const s of DURATION_LADDER) {
    if (s >= spec.min_duration && s <= spec.max_duration) secs.add(s);
  }
  return [...secs]
    .sort((a, b) => a - b)
    .map((s) => ({ value: String(s), label: `${s}s` }));
}

/**
 * Return a duration that's valid for the model: keep the current value if it's
 * within range, otherwise snap to the model's default. Used to re-validate the
 * selected duration whenever the model changes.
 */
export function clampDurationToModel(
  current: string,
  spec: VideoModelSpec | undefined,
): string {
  if (!spec) return current;
  const n = Number(current);
  if (Number.isFinite(n) && n >= spec.min_duration && n <= spec.max_duration) {
    return current;
  }
  return String(spec.default_duration);
}

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
  default_aspect: string;
  default_duration: string;
}

export const DEFAULT_GENERATION: GenerationDefaults = {
  default_model: "ltx-video",
  default_aspect: DEFAULT_ASPECT_RATIO,
  default_duration: "4",
};
