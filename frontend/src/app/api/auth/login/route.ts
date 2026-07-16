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
  } catch (err: any) {
    return NextResponse.json(
      { 
        error: "DEBUG_FETCH_FAILED", 
        message: err?.message, 
        cause: err?.cause?.message, 
        stack: err?.stack,
        url: process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || "fallback"
      }, 
      { status: 502 }
    );
  }

  const payload = await parseBackendJson(backendResponse);
  if (!payload) {
     return NextResponse.json({ 
       error: "DEBUG_PAYLOAD_NULL", 
       status: backendResponse.status,
       statusText: backendResponse.statusText,
       contentType: backendResponse.headers.get("content-type") 
     }, { status: 502 });
  }

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
