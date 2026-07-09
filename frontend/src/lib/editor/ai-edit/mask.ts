/**
 * Mask utilities for the AI Edit canvas. The mask lives in an offscreen
 * canvas at the video's native-ish resolution; the on-screen canvas is a
 * scaled view of it. Export is a PNG data URL (white = selected, transparent
 * = untouched) — the format the backend edit jobs will consume in E2.
 */

export type SelectionTool =
  | "brush"
  | "eraser"
  | "lasso"
  | "rect"
  | "ellipse"
  | "select";

/** A detected/tracked object overlaid on the canvas — normalized 0-1 bbox. */
export interface TrackedObject {
  id: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  confidence: number;
  /** Manually-set presence range within the clip (seconds). Mock tracking
   * has no real per-frame presence data, so this starts as the full clip
   * duration and the user can narrow it — see tracking-panel.tsx. */
  startTime: number;
  endTime: number;
}

export interface BrushSettings {
  /** Diameter in mask-space pixels. */
  size: number;
  /** 0–1; lower = softer edge (rendered as canvas shadow blur). */
  hardness: number;
  /** 0–1 paint opacity. */
  opacity: number;
  /** Extra feather in pixels applied on export (E2 backend param). */
  feather: number;
}

export const DEFAULT_BRUSH: BrushSettings = {
  size: 48,
  hardness: 0.8,
  opacity: 1,
  feather: 4,
};

/** Overlay tint used to visualize the mask on screen. */
export const MASK_TINT = "rgba(139, 92, 246, 0.5)";

/** True if any pixel has been painted. */
export function maskHasInk(mask: HTMLCanvasElement): boolean {
  const ctx = mask.getContext("2d");
  if (!ctx) return false;
  const { data } = ctx.getImageData(0, 0, mask.width, mask.height);
  // Alpha channel scan; step 16 pixels for speed — plenty for a yes/no.
  for (let i = 3; i < data.length; i += 64) {
    if (data[i] > 8) return true;
  }
  return false;
}

/**
 * Export the painted mask as an opaque black/white PNG data URL:
 * white (edit region) where painted, black elsewhere. `feather` softens the
 * edge (mask-space px) so the backend gets a grayscale falloff and blends the
 * edit smoothly rather than with a hard cut.
 */
export function exportMask(mask: HTMLCanvasElement, feather = 0): string {
  const out = document.createElement("canvas");
  out.width = mask.width;
  out.height = mask.height;
  const ctx = out.getContext("2d");
  if (!ctx) return "";

  // 1. Draw the painted alpha (optionally blurred for feathering).
  if (feather > 0) ctx.filter = `blur(${feather}px)`;
  ctx.drawImage(mask, 0, 0);
  ctx.filter = "none";

  // 2. Turn the painted alpha into white, keeping its (feathered) alpha.
  ctx.globalCompositeOperation = "source-in";
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, out.width, out.height);

  // 3. Fill opaque black behind everything → white shape(s) on black.
  ctx.globalCompositeOperation = "destination-over";
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, out.width, out.height);

  return out.toDataURL("image/png");
}

export function clearMask(mask: HTMLCanvasElement): void {
  mask.getContext("2d")?.clearRect(0, 0, mask.width, mask.height);
}
