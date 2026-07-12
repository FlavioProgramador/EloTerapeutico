import { deleteCookie, getCookie, setCookie } from "cookies-next";

export const AUTH_ACCESS_COOKIE = "auth_token";
export const AUTH_REFRESH_COOKIE = "auth_refresh_token";
export const AUTH_ROLE_COOKIE = "auth_role";

const secure = process.env.NODE_ENV === "production";
const commonOptions = {
  path: "/",
  sameSite: "lax" as const,
  secure,
};

export function getAccessToken(): string | null {
  const value = getCookie(AUTH_ACCESS_COOKIE);
  return typeof value === "string" && value ? value : null;
}

export function getRefreshToken(): string | null {
  const value = getCookie(AUTH_REFRESH_COOKIE);
  return typeof value === "string" && value ? value : null;
}

export function persistAuthTokens(access: string, refresh?: string | null): void {
  setCookie(AUTH_ACCESS_COOKIE, access, {
    ...commonOptions,
    maxAge: 30 * 60,
  });
  if (refresh) {
    setCookie(AUTH_REFRESH_COOKIE, refresh, {
      ...commonOptions,
      maxAge: 7 * 24 * 60 * 60,
    });
  }
}

export function persistAuthRole(role: string): void {
  setCookie(AUTH_ROLE_COOKIE, role, {
    ...commonOptions,
    maxAge: 7 * 24 * 60 * 60,
  });
}

export function clearAuthSession(): void {
  deleteCookie(AUTH_ACCESS_COOKIE, commonOptions);
  deleteCookie(AUTH_REFRESH_COOKIE, commonOptions);
  deleteCookie(AUTH_ROLE_COOKIE, commonOptions);
}
