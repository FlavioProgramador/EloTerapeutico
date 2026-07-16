import { NextResponse, type NextRequest } from "next/server";

import {
  clearAuthCookies,
  csrfRejectedResponse,
  gatewayUnavailableResponse,
  getRefreshCookie,
  hasValidCsrf,
  refreshTokenPair,
  setAuthCookies,
  withoutTokenFields,
} from "@/lib/server/auth-bff";

export const runtime = "nodejs";

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!hasValidCsrf(request)) return csrfRejectedResponse();

  const refreshToken = getRefreshCookie(request);
  if (!refreshToken) {
    const response = NextResponse.json(
      {
        error: {
          code: "REFRESH_TOKEN_MISSING",
          message: "A sessão expirou. Entre novamente.",
        },
      },
      { status: 401, headers: { "cache-control": "no-store" } },
    );
    clearAuthCookies(response);
    return response;
  }

  try {
    const { response: backendResponse, tokens, payload } =
      await refreshTokenPair(request, refreshToken);

    if (!backendResponse.ok || !tokens) {
      const response = NextResponse.json(
        payload
          ? withoutTokenFields(payload)
          : {
              error: {
                code: "REFRESH_REJECTED",
                message: "A sessão expirou. Entre novamente.",
              },
            },
        {
          status: backendResponse.ok ? 401 : backendResponse.status,
          headers: { "cache-control": "no-store" },
        },
      );
      clearAuthCookies(response);
      return response;
    }

    const response = NextResponse.json(
      { refreshed: true },
      { status: 200, headers: { "cache-control": "no-store" } },
    );
    setAuthCookies(response, tokens);
    return response;
  } catch {
    return gatewayUnavailableResponse();
  }
}
