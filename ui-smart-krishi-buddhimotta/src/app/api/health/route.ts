export const dynamic = "force-dynamic";

export async function GET() {
  const baseUrl = process.env.BACKEND_URL?.trim().replace(/\/+$/, "");
  if (!baseUrl) {
    return Response.json({ ok: true, backend: "not-configured" });
  }
  try {
    const response = await fetch(`${baseUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    const result = await response.json().catch(() => ({})) as { ok?: boolean };
    return Response.json({ ok: true, backend: response.ok && result.ok ? "available" : "unavailable" });
  } catch {
    // The UI itself can still run without the optional Python service.
    return Response.json({ ok: true, backend: "unavailable" });
  }
}
