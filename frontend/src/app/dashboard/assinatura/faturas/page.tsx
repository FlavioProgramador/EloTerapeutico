import type { Metadata } from "next";

import { BillingShell } from "@/features/billing/billing-shell";

export const metadata: Metadata = {
  title: "Faturas | Elo Terapêutico",
};

export default function BillingPaymentsPage() {
  return <BillingShell mode="payments" />;
}
