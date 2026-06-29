import type { Metadata } from "next";
import { LandingPage } from "@/features/landing/landing-page";
import "@/features/landing/styles/landing.css";

export const metadata: Metadata = {
  title: "Elo Terapêutico | Gestão clínica integrada",
  description:
    "Centralize pacientes, agenda, prontuários e financeiro em uma plataforma criada para a rotina de psicólogos e terapeutas.",
};

export default function HomePage() {
  return <LandingPage />;
}
