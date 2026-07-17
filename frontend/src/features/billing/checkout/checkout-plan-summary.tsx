import { Check } from "lucide-react";

import { featureLabels } from "./checkout.constants";
import { formatCurrency } from "./checkout-formatters";
import type { Plan, PlanPrice } from "../types";

interface CheckoutPlanSummaryProps {
  plan: Plan;
  price: PlanPrice;
  installmentCount: number;
}

export function CheckoutPlanSummary({
  plan,
  price,
  installmentCount,
}: CheckoutPlanSummaryProps) {
  const count = price.billing_model === "INSTALLMENT" ? installmentCount : 1;

  return (
    <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
        Plano selecionado
      </span>
      <h2 className="mt-4 text-2xl font-bold">{plan.name}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        {plan.description}
      </p>
      <div className="mt-5">
        <strong className="text-3xl font-extrabold">
          {formatCurrency(price.total_amount, price.currency)}
        </strong>
        <span className="ml-1 text-xs text-muted-foreground">
          /{price.billing_interval === "MONTHLY" ? "mês" : "ano"}
        </span>
      </div>
      {count > 1 && (
        <p className="mt-2 text-sm font-semibold text-primary">
          {count}x de aproximadamente{" "}
          {formatCurrency(Number(price.total_amount) / count, price.currency)}
        </p>
      )}
      {Number(price.discount_percentage) > 0 && (
        <p className="mt-2 text-sm font-semibold text-success">
          Economia de {price.discount_percentage}%
        </p>
      )}
      <ul className="mt-5 space-y-2 text-sm text-muted-foreground">
        {Object.entries(plan.features)
          .filter(([, enabled]) => enabled)
          .slice(0, 7)
          .map(([key]) => (
            <li key={key} className="flex items-center gap-2">
              <Check className="h-4 w-4 text-primary" />
              {featureLabels[key] || key}
            </li>
          ))}
      </ul>
    </div>
  );
}
