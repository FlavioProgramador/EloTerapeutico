import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import {
  AUTH_ACCESS_COOKIE,
  AUTH_REFRESH_COOKIE,
} from "@/lib/auth-constants";

const publicRoutes = [
  "/login",
  "/register",
  "/cadastro",
  "/forgot-password",
  "/planos",
  "/termos-de-uso",
  "/politica-de-privacidade",
];

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const hasSession = Boolean(
    request.cookies.get(AUTH_ACCESS_COOKIE)?.value ||
      request.cookies.get(AUTH_REFRESH_COOKIE)?.value,
  );

  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/static") ||
    pathname.startsWith("/favicon.ico") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const isPublicRoute = publicRoutes.some(
    (route) => pathname.startsWith(route) || pathname === route,
  );
  const isDashboardRoute =
    pathname.startsWith("/dashboard") || pathname === "/dashboard";
  const isCheckoutRoute =
    pathname.startsWith("/checkout") || pathname.startsWith("/billing");
  const isOnboardingRoute = pathname.startsWith("/onboarding");
  const isProtectedRoute =
    isDashboardRoute || isCheckoutRoute || isOnboardingRoute;

  if (!hasSession && isProtectedRoute) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
  }

  // Este middleware melhora apenas a navegação. Validade da sessão, role,
  // tenant, assinatura e object-level permissions são confirmados pelo backend.
  if (isPublicRoute) return NextResponse.next();

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
