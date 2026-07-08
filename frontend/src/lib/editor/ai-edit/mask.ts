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
  | "ellipse";

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

/** Export the painted mask as a black/white PNG data URL. */
export function exportMask(mask: HTMLCanvasElement): string {
  const out = document.createElement("canvas");
  out.width = mask.width;
  out.height = mask.height;
  const ctx = out.getContext("2d");
  if (!ctx) return "";
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, out.width, out.height);
  // Paint alpha → white.
  ctx.save();
  ctx.drawImage(mask, 0, 0);
  ctx.globalCompositeOperation = "source-in";
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, out.width, out.height);
  ctx.restore();
  return out.toDataURL("image/png");
}

export function clearMask(mask: HTMLCanvasElement): void {
  mask.getContext("2d")?.clearRect(0, 0, mask.width, mask.height);
}
