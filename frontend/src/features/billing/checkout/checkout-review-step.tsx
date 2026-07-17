import { Loader2 } from "lucide-react";

import type { CheckoutWizardController } from "../hooks/use-checkout-wizard";
import { billingModelLabels, billingTypeLabels } from "./checkout.constants";
import { formatCheckoutDate, formatCurrency } from "./checkout-formatters";
import { CheckoutReviewRow } from "./checkout-shared";

export function CheckoutReviewStep({
  controller,
}: {
  controller: CheckoutWizardController;
}) {
  const preview = controller.activePreview;
  if (!preview) return null;

  return (
    <div className="mt-8 space-y-5">
      <CheckoutReviewRow label="Plano" value={preview.plan.name} />
      <CheckoutReviewRow
        label="Modalidade"
        value={billingModelLabels[preview.checkout.billingModel]}
      />
      <CheckoutReviewRow
        label="Valor total"
        value={formatCurrency(
          preview.checkout.totalAmount,
          preview.plan_price.currency,
        )}
      />
      <CheckoutReviewRow
        label="Parcelamento"
        value={
          preview.checkout.installmentCount > 1
            ? `${preview.checkout.installmentCount}x de aproximadamente ${formatCurrency(preview.checkout.installmentAmountEstimate, preview.plan_price.currency)}`
            : "À vista"
        }
      />
      <CheckoutReviewRow
        label="Primeiro vencimento"
        value={formatCheckoutDate(preview.checkout.dueDate)}
      />
      <CheckoutReviewRow
        label="Forma de pagamento"
        value={billingTypeLabels[preview.checkout.billingType]}
      />
      <div className="rounded-2xl border border-warning/20 bg-warning-soft px-4 py-3 text-sm font-semibold text-warning">
        A contratação será criada como pendente e o acesso só será liberado
        após o webhook do Asaas.
      </div>
      <div className="flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={() => controller.setStep(1)}
          className="rounded-2xl border border-border px-5 py-3 text-sm font-bold hover:bg-muted"
        >
          Editar dados
        </button>
        <button
          type="button"
          onClick={controller.handleCreate}
          disabled={controller.submitting}
          className="inline-flex items-center justify-center rounded-2xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-60"
        >
          {controller.submitting && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          Confirmar contratação
        </button>
      </div>
    </div>
  );
}
