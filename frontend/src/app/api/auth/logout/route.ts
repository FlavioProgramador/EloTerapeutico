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
    const backendResponse = await requestLogout(request, refreshToken);
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
