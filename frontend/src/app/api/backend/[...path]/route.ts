import { NextResponse, type NextRequest } from "next/server";

import { isBlockedAuthProxyPath } from "@/lib/auth-constants";
import {
  backendResponseToNext,
  createBackendHeaders,
  csrfRejectedResponse,
  extractTokenPair,
  fetchBackend,
  gatewayUnavailableResponse,
  getAccessCookie,
  hasValidCsrf,
  isTrustedRequestOrigin,
  originRejectedResponse,
  parseBackendJson,
  setAuthCookies,
  withoutTokenFields,
} from "@/lib/server/auth-bff";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

type StreamingRequestInit = RequestInit & { duplex?: "half" };

const PUBLIC_ORIGIN_ONLY_PATHS = new Set([
  "auth/register",
  "auth/password/reset",
  "auth/password/reset/confirm",
]);

async function registrationResponse(
  backendResponse: Response,
): Promise<NextResponse> {
  const payload = await parseBackendJson(backendResponse);
  if (!payload) return gatewayUnavailableResponse();

  if (!backendResponse.ok) {
    return NextResponse.json(payload, {
      status: backendResponse.status,
      headers: { "cache-control": "no-store" },
    });
  }

  const tokens = extractTokenPair(payload);
  if (!tokens) return gatewayUnavailableResponse();

  const response = NextResponse.json(withoutTokenFields(payload), {
    status: backendResponse.status,
    headers: { "cache-control": "no-store" },
  });
  setAuthCookies(response, tokens);
  return response;
}

async function proxyRequest(
  request: NextRequest,
  context: RouteContext,
): Promise<NextResponse> {
  const { path } = await context.params;
  const normalizedPath = path.map((part) => encodeURIComponent(part)).join("/");
  const normalizedLowerPath = normalizedPath.toLowerCase();
  if (!normalizedPath || isBlockedAuthProxyPath(normalizedPath)) {
    return NextResponse.json(
      {
        error: {
          code: "ROUTE_NOT_AVAILABLE",
          message: "A rota solicitada não está disponível neste canal.",
        },
      },
      { status: 404 },
    );
  }

  if (PUBLIC_ORIGIN_ONLY_PATHS.has(normalizedLowerPath)) {
    if (!isTrustedRequestOrigin(request)) return originRejectedResponse();
  } else if (!hasValidCsrf(request)) {
    return csrfRejectedResponse();
  }

  const headers = createBackendHeaders(request, getAccessCookie(request));
  const init: StreamingRequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
    init.body = request.body;
    init.duplex = "half";
  }

  try {
    const backendResponse = await fetchBackend(
      `${normalizedPath}/`,
      init,
      request.nextUrl.search,
    );
    if (normalizedLowerPath === "auth/register") {
      return registrationResponse(backendResponse);
    }
    return backendResponseToNext(backendResponse);
  } catch {
    return gatewayUnavailableResponse();
  }
}

export const GET = proxyRequest;
export const HEAD = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
export const OPTIONS = proxyRequest;
