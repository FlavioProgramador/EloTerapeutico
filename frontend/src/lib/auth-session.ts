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
  _access: string,
  _refresh?: string | null,
): void {
  // Intencionalmente vazio: credenciais nunca são persistidas pelo JavaScript.
}

/**
 * Compatibilidade temporária. O papel do usuário é obtido de `auth/me/` e toda
 * autorização continua sendo aplicada pelo backend.
 */
export function persistAuthRole(_role: string): void {
  // Intencionalmente vazio: papel não é usado como cookie de autorização.
}
