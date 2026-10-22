import { NextRequest, NextResponse } from "next/server";

const numericParam = (value: string | null) => value !== null && Number.isFinite(Number(value)) ? Number(value) : null;

export async function GET(request: NextRequest) {
  const lat = numericParam(request.nextUrl.searchParams.get("lat"));
  const lng = numericParam(request.nextUrl.searchParams.get("lng"));

  if (lat === null || lng === null || lat < 20 || lat > 27 || lng < 88 || lng > 93) {
    return NextResponse.json({ error: "বাংলাদেশের একটি বৈধ অবস্থান নির্বাচন করুন।" }, { status: 400 });
  }

  const query = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lng.toString(),
    current: "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
    daily: "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,sunrise,sunset",
    timezone: "Asia/Dhaka",
    forecast_days: "7",
  });

  try {
    const response = await fetch(`https://api.open-meteo.com/v1/forecast?${query}`, {
      next: { revalidate: 900 },
      signal: AbortSignal.timeout(12000),
    });

    if (!response.ok) {
      return NextResponse.json({ error: "আবহাওয়ার উৎস থেকে তথ্য পাওয়া যায়নি।" }, { status: 502 });
    }

    const weather = await response.json();
    return NextResponse.json({ weather, source: "Open-Meteo", fetchedAt: new Date().toISOString() }, {
      headers: { "Cache-Control": "public, s-maxage=900, stale-while-revalidate=900" },
    });
  } catch {
    return NextResponse.json({ error: "আবহাওয়ার তথ্য আনতে সময় লেগেছে। আবার চেষ্টা করুন।" }, { status: 504 });
  }
}
