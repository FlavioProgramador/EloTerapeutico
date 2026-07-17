import type { BillingInterval, Plan, PlanPrice } from "../types";

export function chooseDefaultPrice(
  plan: Plan,
  interval: BillingInterval,
): PlanPrice | undefined {
  const prices = plan.prices.filter(
    (price) => price.available && price.billing_interval === interval,
  );
  if (interval === "YEARLY") {
    return (
      prices.find((price) => price.billing_model === "INSTALLMENT") ||
      prices.find((price) => price.billing_model === "ONE_TIME") ||
      prices[0]
    );
  }
  return (
    prices.find((price) => price.billing_model === "RECURRING") || prices[0]
  );
}

export function normalizeInstallmentCount(
  price: PlanPrice | undefined,
  requestedCount: number,
) {
  if (!price || price.billing_model !== "INSTALLMENT") return 1;
  if (
    requestedCount < price.min_installments ||
    requestedCount > price.max_installments
  ) {
    return price.max_installments;
  }
  return requestedCount;
}

export function extractCheckoutError(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (
      error as {
        response?: {
          data?: {
            detail?: string;
            non_field_errors?: string[];
            error?: { details?: Record<string, string[]> };
          };
        };
      }
    ).response;
    if (response?.data?.detail) return response.data.detail;
    if (response?.data?.non_field_errors?.[0]) {
      return response.data.non_field_errors[0];
    }
    const details = response?.data?.error?.details;
    if (details) {
      return (
        Object.values(details).flat()[0] ||
        "Não foi possível concluir o checkout."
      );
    }
  }
  return "Não foi possível concluir o checkout.";
}
