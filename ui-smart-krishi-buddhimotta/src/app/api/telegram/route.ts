import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";
export const maxDuration = 10;

function secretMatches(received: string | null, expected: string) {
  if (!received) return false;
  const receivedBytes = Buffer.from(received);
  const expectedBytes = Buffer.from(expected);
  return receivedBytes.length === expectedBytes.length && timingSafeEqual(receivedBytes, expectedBytes);
}

export async function POST(request: NextRequest) {
  const botToken = process.env.TELEGRAM_BOT_TOKEN?.trim();
  const webhookSecret = process.env.TELEGRAM_WEBHOOK_SECRET?.trim();
  const frontendUrl = process.env.FRONTEND_URL?.trim().replace(/\/+$/, "");
  if (!botToken || !webhookSecret || !frontendUrl) {
    return NextResponse.json({ error: "Telegram webhook configuration is incomplete." }, { status: 503 });
  }
  if (!secretMatches(request.headers.get("x-telegram-bot-api-secret-token"), webhookSecret)) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  let update: {
    message?: {
      text?: string;
      chat?: { id?: number | string };
      from?: { first_name?: string };
    };
  };
  try {
    update = await request.json();
  } catch {
    return NextResponse.json({ ok: true });
  }

  const message = update.message;
  const chatId = message?.chat?.id;
  const text = message?.text?.trim() ?? "";
  if (chatId === undefined || !/^\/(?:start|help)(?:@[a-zA-Z0-9_]+)?(?:\s|$)/i.test(text)) {
    return NextResponse.json({ ok: true });
  }

  let link: URL;
  try {
    link = new URL(frontendUrl);
    if (link.protocol !== "https:" && link.hostname !== "localhost") throw new Error("HTTPS required");
  } catch {
    return NextResponse.json({ error: "FRONTEND_URL must be a valid HTTPS URL." }, { status: 500 });
  }

  const firstName = (message?.from?.first_name ?? "কৃষক বন্ধু").slice(0, 50);
  const reply = {
    chat_id: chatId,
    text: `আসসালামু আলাইকুম, ${firstName}! 🌱\n\nক্ষেতসাথীতে স্বাগতম। এখানে আবহাওয়া, ফসল পরামর্শ, রোগ-সহায়তা ও পরীক্ষামূলক বাজার পূর্বাভাস পাবেন। বাজারের নমুনা তথ্য লাইভ দর নয়—কেনাবেচার আগে স্থানীয় বাজারে যাচাই করুন।`,
    reply_markup: {
      inline_keyboard: [[{ text: "🌾 ক্ষেতসাথী ওয়েব অ্যাপ খুলুন", url: link.toString() }]],
    },
    disable_web_page_preview: true,
  };

  try {
    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reply),
      cache: "no-store",
      signal: AbortSignal.timeout(7000),
    });
    if (!response.ok) {
      return NextResponse.json({ error: "Telegram sendMessage failed." }, { status: 502 });
    }
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Telegram API is temporarily unavailable." }, { status: 502 });
  }
}
