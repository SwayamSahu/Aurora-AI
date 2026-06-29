"use client";

import * as React from "react";

/** Fires onIntersect when scrolled near; used to load the next page. */
export function InfiniteSentinel({
  onIntersect,
  disabled,
}: {
  onIntersect: () => void;
  disabled?: boolean;
}) {
  const ref = React.useRef<HTMLDivElement>(null);
  const cb = React.useRef(onIntersect);

  React.useEffect(() => {
    cb.current = onIntersect;
  }, [onIntersect]);

  React.useEffect(() => {
    const el = ref.current;
    if (!el || disabled) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) cb.current();
      },
      { rootMargin: "600px 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [disabled]);

  return <div ref={ref} aria-hidden className="h-px w-full" />;
}
