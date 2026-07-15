import { deleteCookie, getCookie } from "cookies-next";

import { AUTH_CSRF_COOKIE } from "@/lib/auth-constants";

export function getCsrfToken(): string | null {
  const value = getCookie(AUTH_CSRF_COOKIE);
  return typeof value === "string" && value ? value : null;
}

export function clearClientAuthState(): void {
  deleteCookie(AUTH_CSRF_COOKIE, { path: "/" });
}
