import { NextResponse, type NextRequest } from "next/server";

import {
  createBackendHeaders,
  extractTokenPair,
  fetchBackend,
  gatewayUnavailableResponse,
  isTrustedRequestOrigin,
  originRejectedResponse,
  parseBackendJson,
  setAuthCookies,
  withoutTokenFields,
} from "@/lib/server/auth-bff";

export const runtime = "nodejs";

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!isTrustedRequestOrigin(request)) return originRejectedResponse();

  let backendResponse: Response;
  try {
    backendResponse = await fetchBackend("auth/register/", {
      method: "POST",
      headers: createBackendHeaders(request),
      body: await request.text(),
    });
  } catch (error: unknown) {
    return gatewayUnavailableResponse(request, error);
  }

  const payload = await parseBackendJson(backendResponse);
  if (!payload) {
    return gatewayUnavailableResponse(
      request,
      new Error("INVALID_REGISTER_UPSTREAM_RESPONSE"),
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
      new Error("REGISTER_TOKENS_MISSING_FROM_UPSTREAM"),
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
