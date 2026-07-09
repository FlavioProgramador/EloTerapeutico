import type { Metadata } from "next";

import { BillingShell } from "@/features/billing/billing-shell";

export const metadata: Metadata = {
  title: "Upgrade de plano | Elo Terapêutico",
};

export default function BillingUpgradePage() {
  return <BillingShell mode="upgrade" />;
}
