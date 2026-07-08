import type { Metadata } from "next";

import { BillingShell } from "@/features/billing/billing-shell";

export const metadata: Metadata = {
  title: "Pagamento pendente | Elo Terapêutico",
};

export default function BillingPendingPage() {
  return <BillingShell mode="pending" />;
}
