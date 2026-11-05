import { generateText } from "ai";
import { Sandbox } from "@vercel/sandbox";

export const runtime = "nodejs";
export const maxDuration = 300;

const DEFAULT_MODEL = "alibaba/qwen3-coder-30b-a3b";

export async function POST(request: Request) {
  let body: { goal?: unknown };
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Send a valid JSON request." }, { status: 400 });
  }

  const goal = typeof body.goal === "string" ? body.goal.trim() : "";
  if (!goal || goal.length > 2000) {
    return Response.json({ error: "Task must contain 1–2000 characters." }, { status: 400 });
  }

  const model = process.env.AI_GATEWAY_MODEL || DEFAULT_MODEL;

  try {
    const generated = await generateText({
      model,
      maxOutputTokens: 500,
      prompt: [
        "You are HackerCoderAI Remote, a coding and defensive-security assistant.",
        "Analyze the user's goal and give a useful, concise plan or answer.",
        "Do not claim that you inspected files, accessed systems, or performed actions.",
        "Only recommend testing systems the user owns or is authorized to assess.",
        "Do not provide instructions for credential theft, persistence, malware, or attacks on third-party targets.",
        "",
        "User task:",
        goal,
      ].join("\n"),
    });

    const sandbox = await Sandbox.create({
      resources: { vcpus: 1 },
      timeout: 120_000,
      persistent: false,
      networkPolicy: "deny-all",
    });

    try {
      const command = await sandbox.runCommand("python3", [
        "-c",
        "print('HackerCoderAI Vercel Sandbox: online'); print('Arithmetic check:', 6 * 7)",
      ]);
      const stdout = await command.stdout();
      const stderr = await command.stderr();
      return Response.json({
        model,
        answer: generated.text,
        sandbox: {
          status: command.exitCode === 0 ? "passed" : "failed",
          exitCode: command.exitCode,
          stdout: stdout || stderr,
        },
      });
    } finally {
      await sandbox.stop();
    }
  } catch (error) {
    console.error("remote_run_failed", error);
    return Response.json({
      error: error instanceof Error ? error.message : "Cloud run failed.",
      hint: "Check that AI Gateway is enabled for this Vercel project and that the selected model is available to your team.",
    }, { status: 502 });
  }
}
