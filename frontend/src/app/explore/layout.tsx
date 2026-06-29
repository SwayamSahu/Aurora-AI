import type { Metadata } from "next";
import { Press_Start_2P } from "next/font/google";

import { ExploreNav } from "@/components/marketplace/explore-nav";
import { ScrollToTop } from "@/components/marketplace/scroll-to-top";

// Pixel display face — used ONLY for the marketplace wordmark.
const pixel = Press_Start_2P({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-pixel-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Explore — Aurora Marketplace",
  description:
    "Browse and make yours a dense wall of AI-generated video and imagery, created on Aurora's open studio.",
};

export default function ExploreLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <div className={`${pixel.variable} explore-root relative`}>
      <ScrollToTop />
      <ExploreNav />
      <main className="relative z-10">{children}</main>
      {modal}
    </div>
  );
}
