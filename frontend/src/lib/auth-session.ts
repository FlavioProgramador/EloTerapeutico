import { deleteCookie, getCookie } from "cookies-next";

import { AUTH_CSRF_COOKIE } from "@/lib/auth-constants";

export function getCsrfToken(): string | null {
  const value = getCookie(AUTH_CSRF_COOKIE);
  return typeof value === "string" && value ? value : null;
}

export function clearClientAuthState(): void {
  deleteCookie(AUTH_CSRF_COOKIE, { path: "/" });
}

/**
 * Compatibilidade temporária com telas ainda não migradas.
 * Os JWTs já são persistidos exclusivamente pelo Route Handler em cookies HttpOnly.
 */
export function persistAuthTokens(
  access: string,
  refresh?: string | null,
): void {
  void access;
  void refresh;
  // Intencionalmente vazio: credenciais nunca são persistidas pelo JavaScript.
}

/**
 * Compatibilidade temporária. O papel do usuário é obtido de `auth/me/` e toda
 * autorização continua sendo aplicada pelo backend.
 */
export function persistAuthRole(role: string): void {
  void role;
  // Intencionalmente vazio: papel não é usado como cookie de autorização.
}
