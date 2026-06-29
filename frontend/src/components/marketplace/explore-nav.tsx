"use client";

import * as React from "react";
import Link from "next/link";

import { cn } from "@/lib/utils";
import { mkNav } from "@/lib/marketplace/content";

/**
 * Marketplace top navigation. Sticky, transparent over the near-black bg,
 * blurs on scroll. Pixel wordmark left, centered links with a cyan underline
 * on the active route, Sign in + Start Free on the right.
 */
export function ExploreNav() {
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 transition-colors duration-300",
        scrolled
          ? "border-b border-[var(--mk-border)] bg-[var(--mk-bg)]/80 backdrop-blur-xl"
          : "border-b border-transparent",
      )}
    >
      <nav
        aria-label="Marketplace"
        className="mx-auto flex h-[72px] w-full max-w-[1600px] items-center justify-between px-4 md:px-10"
      >
        {/* Pixel wordmark */}
        <Link
          href="/"
          aria-label="Aurora home"
          className="font-pixel text-[15px] tracking-[2px] text-foreground"
        >
          {mkNav.wordmark}
          <span className="text-mk-cyan">.AI</span>
        </Link>

        {/* Center links */}
        <div className="hidden items-center gap-7 md:flex">
          {mkNav.links.map((link) => {
            const active = link.href === mkNav.activeHref;
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative py-1 text-[15px] transition-colors",
                  active
                    ? "font-medium text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {link.label}
                {active ? (
                  <span className="absolute -bottom-[6px] left-0 h-0.5 w-full rounded-full bg-mk-cyan shadow-[0_0_10px_var(--mk-cyan)]" />
                ) : null}
              </Link>
            );
          })}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          <Link
            href={mkNav.signIn.href}
            className="hidden text-[14px] text-muted-foreground transition-colors hover:text-foreground sm:inline"
          >
            {mkNav.signIn.label}
          </Link>
          <Link
            href={mkNav.startFree.href}
            className="rounded-full border border-mk-cyan/40 px-4 py-2 text-[14px] font-medium text-mk-cyan shadow-[0_0_18px_-6px_var(--mk-cyan)] transition-colors hover:bg-mk-cyan/10"
          >
            {mkNav.startFree.label}
          </Link>
        </div>
      </nav>
    </header>
  );
}
