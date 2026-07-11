"use client";

import * as React from "react";
import Link from "next/link";
import { PenLine } from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";

/** Sticky top bar for the blog section — blurs on scroll, like Explore's. */
export function BlogNav() {
  const [scrolled, setScrolled] = React.useState(false);
  const { status } = useAuth();

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const writeHref = status === "authenticated" ? "/blog/new" : "/login";

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
        aria-label="Blog"
        className="mx-auto flex h-[72px] w-full max-w-[1200px] items-center justify-between px-4 md:px-8"
      >
        <Link
          href="/"
          aria-label="Aurora home"
          className="font-serif-display text-lg italic tracking-tight text-foreground"
        >
          Aurora
        </Link>

        <div className="hidden items-center gap-6 md:flex">
          <Link
            href="/blog"
            className="text-[15px] text-muted-foreground transition-colors hover:text-foreground"
          >
            The Journal
          </Link>
          <Link
            href="/explore"
            className="text-[15px] text-muted-foreground transition-colors hover:text-foreground"
          >
            Explore
          </Link>
          {status === "authenticated" ? (
            <Link
              href="/blog/me"
              className="text-[15px] text-muted-foreground transition-colors hover:text-foreground"
            >
              My posts
            </Link>
          ) : null}
        </div>

        <Button asChild size="sm" className="gap-1.5">
          <Link href={writeHref}>
            <PenLine className="size-3.5" />
            Write
          </Link>
        </Button>
      </nav>
    </header>
  );
}
