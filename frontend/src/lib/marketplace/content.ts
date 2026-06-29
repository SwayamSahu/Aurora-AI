/**
 * Aurora Explore marketplace — single source of truth for chrome copy.
 * (Piece/category data lives in mock-pieces.ts; this file is UI text only.)
 */

export interface MkNavLink {
  label: string;
  href: string;
}

/** Marketplace top-bar links. `Explore` is the active route. */
export const mkNav = {
  wordmark: "AURORA",
  links: [
    { label: "Create", href: "/dashboard" },
    { label: "Explore", href: "/explore" },
    { label: "My Creations", href: "/projects" },
    { label: "Pricing", href: "/#open-source" },
    { label: "About", href: "/#features" },
    { label: "Blog", href: "/#faq" },
  ] as MkNavLink[],
  activeHref: "/explore",
  signIn: { label: "Sign in", href: "/login" },
  startFree: { label: "Start Free", href: "/signup" },
};

export const mkSearch = {
  placeholder: "Search — fantasy, anime, landscapes, portraits…",
  create: { label: "Create", href: "/dashboard" },
};
