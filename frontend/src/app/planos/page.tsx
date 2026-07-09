import type { Metadata } from "next";

import { BillingShell } from "@/features/billing/billing-shell";

export const metadata: Metadata = {
  title: "Planos | Elo Terapêutico",
  description: "Escolha um plano de assinatura para liberar os módulos do Elo Terapêutico.",
};

export default function PlansPage() {
  return <BillingShell mode="plans" />;
}
