/**
 * Generates self-hosted, free-license mock media for the Explore marketplace
 * and writes a matching mock-pieces.ts so data + files never drift.
 *
 * Images: Lorem Picsum (https://picsum.photos) — free to use, Unsplash-sourced.
 * Videos: reuse the cinematic free-license (Pexels License) clips already in
 *         /public/media.
 *
 * Run from the frontend/ dir:  node scripts/gen-marketplace-mock.mjs
 */
import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(fileURLToPath(import.meta.url)) + "/..";
const IMG_DIR = `${ROOT}/public/marketplace/img`;
const OUT_TS = `${ROOT}/src/lib/marketplace/mock-pieces.ts`;

// [fileW, fileH, declaredW, declaredH] — varied aspect ratios for the masonry.
const DIMS = [
  [480, 700, 832, 1216],
  [466, 700, 768, 1280],
  [700, 700, 1024, 1024],
  [700, 466, 1216, 832],
  [700, 438, 1280, 800],
];
const CATS = [
  "fantasy",
  "landscapes",
  "portraits",
  "anime",
  "animals",
  "sci-fi",
  "fashion",
  "food",
];
const TITLE = {
  fantasy: "Fantasy",
  landscapes: "Landscapes",
  portraits: "Portraits",
  anime: "Anime",
  animals: "Animals",
  "sci-fi": "Sci-Fi",
  fashion: "Fashion",
  food: "Food",
};
const VIEWS = [
  12000, 7000, 17000, 8500, 6800, 7500, 7200, 1100, 4800, 983, 1800, 1600, 625,
  748, 1200, 913, 14000, 1300,
];

const IMAGE_COUNT = 28;

// Static video pieces reusing existing /public/media clips.
const VIDEOS = [
  { seed: "ocean", file: "hero-ocean", title: "Landscapes", category: "landscapes", dur: 12, w: 1280, h: 720 },
  { seed: "forest", file: "hero-forest", title: "Fantasy", category: "fantasy", dur: 12, w: 1280, h: 720 },
  { seed: "coast", file: "hero-coast", title: "Landscapes", category: "landscapes", dur: 12, w: 1280, h: 720 },
  { seed: "city", file: "hero-city", title: "Sci-Fi", category: "sci-fi", dur: 12, w: 1280, h: 720 },
  { seed: "ink", file: "generate-ink", title: "Anime", category: "anime", dur: 12, w: 1280, h: 720 },
  { seed: "neon", file: "edit-neon", title: "Sci-Fi", category: "sci-fi", dur: 12, w: 1280, h: 720 },
];

async function download(url, path) {
  const res = await fetch(url, { redirect: "follow" });
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  const buf = Buffer.from(await res.arrayBuffer());
  await writeFile(path, buf);
  return buf.length;
}

function stats(i) {
  return {
    views: VIEWS[i % VIEWS.length],
    comments: (i * 3) % 5,
    likes: (i * 7) % 6,
    bookmarks: i % 3,
    inspired: 8000 + i * 317,
  };
}

async function main() {
  await mkdir(IMG_DIR, { recursive: true });

  const pieces = [];

  // ---- Images (download full + tiny LQIP) ----
  for (let i = 0; i < IMAGE_COUNT; i++) {
    const seed = `aur${String(i + 1).padStart(2, "0")}`;
    const [fw, fh, dw, dh] = DIMS[i % DIMS.length];
    const category = CATS[i % CATS.length];
    const lw = Math.max(8, Math.round(fw / 24));
    const lh = Math.max(8, Math.round(fh / 24));

    const full = await download(
      `https://picsum.photos/seed/${seed}/${fw}/${fh}`,
      `${IMG_DIR}/${seed}.jpg`,
    );
    const lqip = await download(
      `https://picsum.photos/seed/${seed}/${lw}/${lh}`,
      `${IMG_DIR}/${seed}-lqip.jpg`,
    );
    process.stdout.write(`img ${seed} ${category} ${full}B (+${lqip}B lqip)\n`);

    const status = i === 5 || i === 17 ? "sold" : "available";
    pieces.push({
      id: `img-${seed}`,
      type: "image",
      title: TITLE[category],
      category,
      width: dw,
      height: dh,
      posterUrl: `/marketplace/img/${seed}.jpg`,
      lqip: `/marketplace/img/${seed}-lqip.jpg`,
      mediaUrl: `/marketplace/img/${seed}.jpg`,
      watermarked: true,
      status,
      stats: stats(i),
      creator: { handle: "@aurora", avatarUrl: "" },
    });
  }

  // ---- Videos (reference existing /media files) ----
  VIDEOS.forEach((v, j) => {
    const i = IMAGE_COUNT + j;
    pieces.push({
      id: `vid-${v.seed}`,
      type: "video",
      title: v.title,
      category: v.category,
      width: v.w,
      height: v.h,
      durationSec: v.dur,
      posterUrl: `/media/${v.file}.jpg`,
      lqip: `/media/${v.file}.jpg`,
      mediaUrl: `/media/${v.file}.mp4`,
      watermarked: true,
      status: "available",
      stats: stats(i),
      creator: { handle: "@aurora", avatarUrl: "" },
    });
  });

  // Interleave so videos are sprinkled through the wall, not clustered.
  const images = pieces.filter((p) => p.type === "image");
  const videos = pieces.filter((p) => p.type === "video");
  const mixed = [];
  let vi = 0;
  images.forEach((p, idx) => {
    mixed.push(p);
    if ((idx + 1) % 5 === 0 && vi < videos.length) mixed.push(videos[vi++]);
  });
  while (vi < videos.length) mixed.push(videos[vi++]);

  // Category display counts for the chips (mock totals, not the rendered count).
  const counts = {
    fantasy: 1314,
    landscapes: 1451,
    portraits: 2278,
    anime: 751,
    animals: 1242,
    "sci-fi": 1964,
    fashion: 1057,
    food: 502,
  };
  const categories = CATS.map((name) => ({
    name,
    label: TITLE[name],
    count: counts[name],
  }));
  const total = Object.values(counts).reduce((a, b) => a + b, 0);

  const ts = `/**
 * Mock marketplace data — Phase 2.
 * Generated by scripts/gen-marketplace-mock.mjs. Edit the generator, not this
 * file. Images are Lorem Picsum (free, Unsplash-sourced); videos are the
 * Pexels-License clips in /public/media. Swap for real data via the API layer.
 */

export type MediaType = "image" | "video";

export interface Piece {
  id: string;
  type: MediaType;
  title: string;
  category: string;
  width: number;
  height: number;
  durationSec?: number;
  posterUrl: string;
  lqip: string;
  mediaUrl: string;
  watermarked: boolean;
  status: "available" | "sold" | "pending";
  stats: {
    views: number;
    comments: number;
    likes: number;
    bookmarks: number;
    inspired: number;
  };
  creator: { handle: string; avatarUrl: string };
}

export interface MkCategory {
  name: string;
  label: string;
  count: number;
}

export const MOCK_TOTAL = ${total};

export const MOCK_CATEGORIES: MkCategory[] = ${JSON.stringify(categories, null, 2)};

export const MOCK_PIECES: Piece[] = ${JSON.stringify(mixed, null, 2)};
`;

  await writeFile(OUT_TS, ts);
  process.stdout.write(`\nwrote ${OUT_TS} (${mixed.length} pieces)\n`);
}

main().catch((e) => {
  process.stderr.write(`FAILED: ${e.message}\n`);
  process.exit(1);
});
