"use client";

import * as React from "react";

/** Scrolls the window to the top once when the marketplace route mounts. */
export function ScrollToTop() {
  React.useEffect(() => {
    window.scrollTo({ top: 0 });
  }, []);
  return null;
}
