import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";

import { NextResponse, type NextRequest } from "next/server";

import {
  buildBackendUrl,
  clearAuthCookies,
  createBackendHeaders,
  csrfRejectedResponse,
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

function requestLogout(
  request: NextRequest,
  refreshToken: string,
): Promise<Response> {
  const url = buildBackendUrl("auth/logout/");
  const body = Buffer.from(JSON.stringify({ refresh: refreshToken }), "utf8");
  const headers = createBackendHeaders(request);
  headers.set("content-type", "application/json");
  headers.set("content-length", String(body.byteLength));
  headers.set("connection", "close");

  const sendRequest = url.protocol === "https:" ? httpsRequest : httpRequest;

  return new Promise<Response>((resolve, reject) => {
    const upstreamRequest = sendRequest(
      url,
      {
        method: "POST",
        headers: Object.fromEntries(headers.entries()),
        agent: false,
        timeout: 10_000,
      },
      (upstreamResponse) => {
        const chunks: Buffer[] = [];
        upstreamResponse.on("data", (chunk: Buffer | string) => {
          chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
        });
        upstreamResponse.on("end", () => {
          const responseHeaders = new Headers();
          for (const [name, value] of Object.entries(upstreamResponse.headers)) {
            if (Array.isArray(value)) {
              for (const item of value) responseHeaders.append(name, item);
            } else if (value !== undefined) {
              responseHeaders.set(name, String(value));
            }
          }

          resolve(
            new Response(Buffer.concat(chunks), {
              status: upstreamResponse.statusCode ?? 502,
              headers: responseHeaders,
            }),
          );
        });
      },
    );

    upstreamRequest.on("timeout", () => {
      upstreamRequest.destroy(new Error("AUTH_LOGOUT_UPSTREAM_TIMEOUT"));
    });
    upstreamRequest.on("error", reject);
    upstreamRequest.end(body);
  });
}

async function revokeCurrentSession(
  request: NextRequest,
  refreshToken: string,
): Promise<Response> {
  logLogoutStage("upstream_start");
  const response = await requestLogout(request, refreshToken);
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
