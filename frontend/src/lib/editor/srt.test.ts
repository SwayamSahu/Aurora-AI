import { describe, expect, it } from "vitest";

import { parseSrt } from "@/lib/editor/srt";

const SAMPLE = `1
00:00:00,000 --> 00:00:02,000
Hello world.

2
00:00:02,500 --> 00:00:05,250
This is Aurora.
`;

describe("parseSrt", () => {
  it("parses captions with timing", () => {
    const caps = parseSrt(SAMPLE);
    expect(caps).toHaveLength(2);
    expect(caps[0]).toMatchObject({ start: 0, duration: 2, text: "Hello world." });
    expect(caps[1].start).toBeCloseTo(2.5);
    expect(caps[1].duration).toBeCloseTo(2.75);
    expect(caps[1].text).toBe("This is Aurora.");
  });

  it("ignores empty input", () => {
    expect(parseSrt("")).toEqual([]);
  });

  it("joins multi-line caption text", () => {
    const caps = parseSrt(
      "1\n00:00:00,000 --> 00:00:01,000\nline one\nline two\n",
    );
    expect(caps[0].text).toBe("line one line two");
  });
});
