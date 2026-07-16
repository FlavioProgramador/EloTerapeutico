import { NextResponse, type NextRequest } from "next/server";

import {
  ensureCsrfToken,
  getAccessCookie,
  getRefreshCookie,
  setCsrfCookie,
} from "@/lib/server/auth-bff";

export const runtime = "nodejs";

export async function GET(request: NextRequest): Promise<NextResponse> {
  const csrfToken = ensureCsrfToken(request);
  const authenticated = Boolean(
    getAccessCookie(request) || getRefreshCookie(request),
  );
  const response = NextResponse.json(
    {
      authenticated,
      csrf_token: csrfToken,
    },
    {
      status: 200,
      headers: { "cache-control": "no-store" },
    },
  );
  setCsrfCookie(response, csrfToken);
  return response;
}
