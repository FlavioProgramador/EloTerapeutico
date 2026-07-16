import { randomBytes, timingSafeEqual } from "node:crypto";

import { NextResponse, type NextRequest } from "next/server";

import {
  AUTH_ACCESS_COOKIE,
  AUTH_CSRF_COOKIE,
  AUTH_REFRESH_COOKIE,
  isUnsafeHttpMethod,
} from "@/lib/auth-constants";

export interface TokenPair {
  access: string;
  refresh: string;
}

interface JsonObject {
  [key: string]: unknown;
}

type StreamingRequestInit = RequestInit & { duplex?: "half" };

const ACCESS_MAX_AGE_SECONDS = readPositiveInteger(
  process.env.AUTH_ACCESS_COOKIE_MAX_AGE,
  30 * 60,
);
const REFRESH_MAX_AGE_SECONDS = readPositiveInteger(
  process.env.AUTH_REFRESH_COOKIE_MAX_AGE,
  7 * 24 * 60 * 60,
);
const CSRF_MAX_AGE_SECONDS = REFRESH_MAX_AGE_SECONDS;
const COOKIE_SECURE = process.env.NODE_ENV === "production";

const FORWARDED_REQUEST_HEADERS = [
  "accept",
  "accept-language",
  "content-type",
  "idempotency-key",
  "if-match",
  "if-none-match",
  "range",
  "user-agent",
  "x-request-id",
] as const;

const FORWARDED_RESPONSE_HEADERS = [
  "accept-ranges",
  "content-disposition",
  "content-language",
  "content-type",
  "etag",
  "last-modified",
  "x-request-id",
] as const;

function readPositiveInteger(value: string | undefined, fallback: number): number {
  const parsed = Number.parseInt(value || "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function backendBaseUrl(): URL {
  const configured =
    process.env.BACKEND_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://backend:8000/api/v1/";
  return new URL(configured.endsWith("/") ? configured : `${configured}/`);
}

export function buildBackendUrl(path: string, search = ""): URL {
  const normalized = path.replace(/^\/+/, "");
  if (
    !normalized ||
    normalized.includes("..") ||
    normalized.includes("\\") ||
    normalized.includes("://")
  ) {
    throw new Error("INVALID_BACKEND_PATH");
  }

  const url = new URL(normalized, backendBaseUrl());
  url.search = search;
  return url;
}

export function isTrustedRequestOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  if (origin) {
    try {
      return new URL(origin).origin === request.nextUrl.origin;
    } catch {
      return false;
    }
  }

  const fetchSite = request.headers.get("sec-fetch-site");
  return (
    fetchSite === null ||
    fetchSite === "same-origin" ||
    fetchSite === "same-site" ||
    fetchSite === "none"
  );
}

function safeTokenEquals(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  if (leftBuffer.length !== rightBuffer.length) return false;
  return timingSafeEqual(leftBuffer, rightBuffer);
}

export function hasValidCsrf(request: NextRequest): boolean {
  if (!isUnsafeHttpMethod(request.method)) return true;
  if (!isTrustedRequestOrigin(request)) return false;

  const cookieToken = request.cookies.get(AUTH_CSRF_COOKIE)?.value || "";
  const headerToken = request.headers.get("x-csrf-token") || "";
  return Boolean(
    cookieToken && headerToken && safeTokenEquals(cookieToken, headerToken),
  );
}

export function csrfRejectedResponse(): NextResponse {
  return NextResponse.json(
    {
      error: {
        code: "CSRF_VALIDATION_FAILED",
        message: "A solicitação não pôde ser validada.",
      },
    },
    { status: 403 },
  );
}

export function originRejectedResponse(): NextResponse {
  return NextResponse.json(
    {
      error: {
        code: "ORIGIN_NOT_ALLOWED",
        message: "A origem da solicitação não é permitida.",
      },
    },
    { status: 403 },
  );
}

export function gatewayUnavailableResponse(errorDetails?: any): NextResponse {
  return NextResponse.json(
    {
      error: {
        code: "AUTH_GATEWAY_UNAVAILABLE",
        message: "O serviço de autenticação está temporariamente indisponível.",
        details: errorDetails ? (errorDetails.message || String(errorDetails)) : undefined,
        url: backendBaseUrl().toString()
      },
    },
    { status: 502 },
  );
}

export function generateCsrfToken(): string {
  return randomBytes(32).toString("base64url");
}

export function ensureCsrfToken(request: NextRequest): string {
  return request.cookies.get(AUTH_CSRF_COOKIE)?.value || generateCsrfToken();
}

export function setCsrfCookie(
  response: NextResponse,
  token: string,
): void {
  response.cookies.set(AUTH_CSRF_COOKIE, token, {
    httpOnly: false,
    secure: COOKIE_SECURE,
    sameSite: "lax",
    path: "/",
    maxAge: CSRF_MAX_AGE_SECONDS,
  });
}

export function setAuthCookies(
  response: NextResponse,
  tokens: TokenPair,
  csrfToken = generateCsrfToken(),
): void {
  response.cookies.set(AUTH_ACCESS_COOKIE, tokens.access, {
    httpOnly: true,
    secure: COOKIE_SECURE,
    sameSite: "lax",
    path: "/",
    maxAge: ACCESS_MAX_AGE_SECONDS,
  });
  response.cookies.set(AUTH_REFRESH_COOKIE, tokens.refresh, {
    httpOnly: true,
    secure: COOKIE_SECURE,
    sameSite: "lax",
    path: "/",
    maxAge: REFRESH_MAX_AGE_SECONDS,
  });
  setCsrfCookie(response, csrfToken);
}

export function clearAuthCookies(response: NextResponse): void {
  for (const cookieName of [
    AUTH_ACCESS_COOKIE,
    AUTH_REFRESH_COOKIE,
    AUTH_CSRF_COOKIE,
  ]) {
    response.cookies.set(cookieName, "", {
      httpOnly: cookieName !== AUTH_CSRF_COOKIE,
      secure: COOKIE_SECURE,
      sameSite: "lax",
      path: "/",
      maxAge: 0,
      expires: new Date(0),
    });
  }
}

export function getAccessCookie(request: NextRequest): string | null {
  return request.cookies.get(AUTH_ACCESS_COOKIE)?.value || null;
}

export function getRefreshCookie(request: NextRequest): string | null {
  return request.cookies.get(AUTH_REFRESH_COOKIE)?.value || null;
}

export function createBackendHeaders(
  request: NextRequest,
  accessToken?: string | null,
): Headers {
  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (accessToken) headers.set("authorization", `Bearer ${accessToken}`);
  headers.set("connection", "close");
  return headers;
}

export async function fetchBackend(
  path: string,
  init: StreamingRequestInit,
  search = "",
): Promise<Response> {
  const url = buildBackendUrl(path, search);
  return fetch(url, {
    ...init,
    cache: "no-store",
    redirect: "manual",
  });
}

export async function parseBackendJson(
  response: Response,
): Promise<JsonObject | null> {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes("application/json")) return null;

  try {
    const payload: unknown = await response.json();
    return payload && typeof payload === "object" && !Array.isArray(payload)
      ? (payload as JsonObject)
      : null;
  } catch {
    return null;
  }
}

export function extractTokenPair(payload: JsonObject): TokenPair | null {
  const nested = payload.tokens;
  const source =
    nested && typeof nested === "object" && !Array.isArray(nested)
      ? (nested as JsonObject)
      : payload;
  const access = source.access;
  const refresh = source.refresh;
  if (typeof access !== "string" || typeof refresh !== "string") return null;
  if (!access || !refresh) return null;
  return { access, refresh };
}

export function withoutTokenFields(payload: JsonObject): JsonObject {
  const sanitized = { ...payload };
  delete sanitized.access;
  delete sanitized.refresh;
  delete sanitized.tokens;
  return sanitized;
}

export async function backendResponseToNext(
  backendResponse: Response,
): Promise<NextResponse> {
  const headers = new Headers();
  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = backendResponse.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set("cache-control", "no-store");
  headers.set("x-content-type-options", "nosniff");

  const body =
    backendResponse.status === 204 || backendResponse.status === 304
      ? null
      : await backendResponse.arrayBuffer();
  return new NextResponse(body, {
    status: backendResponse.status,
    headers,
  });
}

export async function refreshTokenPair(
  request: NextRequest,
  refreshToken: string,
): Promise<{ response: Response; tokens: TokenPair | null; payload: JsonObject | null }> {
  const response = await fetchBackend("auth/token/refresh/", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "user-agent": request.headers.get("user-agent") || "",
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  const payload = await parseBackendJson(response);
  const tokens = payload ? extractTokenPair(payload) : null;
  return { response, tokens, payload };
}
