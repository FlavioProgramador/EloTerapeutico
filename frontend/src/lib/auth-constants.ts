export const AUTH_ACCESS_COOKIE = "elo_access";
export const AUTH_REFRESH_COOKIE = "elo_refresh";
export const AUTH_CSRF_COOKIE = "elo_csrf";

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export function isUnsafeHttpMethod(method: string): boolean {
  return UNSAFE_METHODS.has(method.toUpperCase());
}

export function isBlockedAuthProxyPath(path: string): boolean {
  const normalized = path.replace(/^\/+|\/+$/g, "").toLowerCase();
  return new Set([
    "auth/login",
    "auth/logout",
    "auth/logout-all",
    "auth/token/refresh",
  ]).has(normalized);
}
