import { timingSafeEqual } from "node:crypto";

export const AUTH_GATEWAY_PUBLIC_ERROR = {
  code: "AUTH_GATEWAY_UNAVAILABLE",
  message: "O serviço de autenticação está temporariamente indisponível.",
} as const;

const SAFE_REQUEST_ID = /^[A-Za-z0-9._:-]{1,128}$/;
const TRUSTED_FETCH_SITES = new Set(["same-origin", "same-site", "none"]);

export interface GatewayUnavailablePayload {
  error: typeof AUTH_GATEWAY_PUBLIC_ERROR;
  request_id: string;
}

export interface GatewayUnavailableLog {
  event: "auth_gateway_unavailable";
  request_id: string;
  error_type: string;
}

export function shouldUseSecureCookies(
  nodeEnv: string | undefined = process.env.NODE_ENV,
  ci: string | undefined = process.env.CI,
  allowInsecureCiCookies: string | undefined =
    process.env.AUTH_ALLOW_INSECURE_COOKIES_FOR_TESTS,
): boolean {
  if (nodeEnv !== "production") return false;
  const explicitCiOverride =
    ci === "true" && allowInsecureCiCookies === "true";
  return !explicitCiOverride;
}

export function sanitizeRequestId(value: string | null | undefined): string | null {
  const normalized = value?.trim();
  if (!normalized || !SAFE_REQUEST_ID.test(normalized)) return null;
  return normalized;
}

export function isTrustedOriginValue(
  origin: string | null,
  requestOrigin: string,
  fetchSite: string | null,
): boolean {
  if (origin) {
    try {
      return new URL(origin).origin === requestOrigin;
    } catch {
      return false;
    }
  }

  return fetchSite === null || TRUSTED_FETCH_SITES.has(fetchSite);
}

export function csrfTokensMatch(
  cookieToken: string | null | undefined,
  headerToken: string | null | undefined,
): boolean {
  if (!cookieToken || !headerToken) return false;
  const cookieBuffer = Buffer.from(cookieToken);
  const headerBuffer = Buffer.from(headerToken);
  if (cookieBuffer.length !== headerBuffer.length) return false;
  return timingSafeEqual(cookieBuffer, headerBuffer);
}

export function gatewayUnavailablePayload(
  requestId: string,
): GatewayUnavailablePayload {
  return {
    error: AUTH_GATEWAY_PUBLIC_ERROR,
    request_id: requestId,
  };
}

export function gatewayUnavailableLog(
  requestId: string,
  error?: unknown,
): GatewayUnavailableLog {
  return {
    event: "auth_gateway_unavailable",
    request_id: requestId,
    error_type:
      error instanceof Error && error.name
        ? error.name
        : error === undefined
          ? "UnknownError"
          : typeof error,
  };
}
