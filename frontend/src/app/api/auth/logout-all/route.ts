import { NextResponse, type NextRequest } from "next/server";

import {
  clearAuthCookies,
  createBackendHeaders,
  csrfRejectedResponse,
  fetchBackend,
  gatewayUnavailableResponse,
  getAccessCookie,
  getRefreshCookie,
  hasValidCsrf,
  parseBackendJson,
  refreshTokenPair,
  withoutTokenFields,
} from "@/lib/server/auth-bff";

export const runtime = "nodejs";

async function resolveAccessToken(
  request: NextRequest,
): Promise<string | null> {
  const accessToken = getAccessCookie(request);
  if (accessToken) return accessToken;

  const refreshToken = getRefreshCookie(request);
  if (!refreshToken) return null;
  const refreshed = await refreshTokenPair(request, refreshToken);
  return refreshed.response.ok && refreshed.tokens
    ? refreshed.tokens.access
    : null;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!hasValidCsrf(request)) return csrfRejectedResponse();

  try {
    let accessToken = await resolveAccessToken(request);
    if (!accessToken) {
      const response = NextResponse.json(
        { message: "Todas as sessões locais foram encerradas." },
        {
          status: 200,
          headers: {
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
          },
        },
      );
      clearAuthCookies(response);
      return response;
    }

    let backendResponse = await fetchBackend("auth/logout-all/", {
      method: "POST",
      headers: createBackendHeaders(request, accessToken),
      body: "{}",
    });

    if (backendResponse.status === 401) {
      const refreshToken = getRefreshCookie(request);
      if (refreshToken) {
        const refreshed = await refreshTokenPair(request, refreshToken);
        if (refreshed.response.ok && refreshed.tokens) {
          accessToken = refreshed.tokens.access;
          backendResponse = await fetchBackend("auth/logout-all/", {
            method: "POST",
            headers: createBackendHeaders(request, accessToken),
            body: "{}",
          });
        }
      }
    }

    const payload = await parseBackendJson(backendResponse);
    const response = NextResponse.json(
      payload
        ? withoutTokenFields(payload)
        : {
            error: {
              code: "LOGOUT_ALL_NOT_CONFIRMED",
              message:
                "As sessões locais foram removidas, mas a revogação remota não foi confirmada.",
            },
          },
      {
        status: backendResponse.status,
        headers: {
          "cache-control": "no-store",
          "x-content-type-options": "nosniff",
        },
      },
    );
    clearAuthCookies(response);
    return response;
  } catch (error: unknown) {
    const response = gatewayUnavailableResponse(request, error);
    clearAuthCookies(response);
    return response;
  }
}
