import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Rotas públicas que não necessitam de autenticação
const publicRoutes = ["/login", "/register", "/forgot-password"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Obtém os cookies de autenticação
  const token = request.cookies.get("auth_token")?.value;
  const role = request.cookies.get("auth_role")?.value;

  // Verifica se é uma rota estática do Next.js, imagens ou favicon para ignorar o middleware
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/static") ||
    pathname.startsWith("/favicon.ico") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const isPublicRoute = publicRoutes.some((route) => pathname.startsWith(route) || pathname === route);
  const isDashboardRoute = pathname.startsWith("/dashboard") || pathname === "/dashboard";

  // Caso 1: Usuário NÃO autenticado tentando acessar rotas protegidas (Dashboard)
  if (!token && isDashboardRoute) {
    const loginUrl = new URL("/login", request.url);
    // Adiciona o parâmetro redirect para retornar o usuário à página de origem após o login
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Caso 2: Usuário JÁ autenticado tentando acessar páginas públicas de login/cadastro
  if (token && isPublicRoute) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Caso 3: Controle RBAC de acesso para rotas do Dashboard
  if (token && isDashboardRoute) {
    // 3a. Secretárias não têm acesso a nenhuma rota de prontuários clínicos (/dashboard/records/*)
    if (role === "secretary" && pathname.startsWith("/dashboard/records")) {
      const dashboardUrl = new URL("/dashboard", request.url);
      dashboardUrl.searchParams.set("error", "access_denied_records");
      return NextResponse.redirect(dashboardUrl);
    }

    // 3b. Apenas administradores acessam painéis de gestão interna da clínica (/dashboard/admin/*)
    if (role !== "admin" && pathname.startsWith("/dashboard/admin")) {
      const dashboardUrl = new URL("/dashboard", request.url);
      dashboardUrl.searchParams.set("error", "access_denied_admin");
      return NextResponse.redirect(dashboardUrl);
    }
  }

  return NextResponse.next();
}

// Define em quais caminhos o Middleware deve ser ativado
export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
