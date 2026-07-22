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

function validOrganizationId(value: string | null): value is string {
  return Boolean(
    value &&
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        value,
      ),
  );
}

async function registrationResponse(
  request: NextRequest,
  backendResponse: Response,
): Promise<NextResponse> {
  const payload = await parseBackendJson(backendResponse);
  if (!payload) {
    return gatewayUnavailableResponse(
      request,
      new Error("INVALID_REGISTER_PROXY_RESPONSE"),
    );
  }

  if (!backendResponse.ok) {
    return NextResponse.json(payload, {
      status: backendResponse.status,
      headers: {
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
      },
    });
  }

  const tokens = extractTokenPair(payload);
  if (!tokens) {
    return gatewayUnavailableResponse(
      request,
      new Error("REGISTER_PROXY_TOKENS_MISSING"),
    );
  }

  const response = NextResponse.json(withoutTokenFields(payload), {
    status: backendResponse.status,
    headers: {
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
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
      {
        status: 404,
        headers: {
          "cache-control": "no-store",
          "x-content-type-options": "nosniff",
        },
      },
    );
  }

  if (PUBLIC_ORIGIN_ONLY_PATHS.has(normalizedLowerPath)) {
    if (!isTrustedRequestOrigin(request)) return originRejectedResponse();
  } else if (!hasValidCsrf(request)) {
    return csrfRejectedResponse();
  }

  const headers = createBackendHeaders(request, getAccessCookie(request));
  const organizationId = request.headers.get("x-organization-id");
  if (validOrganizationId(organizationId)) {
    headers.set("x-organization-id", organizationId);
  }
  const init: StreamingRequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
    const contentType = request.headers.get("content-type") || "";
    if (contentType.includes("multipart/form-data")) {
      init.body = await request.formData();
      headers.delete("content-type");
      headers.delete("content-length");
    } else {
      init.body = await request.arrayBuffer();
    }
  }

  try {
    const backendResponse = await fetchBackend(
      `${normalizedPath}/`,
      init,
      request.nextUrl.search,
    );
    if (backendResponse.status === 404) {
      console.log("BACKEND RETURNED 404 for:", normalizedPath);
    }
    if (normalizedLowerPath === "auth/register") {
      return registrationResponse(request, backendResponse);
    }
    return backendResponseToNext(backendResponse);
  } catch (error: unknown) {
    console.log("PROXY ERROR:", error);
    return gatewayUnavailableResponse(request, error);
  }
}

export const GET = proxyRequest;
export const HEAD = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
export const OPTIONS = proxyRequest;
