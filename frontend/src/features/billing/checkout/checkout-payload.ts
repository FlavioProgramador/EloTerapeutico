import type {
  BillingType,
  CheckoutPayload,
  PlanPrice,
} from "../types";

interface CheckoutPayloadInput {
  selectedPrice?: PlanPrice;
  billingType: BillingType;
  cpfCnpj: string;
  name: string;
  phone: string;
  dueDate: string;
  installmentCount: number;
  idempotencyKey: string;
}

export function buildCheckoutPayload({
  selectedPrice,
  billingType,
  cpfCnpj,
  name,
  phone,
  dueDate,
  installmentCount,
  idempotencyKey,
}: CheckoutPayloadInput): CheckoutPayload | null {
  if (!selectedPrice) return null;
  return {
    plan_price_id: selectedPrice.id,
    billingType,
    cpfCnpj,
    name,
    phone,
    dueDate,
    installmentCount,
    description: `Elo Terapêutico — ${selectedPrice.name}`,
    idempotency_key: idempotencyKey,
  };
}
