export const runtime = "nodejs";

export async function POST() {
  return Response.json(
    { error: "This legacy paid-compute endpoint is disabled. Use /api/workers for the zero-cost Qill fleet." },
    { status: 410 },
  );
}
