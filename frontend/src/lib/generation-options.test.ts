import { describe, expect, it } from "vitest";

import {
  ASPECT_RATIOS,
  aspectFromLegacyResolution,
  DEFAULT_ASPECT_RATIO,
  resolutionForAspect,
} from "./generation-options";

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
