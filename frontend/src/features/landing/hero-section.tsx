import Link from "next/link";

export function HeroSection() {
  return (
    <section id="conteudo" className="py-24">
      <h1>Sua clínica organizada. Seu cuidado no centro.</h1>
      <p>Centralize pacientes, agenda, prontuários e financeiro.</p>
      <Link href="/register">Criar minha conta</Link>
    </section>
  );
}
