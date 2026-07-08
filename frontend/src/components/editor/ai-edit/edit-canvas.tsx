"use client";

import * as React from "react";

import type { Clip } from "@/lib/api/timeline";
import { assetContentUrl } from "@/lib/api/assets";
import { useAsset } from "@/components/editor/assets-context";
import {
  type SelectionTool,
  type BrushSettings,
  MASK_TINT,
  clearMask,
  maskHasInk,
} from "@/lib/editor/ai-edit/mask";

/** Mask-space resolution; the display canvas scales to fit. */
const MASK_W = 1280;
const MASK_H = 720;

export interface EditCanvasHandle {
  getMaskCanvas: () => HTMLCanvasElement | null;
  clear: () => void;
}

interface Point {
  x: number;
  y: number;
}

/**
 * The AI Edit painting surface: shows the selected clip's frame with a
 * mask-painting canvas on top. Brush/eraser paint continuously; lasso,
 * rectangle and ellipse commit a region on pointer-up.
 */
export const EditCanvas = React.forwardRef<
  EditCanvasHandle,
  {
    clip: Clip;
    tool: SelectionTool;
    brush: BrushSettings;
    onInkChange: (hasInk: boolean) => void;
  }
>(function EditCanvas({ clip, tool, brush, onInkChange }, ref) {
  const asset = useAsset(clip.asset_id);
  const displayRef = React.useRef<HTMLCanvasElement>(null);
  const maskRef = React.useRef<HTMLCanvasElement | null>(null);
  const drawing = React.useRef(false);
  const lastPt = React.useRef<Point | null>(null);
  const startPt = React.useRef<Point | null>(null);
  const lassoPts = React.useRef<Point[]>([]);
  const [cursor, setCursor] = React.useState<Point | null>(null);

  // Lazily create the offscreen mask canvas.
  if (typeof window !== "undefined" && !maskRef.current) {
    const c = document.createElement("canvas");
    c.width = MASK_W;
    c.height = MASK_H;
    maskRef.current = c;
  }

  React.useImperativeHandle(ref, () => ({
    getMaskCanvas: () => maskRef.current,
    clear: () => {
      if (maskRef.current) clearMask(maskRef.current);
      repaint();
      onInkChange(false);
    },
  }));

  /** Composite mask tint onto the display canvas. */
  const repaint = React.useCallback(
    (previewShape?: { kind: SelectionTool; a: Point; b: Point } | null) => {
      const display = displayRef.current;
      const mask = maskRef.current;
      if (!display || !mask) return;
      const ctx = display.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, display.width, display.height);

      // Tinted mask.
      ctx.save();
      ctx.globalAlpha = 1;
      const tint = document.createElement("canvas");
      tint.width = mask.width;
      tint.height = mask.height;
      const tctx = tint.getContext("2d");
      if (tctx) {
        tctx.drawImage(mask, 0, 0);
        tctx.globalCompositeOperation = "source-in";
        tctx.fillStyle = MASK_TINT;
        tctx.fillRect(0, 0, tint.width, tint.height);
        ctx.drawImage(tint, 0, 0, display.width, display.height);
      }
      ctx.restore();

      // Marching-ants style preview for shape tools.
      if (previewShape) {
        const { kind, a, b } = previewShape;
        const sx = display.width / MASK_W;
        const sy = display.height / MASK_H;
        ctx.save();
        ctx.strokeStyle = "rgba(196,181,253,0.95)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        if (kind === "rect") {
          ctx.strokeRect(a.x * sx, a.y * sy, (b.x - a.x) * sx, (b.y - a.y) * sy);
        } else if (kind === "ellipse") {
          ctx.beginPath();
          ctx.ellipse(
            ((a.x + b.x) / 2) * sx,
            ((a.y + b.y) / 2) * sy,
            (Math.abs(b.x - a.x) / 2) * sx,
            (Math.abs(b.y - a.y) / 2) * sy,
            0,
            0,
            Math.PI * 2,
          );
          ctx.stroke();
        } else if (kind === "lasso" && lassoPts.current.length > 1) {
          ctx.beginPath();
          lassoPts.current.forEach((p, i) => {
            if (i === 0) ctx.moveTo(p.x * sx, p.y * sy);
            else ctx.lineTo(p.x * sx, p.y * sy);
          });
          ctx.stroke();
        }
        ctx.restore();
      }
    },
    [],
  );

  // Size the display canvas to its container.
  React.useEffect(() => {
    const display = displayRef.current;
    if (!display) return;
    const parent = display.parentElement;
    if (!parent) return;
    const ro = new ResizeObserver(() => {
      display.width = parent.clientWidth;
      display.height = parent.clientHeight;
      repaint();
    });
    ro.observe(parent);
    return () => ro.disconnect();
  }, [repaint]);

  /** Pointer position in mask-space coordinates. */
  function toMask(e: React.PointerEvent): Point {
    const rect = displayRef.current!.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * MASK_W,
      y: ((e.clientY - rect.top) / rect.height) * MASK_H,
    };
  }

  function strokeTo(p: Point) {
    const mask = maskRef.current;
    if (!mask) return;
    const ctx = mask.getContext("2d");
    if (!ctx) return;
    const from = lastPt.current ?? p;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.lineWidth = brush.size;
    ctx.globalAlpha = brush.opacity;
    if (tool === "eraser") {
      ctx.globalCompositeOperation = "destination-out";
      ctx.strokeStyle = "#fff";
    } else {
      ctx.globalCompositeOperation = "source-over";
      ctx.strokeStyle = "#8b5cf6";
      // Soft edge via shadow blur when hardness < 1.
      const blur = (1 - brush.hardness) * brush.size * 0.6;
      if (blur > 0.5) {
        ctx.shadowColor = "#8b5cf6";
        ctx.shadowBlur = blur;
      }
    }
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    ctx.restore();
    lastPt.current = p;
  }

  function commitShape(a: Point, b: Point) {
    const mask = maskRef.current;
    if (!mask) return;
    const ctx = mask.getContext("2d");
    if (!ctx) return;
    ctx.save();
    ctx.globalAlpha = brush.opacity;
    ctx.fillStyle = "#8b5cf6";
    if (tool === "rect") {
      ctx.fillRect(
        Math.min(a.x, b.x),
        Math.min(a.y, b.y),
        Math.abs(b.x - a.x),
        Math.abs(b.y - a.y),
      );
    } else if (tool === "ellipse") {
      ctx.beginPath();
      ctx.ellipse(
        (a.x + b.x) / 2,
        (a.y + b.y) / 2,
        Math.abs(b.x - a.x) / 2,
        Math.abs(b.y - a.y) / 2,
        0,
        0,
        Math.PI * 2,
      );
      ctx.fill();
    } else if (tool === "lasso" && lassoPts.current.length > 2) {
      ctx.beginPath();
      lassoPts.current.forEach((p, i) => {
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      });
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();
  }

  function onPointerDown(e: React.PointerEvent) {
    e.currentTarget.setPointerCapture(e.pointerId);
    drawing.current = true;
    const p = toMask(e);
    lastPt.current = p;
    startPt.current = p;
    lassoPts.current = [p];
    if (tool === "brush" || tool === "eraser") {
      strokeTo(p);
      repaint();
    }
  }

  function onPointerMove(e: React.PointerEvent) {
    const p = toMask(e);
    setCursor({ x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY });
    if (!drawing.current) return;
    if (tool === "brush" || tool === "eraser") {
      strokeTo(p);
      repaint();
    } else if (tool === "lasso") {
      lassoPts.current.push(p);
      repaint({ kind: "lasso", a: startPt.current!, b: p });
    } else {
      repaint({ kind: tool, a: startPt.current!, b: p });
    }
  }

  function onPointerUp(e: React.PointerEvent) {
    if (!drawing.current) return;
    drawing.current = false;
    const p = toMask(e);
    if (tool === "rect" || tool === "ellipse" || tool === "lasso") {
      commitShape(startPt.current!, p);
    }
    lastPt.current = null;
    startPt.current = null;
    lassoPts.current = [];
    repaint();
    if (maskRef.current) onInkChange(maskHasInk(maskRef.current));
  }

  const showBrushCursor = tool === "brush" || tool === "eraser";
  const display = displayRef.current;
  const cursorSize = display
    ? (brush.size * display.width) / MASK_W
    : brush.size;

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-black">
      {/* Frame under the mask */}
      {asset && clip.kind === "video" ? (
        <video
          src={assetContentUrl(asset)}
          muted
          playsInline
          preload="metadata"
          className="pointer-events-none absolute inset-0 size-full object-contain"
        />
      ) : (
        <div className="absolute inset-0 grid place-items-center text-sm text-muted-foreground">
          Select a video clip to edit
        </div>
      )}

      {/* Paint layer */}
      <canvas
        ref={displayRef}
        role="img"
        aria-label="Mask painting canvas"
        className="absolute inset-0 size-full touch-none"
        style={{ cursor: showBrushCursor ? "none" : "crosshair" }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={() => setCursor(null)}
      />

      {/* Brush size cursor */}
      {showBrushCursor && cursor ? (
        <div
          aria-hidden
          className="pointer-events-none absolute rounded-full border border-white/80 shadow-[0_0_0_1px_rgba(0,0,0,0.5)]"
          style={{
            width: cursorSize,
            height: cursorSize,
            left: cursor.x - cursorSize / 2,
            top: cursor.y - cursorSize / 2,
          }}
        />
      ) : null}
    </div>
  );
});
