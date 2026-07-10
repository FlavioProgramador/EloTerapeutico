import type { Metadata } from "next";

import { BillingIntegrationHealth } from "@/features/billing/integration-health";

export const metadata: Metadata = {
  title: "Integrações | Elo Terapêutico",
  description: "Saúde operacional das integrações de cobrança do Elo Terapêutico.",
};

export default function IntegrationsPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 md:px-8">
      <div>
        <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
          Administração
        </span>
        <h1 className="mt-4 text-3xl font-bold text-foreground">Integrações</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Monitore a conectividade do gateway, os webhooks pendentes e as falhas que exigem reconciliação.
        </p>
      </div>
      <BillingIntegrationHealth />
    </div>
  );
}
