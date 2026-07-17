import type { CheckoutWizardController } from "../hooks/use-checkout-wizard";
import type { BillingInterval } from "../types";
import { billingModelLabels } from "./checkout.constants";
import { formatCurrency } from "./checkout-formatters";

export function CheckoutPlanOptions({
  controller,
}: {
  controller: CheckoutWizardController;
}) {
  const { selectedPlan, selectedPrice } = controller;
  if (!selectedPlan || !selectedPrice) return null;

  return (
    <>
      <div>
        <span className="text-sm font-semibold">Período do plano</span>
        <div className="mt-3 grid grid-cols-2 gap-2 rounded-2xl bg-muted/50 p-1.5">
          {(["MONTHLY", "YEARLY"] as BillingInterval[]).map((item) => {
            const enabled = selectedPlan.prices.some(
              (price) =>
                price.available && price.billing_interval === item,
            );
            return (
              <button
                key={item}
                type="button"
                disabled={!enabled}
                onClick={() => controller.changeInterval(item)}
                className={`rounded-xl px-4 py-3 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-40 ${controller.interval === item ? "bg-card text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
              >
                {item === "MONTHLY" ? "Mensal" : "Anual"}
              </button>
            );
          })}
        </div>
      </div>

      {controller.intervalPrices.length > 1 && (
        <div>
          <span className="text-sm font-semibold">Modalidade</span>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {controller.intervalPrices.map((price) => (
              <button
                key={price.id}
                type="button"
                onClick={() => controller.selectPrice(price.id)}
                className={`rounded-2xl border p-4 text-left transition ${selectedPrice.id === price.id ? "border-primary bg-primary/10" : "border-border bg-background hover:border-primary/30"}`}
              >
                <span className="block text-sm font-bold">
                  {billingModelLabels[price.billing_model]}
                </span>
                <span className="mt-1 block text-sm text-muted-foreground">
                  {formatCurrency(price.total_amount, price.currency)}
                  {price.billing_model === "INSTALLMENT" &&
                    ` em até ${price.max_installments}x`}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
