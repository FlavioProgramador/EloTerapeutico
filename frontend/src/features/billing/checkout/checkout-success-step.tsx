import { ShieldCheck } from "lucide-react";
import Link from "next/link";

import type { CheckoutWizardController } from "../hooks/use-checkout-wizard";

export function CheckoutSuccessStep({
  controller,
}: {
  controller: CheckoutWizardController;
}) {
  const result = controller.result;
  if (!result) return null;

  return (
    <div className="mt-8 rounded-3xl border border-primary/20 bg-primary/5 p-6">
      <div className="flex items-start gap-3">
        <div className="rounded-2xl bg-primary/10 p-2 text-primary">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-bold">
            Contratação criada com segurança
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            {result.payments?.length
              ? `${result.payments.length} fatura(s) já foram sincronizadas. Acompanhe cada parcela na área de faturas.`
              : "A contratação está aguardando a primeira cobrança gerada pelo Asaas."}
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              href="/dashboard/assinatura/faturas"
              className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground"
            >
              Ver minhas faturas
            </Link>
            {result.payments?.[0]?.invoice_url && (
              <a
                href={result.payments[0].invoice_url}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-border px-5 py-2.5 text-sm font-bold hover:bg-muted"
              >
                Abrir primeira cobrança
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
