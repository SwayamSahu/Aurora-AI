"use client";

import * as React from "react";
import Link from "next/link";
import { ShoppingCart, Coins, PlusCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { useCart, useWallet } from "@/lib/marketplace/queries";

/**
 * Marketplace top navigation. Sticky, transparent over the near-black bg,
 * blurs on scroll. Pixel wordmark left, centered links, auth-aware right
 * side: wallet balance + cart badge + sell CTA when signed in, Sign
 * in/Start Free otherwise.
 */
export function ExploreNav() {
  const [scrolled, setScrolled] = React.useState(false);
  const { status } = useAuth();
  const authed = status === "authenticated";
  const { data: wallet } = useWallet(authed);
  const { data: cart } = useCart(authed);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = [
    { label: "Explore", href: "/explore" },
    { label: "My Marketplace", href: "/explore/me", authOnly: true },
    { label: "Plans", href: "/explore/plans" },
  ];

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
        <Link
          href="/"
          aria-label="Aurora home"
          className="font-pixel text-[15px] tracking-[2px] text-foreground"
        >
          AURORA
          <span className="text-mk-cyan">.AI</span>
        </Link>

        <div className="hidden items-center gap-7 md:flex">
          {links
            .filter((l) => !l.authOnly || authed)
            .map((link) => {
              const active = link.href === "/explore";
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

        <div className="flex items-center gap-3">
          {authed ? (
            <>
              <Link
                href="/explore/wallet"
                className="hidden items-center gap-1.5 rounded-full bg-[var(--mk-surface-2)] px-3 py-1.5 text-[13px] font-semibold text-foreground transition-colors hover:bg-[var(--mk-surface-hover)] sm:inline-flex"
              >
                <Coins className="size-3.5 text-mk-lavender" />
                {wallet?.balance_credits ?? 0}
              </Link>
              <Link
                href="/explore/cart"
                aria-label="Cart"
                className="relative inline-flex size-9 items-center justify-center rounded-full bg-[var(--mk-surface-2)] text-foreground transition-colors hover:bg-[var(--mk-surface-hover)]"
              >
                <ShoppingCart className="size-4" />
                {cart && cart.items.length > 0 ? (
                  <span className="absolute -right-1 -top-1 grid size-4 place-items-center rounded-full bg-mk-lavender text-[10px] font-bold text-black">
                    {cart.items.length}
                  </span>
                ) : null}
              </Link>
              <Link
                href="/explore/new"
                className="hidden items-center gap-1.5 rounded-full border border-mk-cyan/40 px-4 py-2 text-[14px] font-medium text-mk-cyan shadow-[0_0_18px_-6px_var(--mk-cyan)] transition-colors hover:bg-mk-cyan/10 sm:inline-flex"
              >
                <PlusCircle className="size-3.5" />
                Sell
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden text-[14px] text-muted-foreground transition-colors hover:text-foreground sm:inline"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="rounded-full border border-mk-cyan/40 px-4 py-2 text-[14px] font-medium text-mk-cyan shadow-[0_0_18px_-6px_var(--mk-cyan)] transition-colors hover:bg-mk-cyan/10"
              >
                Start Free
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
