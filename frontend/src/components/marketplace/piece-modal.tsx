"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "motion/react";

import type { Piece } from "@/lib/marketplace/mock-pieces";
import { PieceDetail } from "@/components/marketplace/piece-detail";

export function PieceModal({
  piece,
  similar,
  number,
}: {
  piece: Piece;
  similar: Piece[];
  number: string;
}) {
  const router = useRouter();
  const reduce = useReducedMotion();
  const close = React.useCallback(() => router.back(), [router]);

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [close]);

  return (
    <div className="fixed inset-0 z-[60]" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <motion.div
        className="absolute inset-0 bg-[var(--mk-bg)]/96 backdrop-blur-sm"
        initial={{ opacity: reduce ? 1 : 0 }}
        animate={{ opacity: 1 }}
        onClick={close}
      />

      {/* Scrollable content */}
      <motion.div
        className="absolute inset-0 overflow-y-auto scrollbar-thin"
        initial={{ opacity: reduce ? 1 : 0, y: reduce ? 0 : 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* Clicking empty space closes; inner content stops propagation. */}
        <div
          className="min-h-full"
          onClick={(e) => {
            if (e.target === e.currentTarget) close();
          }}
        >
          <div onClick={(e) => e.stopPropagation()}>
            <PieceDetail
              piece={piece}
              similar={similar}
              number={number}
              onBack={close}
              pulse
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
