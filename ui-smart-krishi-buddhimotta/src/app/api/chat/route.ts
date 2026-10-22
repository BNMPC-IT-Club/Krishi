import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 60;

type IncomingMessage = { role: "user" | "assistant"; content: string };

function safeMessages(value: unknown): IncomingMessage[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((message): message is IncomingMessage => Boolean(message) && typeof message === "object" && (message as { role?: unknown }).role !== undefined && typeof (message as { content?: unknown }).content === "string")
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({ role: message.role, content: message.content.trim().slice(0, 1800) }))
    .filter((message) => message.content.length > 0)
    .slice(-10);
}

export async function POST(request: NextRequest) {
  const baseUrl = process.env.BACKEND_URL?.trim().replace(/\/+$/, "");
  if (!baseUrl) {
    return NextResponse.json({
      error: "Python backend-এর BACKEND_URL সেট করা নেই। পরে আবার চেষ্টা করুন।",
      code: "BACKEND_NOT_CONFIGURED",
    }, { status: 503 });
  }

  let body: { messages?: unknown; context?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "অনুরোধটি পড়া যায়নি।" }, { status: 400 });
  }
  const messages = safeMessages(body.messages);
  if (!messages.length) {
    return NextResponse.json({ error: "একটি প্রশ্ন লিখুন।" }, { status: 400 });
  }
  const context = typeof body.context === "string" ? body.context.trim().slice(0, 1000) : undefined;

  try {
    const response = await fetch(`${baseUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, context }),
      cache: "no-store",
      signal: AbortSignal.timeout(55_000),
    });
    const data = await response.json().catch(() => ({})) as { answer?: string; error?: string; detail?: string; model?: string; code?: string };
    if (!response.ok) {
      return NextResponse.json({
        error: data.detail ?? data.error ?? "AI সেবাটি এই মুহূর্তে সাড়া দিচ্ছে না। পরে আবার চেষ্টা করুন।",
        code: data.code ?? "BACKEND_ERROR",
      }, { status: response.status });
    }
    return NextResponse.json(data, { status: 200 });
  } catch {
    return NextResponse.json({
      error: "Python backend-এ সংযোগ পাওয়া যাচ্ছে না। ফ্রি হোস্টে প্রথম অনুরোধে ঘুম ভাঙতে সময় লাগতে পারে—একটু পরে আবার চেষ্টা করুন।",
      code: "BACKEND_UNAVAILABLE",
    }, { status: 502 });
  }
}
