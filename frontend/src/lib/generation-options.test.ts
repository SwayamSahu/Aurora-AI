import { describe, expect, it } from "vitest";

import type { VideoModelSpec } from "@/lib/api/generation";

import {
  ASPECT_RATIOS,
  aspectFromLegacyResolution,
  clampDurationToModel,
  DEFAULT_ASPECT_RATIO,
  durationOptionsFor,
  resolutionForAspect,
} from "./generation-options";

function spec(overrides: Partial<VideoModelSpec> = {}): VideoModelSpec {
  return {
    id: "test",
    label: "Test",
    provider: "Test",
    kind: "api",
    resolution: "1080p",
    max_width: 1920,
    max_height: 1080,
    min_duration: 3,
    max_duration: 15,
    default_duration: 5,
    supports_i2v: false,
    badges: [],
    ...overrides,
  };
}

describe("aspect ratio catalog", () => {
  it("has a unique id per entry, matching the reference picker order", () => {
    const ids = ASPECT_RATIOS.map((a) => a.id);
    expect(ids).toEqual(["auto", "16:9", "9:16", "4:3", "3:4", "1:1", "21:9"]);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("default aspect is a real catalog entry", () => {
    expect(ASPECT_RATIOS.some((a) => a.id === DEFAULT_ASPECT_RATIO)).toBe(true);
  });
});

describe("resolutionForAspect", () => {
  it("returns null for auto — caller omits width/height", () => {
    expect(resolutionForAspect("auto")).toBeNull();
  });

  it("returns null for an unknown id", () => {
    expect(resolutionForAspect("nope")).toBeNull();
  });

  it("produces square dimensions for 1:1", () => {
    const r = resolutionForAspect("1:1");
    expect(r).not.toBeNull();
    expect(r!.width).toBe(r!.height);
  });

  it("produces a wide box for 16:9 and a tall box for 9:16 (inverse)", () => {
    const landscape = resolutionForAspect("16:9")!;
    const portrait = resolutionForAspect("9:16")!;
    expect(landscape.width).toBeGreaterThan(landscape.height);
    expect(portrait.height).toBeGreaterThan(portrait.width);
    // 9:16 is the transpose of 16:9.
    expect(landscape.width).toBe(portrait.height);
    expect(landscape.height).toBe(portrait.width);
  });

  it("every non-auto ratio yields dimensions divisible by 8", () => {
    for (const a of ASPECT_RATIOS) {
      if (!a.ratio) continue;
      const r = resolutionForAspect(a.id)!;
      expect(r.width % 8).toBe(0);
      expect(r.height % 8).toBe(0);
    }
  });

  it("width/height ratio approximates the requested aspect", () => {
    const r = resolutionForAspect("21:9")!;
    expect(r.width / r.height).toBeCloseTo(21 / 9, 1);
  });
});

describe("durationOptionsFor (per-model capability envelope)", () => {
  it("falls back to the static durations when no model is known", () => {
    const opts = durationOptionsFor(undefined);
    expect(opts.map((o) => o.value)).toEqual(["2", "4", "6"]);
  });

  it("only offers durations within the model's range, including endpoints", () => {
    const opts = durationOptionsFor(spec({ min_duration: 3, max_duration: 15 }));
    const vals = opts.map((o) => Number(o.value));
    expect(Math.min(...vals)).toBe(3);
    expect(Math.max(...vals)).toBe(15);
    expect(vals.every((v) => v >= 3 && v <= 15)).toBe(true);
    // Sorted ascending, no duplicates.
    expect([...vals].sort((a, b) => a - b)).toEqual(vals);
    expect(new Set(vals).size).toBe(vals.length);
  });

  it("handles a tight range (Veo 3.1 Lite: 4–8s)", () => {
    const opts = durationOptionsFor(spec({ min_duration: 4, max_duration: 8 }));
    expect(opts.map((o) => Number(o.value))).toEqual([4, 5, 6, 8]);
  });

  it("handles a very wide range (Kling Motion: 3–30s)", () => {
    const opts = durationOptionsFor(spec({ min_duration: 3, max_duration: 30 }));
    const vals = opts.map((o) => Number(o.value));
    expect(vals[0]).toBe(3);
    expect(vals[vals.length - 1]).toBe(30);
  });
});

describe("clampDurationToModel", () => {
  it("keeps an in-range duration unchanged", () => {
    expect(clampDurationToModel("5", spec({ min_duration: 3, max_duration: 15 }))).toBe(
      "5",
    );
  });

  it("snaps an out-of-range duration to the model default", () => {
    const s = spec({ min_duration: 4, max_duration: 8, default_duration: 6 });
    expect(clampDurationToModel("2", s)).toBe("6"); // below min
    expect(clampDurationToModel("15", s)).toBe("6"); // above max
  });

  it("passes the value through untouched when no model is known", () => {
    expect(clampDurationToModel("2", undefined)).toBe("2");
  });
});

describe("aspectFromLegacyResolution (back-compat)", () => {
  it("maps old square resolutions to 1:1", () => {
    expect(aspectFromLegacyResolution("512x512")).toBe("1:1");
  });

  it("maps old 16:9-ish resolutions to 16:9", () => {
    expect(aspectFromLegacyResolution("1024x576")).toBe("16:9");
  });

  it("maps old portrait resolutions to their nearest ratio", () => {
    // 512x768 = 0.667, closer to 3:4 (0.75) than 9:16 (0.5625).
    expect(aspectFromLegacyResolution("512x768")).toBe("3:4");
    // 576x1024 = 0.5625, an exact 9:16.
    expect(aspectFromLegacyResolution("576x1024")).toBe("9:16");
  });

  it("falls back to the default for missing/malformed input", () => {
    expect(aspectFromLegacyResolution(undefined)).toBe(DEFAULT_ASPECT_RATIO);
    expect(aspectFromLegacyResolution("garbage")).toBe(DEFAULT_ASPECT_RATIO);
  });
});
