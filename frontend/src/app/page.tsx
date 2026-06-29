import type { Metadata } from "next";
import { LandingPage } from "@/features/landing/landing-page";
import "@/features/landing/styles/landing.css";

export const metadata: Metadata = {
  title: "Elo Terapêutico | Gestão para psicólogos e terapeutas",
  description:
    "Centralize pacientes, agenda, prontuários e financeiro em uma plataforma criada para a rotina de psicólogos, terapeutas e equipes clínicas.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Elo Terapêutico | Gestão clínica integrada",
    description:
      "Uma experiência conectada para organizar pacientes, atendimentos, registros clínicos e financeiro.",
    type: "website",
    locale: "pt_BR",
  },
};

export default function HomePage() {
  return <LandingPage />;
}
