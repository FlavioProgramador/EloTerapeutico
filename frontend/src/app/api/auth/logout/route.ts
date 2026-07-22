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

function logLogoutStage(stage: string, details: Record<string, unknown> = {}): void {
  console.info(
    JSON.stringify({
      event: "auth_logout_stage",
      stage,
      ...details,
    }),
  );
}

async function revokeCurrentSession(
  request: NextRequest,
  refreshToken: string,
): Promise<Response> {
  logLogoutStage("upstream_start");
  const response = await fetchBackend("auth/logout/", {
    method: "POST",
    headers: {
      ...Object.fromEntries(createBackendHeaders(request).entries()),
      "content-type": "application/json",
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  logLogoutStage("upstream_complete", { status: response.status });
  return response;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  logLogoutStage("request_received");
  if (!hasValidCsrf(request)) {
    logLogoutStage("csrf_rejected");
    return csrfRejectedResponse();
  }

  const refreshToken = getRefreshCookie(request);
  logLogoutStage("csrf_accepted", { has_refresh_cookie: Boolean(refreshToken) });
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
    logLogoutStage("local_session_cleared");
    return response;
  }

  try {
    const backendResponse = await revokeCurrentSession(request, refreshToken);
    logLogoutStage("upstream_parse_start");
    const payload = await parseBackendJson(backendResponse);
    logLogoutStage("upstream_parse_complete", { has_payload: Boolean(payload) });
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
    logLogoutStage("response_ready", { status: backendResponse.status });
    return response;
  } catch (error: unknown) {
    logLogoutStage("upstream_error", {
      error_type: error instanceof Error ? error.name : typeof error,
    });
    const response = gatewayUnavailableResponse(request, error);
    clearAuthCookies(response);
    return response;
  }
}
