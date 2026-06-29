import Link from "next/link";
import { Brand } from "./brand";

export function SiteFooter() {
  return (
    <footer className="landing-footer"><div><Brand /><p>Gestão integrada para profissionais que cuidam de pessoas.</p></div><nav aria-label="Links do rodapé"><a href="#produto">Produto</a><a href="#recursos">Recursos</a><a href="#seguranca">Segurança</a><a href="#faq">Perguntas</a><Link href="/login">Entrar</Link></nav><small>© {new Date().getFullYear()} Elo Terapêutico. Todos os direitos reservados.</small></footer>
  );
}
