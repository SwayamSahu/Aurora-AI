"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { brand, navLinks, cta } from "@/lib/landing/content";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/layout/logo";
import { ThemeToggle } from "@/components/theme/theme-toggle";

export function MarketingNav() {
  const [scrolled, setScrolled] = React.useState(false);
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Lock body scroll while the mobile menu is open.
  React.useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b border-border bg-background/80 backdrop-blur-xl"
          : "border-b border-transparent bg-transparent",
      )}
    >
      <nav
        aria-label="Primary"
        className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6"
      >
        <Link href="/" aria-label={`${brand.name} home`} className="shrink-0">
          <Logo />
        </Link>

        {/* Desktop links */}
        <div className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
          <Link
            href="/explore"
            className="rounded-md px-3 py-2 text-sm font-medium text-foreground transition-colors hover:text-primary"
          >
            Explore
          </Link>
          <Link
            href="/blog"
            className="rounded-md px-3 py-2 text-sm font-medium text-foreground transition-colors hover:text-primary"
          >
            Blogs
          </Link>
        </div>

        {/* Desktop actions */}
        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          <Button variant="ghost" size="sm" asChild>
            <Link href={cta.login.href}>{cta.login.label}</Link>
          </Button>
          <Button size="sm" asChild>
            <Link href={cta.primary.href}>{cta.primary.label}</Link>
          </Button>
        </div>

        {/* Mobile trigger */}
        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </div>
      </nav>

      {/* Mobile panel */}
      {open ? (
        <div className="border-t border-border bg-background/95 backdrop-blur-xl md:hidden">
          <div className="mx-auto flex w-full max-w-7xl flex-col gap-1 px-6 py-4">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2.5 text-sm font-medium text-foreground/90 transition-colors hover:bg-accent"
              >
                {link.label}
              </a>
            ))}
            <Link
              href="/explore"
              onClick={() => setOpen(false)}
              className="rounded-md px-3 py-2.5 text-sm font-semibold text-primary transition-colors hover:bg-accent"
            >
              Explore
            </Link>
            <Link
              href="/blog"
              onClick={() => setOpen(false)}
              className="rounded-md px-3 py-2.5 text-sm font-semibold text-primary transition-colors hover:bg-accent"
            >
              Blogs
            </Link>
            <div className="mt-3 flex flex-col gap-2">
              <Button variant="outline" asChild>
                <Link href={cta.login.href} onClick={() => setOpen(false)}>
                  {cta.login.label}
                </Link>
              </Button>
              <Button asChild>
                <Link href={cta.primary.href} onClick={() => setOpen(false)}>
                  {cta.primary.label}
                </Link>
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </header>
  );
}
