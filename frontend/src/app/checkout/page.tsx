import type { Metadata } from "next";

import { CheckoutWizard } from "@/features/billing/checkout-wizard";

export const metadata: Metadata = {
  title: "Checkout | Elo Terapêutico",
  description: "Finalize sua assinatura de plano com cobrança processada pelo Asaas.",
};

export default function CheckoutPage() {
  return <CheckoutWizard />;
}
