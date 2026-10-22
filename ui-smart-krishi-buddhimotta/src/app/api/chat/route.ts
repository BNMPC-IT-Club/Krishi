import { NextRequest, NextResponse } from "next/server";

const models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"];

type IncomingMessage = { role: "user" | "assistant"; content: string };

const systemPrompt = `আপনি “ক্ষেতসাথী” নামের বাংলাদেশের কৃষকদের জন্য সহায়ক এআই। সব উত্তর প্রাঞ্জল, সম্মানজনক বাংলায় দিন।
আপনি সাধারণ কৃষি পরিচর্যা, আবহাওয়া-সচেতন পরিকল্পনা, ফসল ব্যবস্থাপনা এবং বাজারের তথ্য কীভাবে যাচাই করতে হয়—এসব বিষয়ে সহায়তা করেন।
নিয়ম: (১) প্রদত্ত বাজার তথ্যকে কেবল প্রোটোটাইপ/নমুনা বলা হলে কখনো লাইভ বা সরকারি দাম বলবেন না। (২) রোগের ছবি না দেখে নিশ্চিত রোগ নির্ণয় করবেন না; সম্ভাব্য কারণ, নিরাপদ পদক্ষেপ এবং স্থানীয় কৃষি কর্মকর্তার পরামর্শের কথা বলবেন। (৩) কীটনাশক বা সার ব্যবহারে নিবন্ধিত লেবেল, স্থানীয় কৃষি অফিস ও নিরাপত্তা নির্দেশনা অনুসরণ করতে বলবেন; নির্দিষ্ট মাত্রা অনুমান করবেন না। (৪) আবহাওয়ার তথ্য থাকলে তা পূর্বাভাস, নিশ্চয়তা নয়—এ কথা বলবেন। (৫) সংক্ষিপ্ত, কাজের ধাপভিত্তিক উত্তর দিন; প্রয়োজন হলে ৩–৫টি বুলেট ব্যবহার করুন।`;

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
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    return NextResponse.json({
      error: "AI সহকারী চালু করতে সার্ভারে GROQ_API_KEY যোগ করুন। অন্য সব ফিচার ব্যবহার করা যাবে।",
      code: "MISSING_GROQ_KEY",
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

  const context = typeof body.context === "string" ? body.context.trim().slice(0, 1000) : "";
  const content = context ? `${systemPrompt}\n\nপ্রাসঙ্গিক অ্যাপ তথ্য: ${context}` : systemPrompt;
  let lastError = "";

  for (const model of models) {
    try {
      const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
        signal: AbortSignal.timeout(30000),
        body: JSON.stringify({
          model,
          messages: [{ role: "system", content }, ...messages],
          temperature: 0.45,
          max_completion_tokens: 650,
          include_reasoning: false,
        }),
      });

      if (!response.ok) {
        lastError = `${model}: ${response.status}`;
        if (response.status === 401 || response.status === 403) break;
        continue;
      }

      const result = await response.json() as { choices?: Array<{ message?: { content?: string } }> };
      const answer = result.choices?.[0]?.message?.content?.trim();
      if (answer) return NextResponse.json({ answer, model });
      lastError = `${model}: empty response`;
    } catch {
      lastError = `${model}: request failed`;
    }
  }

  console.error("Groq chat unavailable", lastError);
  return NextResponse.json({
    error: "AI সেবাটি এই মুহূর্তে সাড়া দিচ্ছে না। কিছুক্ষণ পরে আবার চেষ্টা করুন।",
    code: "GROQ_UNAVAILABLE",
  }, { status: 502 });
}
