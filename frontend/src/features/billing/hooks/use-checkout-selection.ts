import { useMemo, useState } from "react";

import {
  chooseDefaultPrice,
  normalizeInstallmentCount,
} from "../checkout/checkout-rules";
import type { BillingInterval, Plan } from "../types";

export function useCheckoutSelection(
  plans: Plan[],
  selectedPlanSlug: string,
  requestedInterval: BillingInterval,
) {
  const [interval, setInterval] =
    useState<BillingInterval>(requestedInterval);
  const [selectedPriceId, setSelectedPriceId] = useState<number | null>(null);
  const [installmentCount, setInstallmentCount] = useState(1);

  const selectedPlan = useMemo(
    () => plans.find((plan) => plan.slug === selectedPlanSlug) || plans[0],
    [plans, selectedPlanSlug],
  );
  const intervalPrices = useMemo(
    () =>
      selectedPlan?.prices.filter(
        (price) => price.available && price.billing_interval === interval,
      ) || [],
    [interval, selectedPlan],
  );
  const selectedPrice = useMemo(
    () =>
      intervalPrices.find((price) => price.id === selectedPriceId) ||
      (selectedPlan ? chooseDefaultPrice(selectedPlan, interval) : undefined) ||
      intervalPrices[0],
    [interval, intervalPrices, selectedPlan, selectedPriceId],
  );
  const effectiveInstallmentCount = normalizeInstallmentCount(
    selectedPrice,
    installmentCount,
  );

  function changeInterval(nextInterval: BillingInterval) {
    setInterval(nextInterval);
    const price = selectedPlan
      ? chooseDefaultPrice(selectedPlan, nextInterval)
      : undefined;
    setSelectedPriceId(price?.id ?? null);
    setInstallmentCount(
      price?.billing_model === "INSTALLMENT" ? price.max_installments : 1,
    );
  }

  function selectPrice(priceId: number) {
    setSelectedPriceId(priceId);
    const price = intervalPrices.find((item) => item.id === priceId);
    setInstallmentCount(
      price?.billing_model === "INSTALLMENT" ? price.max_installments : 1,
    );
  }

  return {
    interval,
    selectedPlan,
    intervalPrices,
    selectedPrice,
    installmentCount: effectiveInstallmentCount,
    setInstallmentCount,
    changeInterval,
    selectPrice,
  };
}
