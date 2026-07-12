import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

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
  const token = request.cookies.get("auth_token")?.value;
  const role = request.cookies.get("auth_role")?.value;

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
  const isDashboardRoute = pathname.startsWith("/dashboard") || pathname === "/dashboard";
  const isCheckoutRoute = pathname.startsWith("/checkout") || pathname.startsWith("/billing");
  const isOnboardingRoute = pathname.startsWith("/onboarding");
  const isProtectedRoute = isDashboardRoute || isCheckoutRoute || isOnboardingRoute;

  if (!token && isProtectedRoute) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
  }

  // A validade do cookie e o estado da assinatura são confirmados pelas APIs.
  // Assim, login/cadastro permanecem acessíveis para limpar sessões expiradas.
  if (isPublicRoute) {
    return NextResponse.next();
  }

  if (token && isDashboardRoute) {
    if (role === "secretary" && pathname.startsWith("/dashboard/records")) {
      const dashboardUrl = new URL("/dashboard", request.url);
      dashboardUrl.searchParams.set("error", "access_denied_records");
      return NextResponse.redirect(dashboardUrl);
    }

    if (role !== "admin" && pathname.startsWith("/dashboard/admin")) {
      const dashboardUrl = new URL("/dashboard", request.url);
      dashboardUrl.searchParams.set("error", "access_denied_admin");
      return NextResponse.redirect(dashboardUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
