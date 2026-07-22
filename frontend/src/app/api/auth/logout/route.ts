import { NextResponse, type NextRequest } from "next/server";

import {
  clearAuthCookies,
  createBackendHeaders,
  csrfRejectedResponse,
  fetchBackend,
  gatewayUnavailableResponse,
  getRefreshCookie,
  hasValidCsrf,
  parseBackendJson,
  withoutTokenFields,
} from "@/lib/server/auth-bff";

export const runtime = "nodejs";

async function revokeCurrentSession(
  request: NextRequest,
  refreshToken: string,
): Promise<Response> {
  return fetchBackend("auth/logout/", {
    method: "POST",
    headers: {
      ...Object.fromEntries(createBackendHeaders(request).entries()),
      "content-type": "application/json",
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!hasValidCsrf(request)) return csrfRejectedResponse();

  const refreshToken = getRefreshCookie(request);
  if (!refreshToken) {
    const response = NextResponse.json(
      { message: "Sessão encerrada." },
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

  try {
    const backendResponse = await revokeCurrentSession(request, refreshToken);
    const payload = await parseBackendJson(backendResponse);
    const response = NextResponse.json(
      payload
        ? withoutTokenFields(payload)
        : {
            error: {
              code: "LOGOUT_NOT_CONFIRMED",
              message:
                "A sessão local foi removida, mas a revogação remota não foi confirmada.",
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
