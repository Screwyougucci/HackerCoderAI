export const runtime = "nodejs";

export async function GET() {
  return Response.json({
    ok: true,
    service: "Qill Distributed Control Center",
    dashboard: "online",
    compute: "GitHub Actions public-repository runners",
    workerCount: 8,
    billingMode: "strict-zero",
    modelInference: "not enabled; no paid model APIs are called",
  });
}
