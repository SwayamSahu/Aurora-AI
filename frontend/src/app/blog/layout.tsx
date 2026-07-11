import type { Metadata } from "next";
import { Playfair_Display } from "next/font/google";

import { BlogNav } from "@/components/blog/blog-nav";

// Elegant serif for headings only — body text stays on Aurora's Geist Sans.
const serif = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-blog-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: "The Journal — Aurora Blog",
  description:
    "Tutorials, prompts and creative guides from the people building on Aurora.",
};

export default function BlogLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={`${serif.variable} blog-root relative`}>
      <BlogNav />
      <main className="relative z-10">{children}</main>
    </div>
  );
}
