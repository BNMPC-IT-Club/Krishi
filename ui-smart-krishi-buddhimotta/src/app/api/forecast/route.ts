import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function GET(request: NextRequest) {
  const baseUrl = process.env.BACKEND_URL?.trim().replace(/\/+$/, "");
  if (!baseUrl) {
    return NextResponse.json({ error: "Python backend-এর BACKEND_URL সেট করা নেই।" }, { status: 503 });
  }
  const district = (request.nextUrl.searchParams.get("district") ?? "ঢাকা").slice(0, 80);
  const crop = (request.nextUrl.searchParams.get("crop") ?? "ধান").slice(0, 80);
  const url = new URL(`${baseUrl}/api/forecast`);
  url.searchParams.set("district", district);
  url.searchParams.set("crop", crop);

  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: AbortSignal.timeout(55_000),
    });
    const data = await response.json().catch(() => ({})) as Record<string, unknown>;
    if (!response.ok) {
      return NextResponse.json({
        error: typeof data.detail === "string" ? data.detail : "নমুনা পূর্বাভাস পাওয়া যায়নি।",
      }, { status: response.status });
    }
    return NextResponse.json(data, { status: 200 });
  } catch {
    return NextResponse.json({ error: "Python backend সাময়িকভাবে অনুপলব্ধ।" }, { status: 502 });
  }
}
