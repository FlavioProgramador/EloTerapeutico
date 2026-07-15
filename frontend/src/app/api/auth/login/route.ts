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
    backendResponse = await fetchBackend("auth/login/", {
      method: "POST",
      headers: createBackendHeaders(request),
      body: await request.text(),
    });
  } catch {
    return gatewayUnavailableResponse();
  }

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
