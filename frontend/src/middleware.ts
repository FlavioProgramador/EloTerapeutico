import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Rotas públicas que não necessitam de autenticação
const publicRoutes = ["/login", "/register", "/cadastro", "/forgot-password", "/planos"];

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // A presença do cookie só indica uma sessão candidata. A validade é confirmada
  // pelo frontend em /auth/me/ para evitar loops causados por tokens antigos.
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

  const isRegisterRoute = pathname.startsWith("/register") || pathname.startsWith("/cadastro");
  const selectedPlan =
    request.nextUrl.searchParams.get("plan") ||
    request.nextUrl.searchParams.get("plan_slug") ||
    request.nextUrl.searchParams.get("plan_price_slug") ||
    request.nextUrl.searchParams.get("plan_price_id");

  // Cadastro público só pode ser iniciado depois da seleção de um plano.
  if (!token && isRegisterRoute && !selectedPlan) {
    const plansUrl = new URL("/planos", request.url);
    plansUrl.searchParams.set("reason", "plan_required");
    return NextResponse.redirect(plansUrl);
  }

  const isPublicRoute = publicRoutes.some(
    (route) => pathname.startsWith(route) || pathname === route,
  );
  const isDashboardRoute = pathname.startsWith("/dashboard") || pathname === "/dashboard";
  const isCheckoutRoute = pathname.startsWith("/checkout") || pathname.startsWith("/billing");
  const isProtectedRoute = isDashboardRoute || isCheckoutRoute;

  // Usuário sem cookie tentando acessar rota protegida.
  if (!token && isProtectedRoute) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
  }

  // Login e cadastro não redirecionam apenas pela presença do cookie. Isso
  // permite que uma sessão expirada seja limpa sem loop login → dashboard.
  if (isPublicRoute) {
    return NextResponse.next();
  }

  // Controle RBAC de acesso para rotas do Dashboard. A API continua sendo a
  // autoridade final; este bloqueio é apenas uma proteção de navegação.
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
