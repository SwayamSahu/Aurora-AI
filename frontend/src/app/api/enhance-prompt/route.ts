const OLLAMA_URL = process.env.OLLAMA_URL ?? "http://localhost:11434";
const OLLAMA_MODEL = process.env.OLLAMA_MODEL ?? "llama3.2:latest";

export async function POST(request: Request) {
  const { prompt, type } = await request.json();

  if (!prompt || typeof prompt !== "string" || !prompt.trim()) {
    return Response.json({ error: "prompt is required" }, { status: 400 });
  }

  const medium = type === "generate_image" ? "image" : "video";

  const systemPrompt = `You are an expert AI ${medium} prompt engineer. When given a prompt, rewrite it to be more vivid, detailed, and cinematic. Add specific details about lighting, atmosphere, camera angles, style, and mood. Keep the core idea intact. Return ONLY the enhanced prompt text with no preamble, explanation, or quotes.`;

  const res = await fetch(`${OLLAMA_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      stream: false,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: prompt.trim() },
      ],
    }),
  });

  if (!res.ok) {
    return Response.json({ error: "Ollama request failed" }, { status: 502 });
  }

  const data = await res.json();
  const enhanced = (data.message?.content as string | undefined)?.trim() ?? prompt;

  return Response.json({ enhanced });
}
