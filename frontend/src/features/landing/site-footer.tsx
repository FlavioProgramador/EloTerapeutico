import Link from "next/link";
import { ArrowUpRight, ShieldCheck } from "lucide-react";
import { Brand } from "./brand";

const columns = [
  {
    title: "Produto",
    links: [
      ["Funcionalidades", "#produto"],
      ["Como funciona", "#fluxo"],
      ["Módulos", "#modulos"],
      ["Segurança", "#seguranca"],
    ],
  },
  {
    title: "Acesso",
    links: [
      ["Entrar", "/login"],
      ["Testar grátis", "/register"],
      ["Recuperar senha", "/forgot-password"],
    ],
  },
  {
    title: "Suporte",
    links: [
      ["Perguntas frequentes", "#faq"],
      ["Demonstração do produto", "#produto"],
    ],
  },
] as const;

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__glow" aria-hidden="true" />
      <div className="site-footer__inner">
        <div className="site-footer__brand">
          <Brand />
          <p>
            Gestão integrada para psicólogos, terapeutas e equipes que precisam
            organizar cuidado clínico e operação em um só ambiente.
          </p>
          <small>
            O projeto está em evolução contínua. Informações comerciais e
            documentos legais serão publicados antes da disponibilização
            comercial.
          </small>
        </div>

        <div className="site-footer__columns">
          {columns.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <strong>{column.title}</strong>
              {column.links.map(([label, href]) =>
                href.startsWith("/") ? (
                  <Link key={label} href={href}>
                    {label}
                    <ArrowUpRight aria-hidden="true" />
                  </Link>
                ) : (
                  <a key={label} href={href}>
                    {label}
                    <ArrowUpRight aria-hidden="true" />
                  </a>
                ),
              )}
            </nav>
          ))}
        </div>
      </div>

      <div className="site-footer__bottom">
        <span>© {new Date().getFullYear()} Elo Terapêutico.</span>
        <span className="site-footer__lgpd">
          <ShieldCheck aria-hidden="true" />
          Em conformidade com a LGPD
        </span>
        <span>Produto digital em desenvolvimento.</span>
      </div>
    </footer>
  );
}
