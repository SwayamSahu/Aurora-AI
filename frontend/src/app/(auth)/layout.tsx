import Link from "next/link";

import { Logo } from "@/components/layout/logo";
import { RedirectIfAuthed } from "@/components/auth/redirect-if-authed";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RedirectIfAuthed>
      <div className="grid min-h-svh lg:grid-cols-2">
        {/* Form side */}
        <div className="flex flex-col px-6 py-8">
          <div className="mb-auto">
            <Link href="/" aria-label="Aurora home">
              <Logo />
            </Link>
          </div>
          <div className="mx-auto w-full max-w-sm py-12">{children}</div>
          <p className="mb-auto text-center text-xs text-muted-foreground">
            © {new Date().getFullYear()} Aurora · Open source
          </p>
        </div>

        {/* Brand side */}
        <div className="relative hidden overflow-hidden bg-primary lg:block">
          <div
            className="absolute inset-0 opacity-90"
            style={{
              background:
                "radial-gradient(120% 120% at 20% 10%, oklch(0.72 0.2 320) 0%, oklch(0.55 0.22 285) 45%, oklch(0.3 0.12 275) 100%)",
            }}
          />
          <div className="relative flex h-full flex-col justify-end p-12 text-primary-foreground">
            <blockquote className="space-y-3">
              <p className="text-2xl font-semibold leading-snug">
                Generate, edit and export AI video — all in one open-source
                studio.
              </p>
              <footer className="text-sm opacity-80">
                Aurora — built on free & open-source software.
              </footer>
            </blockquote>
          </div>
        </div>
      </div>
    </RedirectIfAuthed>
  );
}
