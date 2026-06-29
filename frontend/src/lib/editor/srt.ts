export interface Caption {
  start: number;
  duration: number;
  text: string;
}

function parseTimestamp(ts: string): number {
  // 00:00:02,000  (hh:mm:ss,mmm)
  const m = ts.trim().match(/(\d+):(\d+):(\d+)[,.](\d+)/);
  if (!m) return 0;
  const [, h, min, s, ms] = m;
  return (
    Number(h) * 3600 + Number(min) * 60 + Number(s) + Number(ms) / 1000
  );
}

/** Parse an SRT document into caption clips (start + duration + text). */
export function parseSrt(srt: string): Caption[] {
  const blocks = srt.replace(/\r/g, "").trim().split(/\n\s*\n/);
  const captions: Caption[] = [];
  for (const block of blocks) {
    const lines = block.split("\n");
    const timeLine = lines.find((l) => l.includes("-->"));
    if (!timeLine) continue;
    const [from, to] = timeLine.split("-->");
    const start = parseTimestamp(from);
    const end = parseTimestamp(to);
    const text = lines
      .slice(lines.indexOf(timeLine) + 1)
      .join(" ")
      .trim();
    if (text) {
      captions.push({ start, duration: Math.max(0.3, end - start), text });
    }
  }
  return captions;
}
