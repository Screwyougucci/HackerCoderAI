export const runtime = "nodejs";

export async function GET() {
  return Response.json({
    ok: true,
    service: "HackerCoderAI Remote",
    sandbox: "Vercel Sandbox SDK configured",
    model: process.env.AI_GATEWAY_MODEL || "alibaba/qwen3-coder-30b-a3b",
  });
}
