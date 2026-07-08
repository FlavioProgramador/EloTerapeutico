import type { Metadata } from "next";
import { LandingPage } from "@/features/landing/landing-page";
import "@/features/landing/styles/landing.css";

export const metadata: Metadata = {
  title: "Elo Terapêutico | Gestão completa para terapeutas",
  description:
    "Organize agenda, prontuários, pacientes e financeiro em uma só plataforma. Feita para psicólogos, psicanalistas e terapeutas que querem mais tempo para cuidar.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Elo Terapêutico | Gestão completa para terapeutas",
    description:
      "Agenda, prontuários eletrônicos, financeiro e conformidade com LGPD — tudo conectado em uma plataforma feita para terapeutas.",
    type: "website",
    locale: "pt_BR",
  },
};

export default function HomePage() {
  return <LandingPage />;
}
