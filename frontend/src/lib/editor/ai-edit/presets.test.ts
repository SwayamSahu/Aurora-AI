import { describe, expect, it } from "vitest";

import {
  EDIT_CATEGORIES,
  EDIT_PRESETS,
  MAGIC_PROMPT_PRESET,
  needsPaintedMask,
  needsPromptInput,
  presetsByCategory,
  resolvePrompt,
} from "./presets";

describe("AI edit preset catalog", () => {
  it("has unique preset ids", () => {
    const ids = EDIT_PRESETS.map((p) => p.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("every preset belongs to a declared category", () => {
    const cats = new Set(EDIT_CATEGORIES.map((c) => c.id));
    for (const p of EDIT_PRESETS) {
      expect(cats.has(p.category), `preset ${p.id} → ${p.category}`).toBe(true);
    }
  });

  it("every category has at least one preset", () => {
    for (const c of EDIT_CATEGORIES) {
      expect(
        presetsByCategory(c.id).length,
        `category ${c.id} is empty`,
      ).toBeGreaterThan(0);
    }
  });

  it("face swap is intentionally absent (ships gated in E6)", () => {
    for (const p of EDIT_PRESETS) {
      expect(p.id).not.toMatch(/face-?swap/i);
      expect(p.label.toLowerCase()).not.toContain("face swap");
    }
  });

  it("resolvePrompt substitutes the user text", () => {
    const p = EDIT_PRESETS.find((x) => x.id === "replace-object")!;
    expect(needsPromptInput(p)).toBe(true);
    expect(resolvePrompt(p, " a yellow Ferrari ")).toContain("a yellow Ferrari");
    expect(resolvePrompt(p, "x")).not.toContain("{prompt}");
  });

  it("painted-mask presets are flagged, auto-mask ones are not", () => {
    const painted = EDIT_PRESETS.find((x) => x.id === "remove-object")!;
    const auto = EDIT_PRESETS.find((x) => x.id === "sky-sunset")!;
    expect(needsPaintedMask(painted)).toBe(true);
    expect(needsPaintedMask(auto)).toBe(false);
  });

  it("magic prompt passes user text through verbatim", () => {
    expect(resolvePrompt(MAGIC_PROMPT_PRESET, "make it cinematic")).toBe(
      "make it cinematic",
    );
  });

  it("relight/atmosphere presets use global-restyle full-frame in the lighting category", () => {
    const ids = [
      "relight-storm",
      "relight-candlelight",
      "relight-rim",
      "relight-underwater",
      "relight-aurora-glow",
    ];
    for (const id of ids) {
      const p = EDIT_PRESETS.find((x) => x.id === id)!;
      expect(p, `missing preset ${id}`).toBeDefined();
      expect(p.category).toBe("lighting");
      expect(p.engine).toBe("global-restyle");
      expect(p.maskMode).toBe("full-frame");
      expect(needsPaintedMask(p)).toBe(false);
    }
  });

  it("swap-precise carries a lower diffusion strength for pose preservation", () => {
    const p = EDIT_PRESETS.find((x) => x.id === "swap-precise")!;
    expect(p).toBeDefined();
    expect(p.engine).toBe("masked-v2v");
    expect(needsPaintedMask(p)).toBe(true);
    expect(needsPromptInput(p)).toBe(true);
    expect(p.params?.strength).toBe(0.55);
  });

  it("reframe presets use the retime-camera engine with no mask", () => {
    const ids = ["cam-closeup", "cam-wide", "cam-vertical", "cam-dutch", "cam-thirds"];
    for (const id of ids) {
      const p = EDIT_PRESETS.find((x) => x.id === id)!;
      expect(p, `missing preset ${id}`).toBeDefined();
      expect(p.category).toBe("motion-camera");
      expect(p.engine).toBe("retime-camera");
      expect(p.maskMode).toBe("full-frame");
      expect(needsPaintedMask(p)).toBe(false);
      expect(needsPromptInput(p)).toBe(false);
    }
  });
});
