import { NextResponse, type NextRequest } from "next/server";

// Stronger gate than the friends' invite code: /admin exposes everyone's notify
// targets. Mirrors require_admin() in server.py (Basic Auth, constant-time compare).
// Runs on the edge runtime, so no node:crypto — hand-rolled constant-time compare.
function timingSafeEqual(a: string, b: string): boolean {
  let diff = a.length ^ b.length;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ (b.charCodeAt(i) || 0);
  return diff === 0;
}

const UNAUTHORIZED = new NextResponse("admin only", {
  status: 401,
  headers: { "WWW-Authenticate": 'Basic realm="admin"' },
});

export function middleware(req: NextRequest) {
  const password = process.env.ADMIN_PASSWORD ?? "";
  const header = req.headers.get("authorization") ?? "";
  if (!password || !header.startsWith("Basic ")) return UNAUTHORIZED;

  let decoded = "";
  try {
    decoded = atob(header.slice(6));
  } catch {
    return UNAUTHORIZED;
  }
  const idx = decoded.indexOf(":");
  const user = idx === -1 ? decoded : decoded.slice(0, idx);
  const pass = idx === -1 ? "" : decoded.slice(idx + 1);

  if (timingSafeEqual(user, "admin") && timingSafeEqual(pass, password)) return NextResponse.next();
  return UNAUTHORIZED;
}

export const config = { matcher: "/admin" };
