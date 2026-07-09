import { Suspense } from "react";
import type { Metadata } from "next";
import { Loader2 } from "lucide-react";

import { CheckoutWizard } from "@/features/billing/checkout-wizard";

export const metadata: Metadata = {
  title: "Checkout | Elo Terapêutico",
  description: "Finalize sua assinatura de plano com cobrança processada pelo Asaas.",
};

function CheckoutFallback() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
        <Loader2 className="h-4 w-4 animate-spin" /> Carregando checkout Asaas...
      </div>
    </main>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<CheckoutFallback />}>
      <CheckoutWizard />
    </Suspense>
  );
}
