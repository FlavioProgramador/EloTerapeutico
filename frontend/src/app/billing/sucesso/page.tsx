import type { Metadata } from "next";

import { BillingShell } from "@/features/billing/billing-shell";

export const metadata: Metadata = {
  title: "Assinatura | Elo Terapêutico",
};

export default function BillingSuccessPage() {
  return <BillingShell mode="success" />;
}
