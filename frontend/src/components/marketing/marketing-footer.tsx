import Link from "next/link";

import { brand, footer } from "@/lib/landing/content";
import { Logo } from "@/components/layout/logo";
import { GithubMark } from "@/components/marketing/github-mark";

function FooterLink({ href, external, label }: { href: string; external?: boolean; label: string }) {
  const className =
    "text-sm text-muted-foreground transition-colors hover:text-foreground";
  if (external) {
    return (
      <a href={href} target="_blank" rel="noreferrer noopener" className={className}>
        {label}
      </a>
    );
  }
  return (
    <Link href={href} className={className}>
      {label}
    </Link>
  );
}

export function MarketingFooter() {
  return (
    <footer className="border-t border-border bg-card/20">
      <div className="mx-auto w-full max-w-7xl px-6 py-16">
        <div className="grid gap-12 lg:grid-cols-[1.5fr_2fr]">
          {/* Brand blurb */}
          <div className="max-w-sm">
            <Logo />
            <p className="mt-4 text-pretty text-sm text-muted-foreground">
              {footer.blurb}
            </p>
            <a
              href={brand.social.github}
              target="_blank"
              rel="noreferrer noopener"
              aria-label="GitHub"
              className="mt-5 inline-flex size-9 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:text-foreground"
            >
              <GithubMark className="size-4" />
            </a>
          </div>

          {/* Link columns */}
          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
            {footer.columns.map((column) => (
              <div key={column.title}>
                <h3 className="text-sm font-semibold">{column.title}</h3>
                <ul className="mt-4 space-y-3">
                  {column.links.map((link) => (
                    <li key={link.label}>
                      <FooterLink {...link} />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
          <p className="text-xs text-muted-foreground">{footer.copyright}</p>
          <div className="flex items-center gap-6">
            {footer.legal.map((link) => (
              <FooterLink key={link.label} {...link} />
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
