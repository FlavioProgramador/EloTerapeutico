import { NextResponse, type NextRequest } from "next/server";

import { isBlockedAuthProxyPath } from "@/lib/auth-constants";
import {
  backendResponseToNext,
  createBackendHeaders,
  csrfRejectedResponse,
  fetchBackend,
  gatewayUnavailableResponse,
  getAccessCookie,
  hasValidCsrf,
} from "@/lib/server/auth-bff";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

type StreamingRequestInit = RequestInit & { duplex?: "half" };

async function proxyRequest(
  request: NextRequest,
  context: RouteContext,
): Promise<NextResponse> {
  if (!hasValidCsrf(request)) return csrfRejectedResponse();

  const { path } = await context.params;
  const normalizedPath = path.map((part) => encodeURIComponent(part)).join("/");
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
