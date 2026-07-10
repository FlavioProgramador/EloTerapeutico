import { api } from "@/lib/api";
import type {
  AsaasIntegrationHealth,
  BillingOrder,
  CheckoutPayload,
  CheckoutPreview,
  Payment,
  PaymentSummary,
  Plan,
  PlanPrice,
  Subscription,
} from "./types";

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

function unwrap<T>(data: Paginated<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results;
}

export async function listPlans(): Promise<Plan[]> {
  const response = await api.get<Paginated<Plan> | Plan[]>("billing/plans/");
  return unwrap(response.data);
}

export async function listPlanPrices(params?: {
  plan?: string;
  billing_interval?: string;
  billing_model?: string;
}): Promise<PlanPrice[]> {
  const response = await api.get<Paginated<PlanPrice> | PlanPrice[]>("billing/plan-prices/", { params });
  return unwrap(response.data);
}

export async function getMySubscription(): Promise<Subscription | null> {
  const response = await api.get<{ subscription: Subscription | null }>("billing/subscription/me/");
  return response.data.subscription;
}

export async function previewCheckout(payload: CheckoutPayload): Promise<CheckoutPreview> {
  const response = await api.post<CheckoutPreview>("billing/checkout/preview/", payload);
  return response.data;
}

export async function createCheckout(payload: CheckoutPayload): Promise<CheckoutPreview> {
  const idempotencyKey = payload.idempotency_key || crypto.randomUUID();
  const response = await api.post<CheckoutPreview>(
    "billing/checkout/create/",
    { ...payload, idempotency_key: idempotencyKey },
    { headers: { "Idempotency-Key": idempotencyKey } },
  );
  return response.data;
}

export async function createSubscription(planId: number): Promise<Subscription> {
  const response = await api.post<Subscription>("billing/subscription/create/", { plan_id: planId });
  return response.data;
}

export async function changePlan(planId: number): Promise<{ subscription: Subscription; detail: string }> {
  const response = await api.post<{ subscription: Subscription; detail: string }>(
    "billing/subscription/change-plan/",
    { plan_id: planId },
  );
  return response.data;
}

export async function cancelSubscription(): Promise<Subscription> {
  const response = await api.post<Subscription>("billing/subscription/cancel/");
  return response.data;
}

export async function scheduleCancellation(): Promise<Subscription> {
  const response = await api.post<Subscription>("billing/subscription/cancel-at-period-end/");
  return response.data;
}

export async function resumeSubscription(): Promise<Subscription> {
  const response = await api.post<Subscription>("billing/subscription/resume/");
  return response.data;
}

export async function listOrders(): Promise<BillingOrder[]> {
  const response = await api.get<Paginated<BillingOrder> | BillingOrder[]>("billing/orders/");
  return unwrap(response.data);
}

export async function getOrder(publicId: string): Promise<BillingOrder> {
  const response = await api.get<BillingOrder>(`billing/orders/${publicId}/`);
  return response.data;
}

export async function listPayments(params?: {
  status?: string;
  order?: string;
  ordering?: string;
}): Promise<Payment[]> {
  const response = await api.get<Paginated<Payment> | Payment[]>("billing/payments/", { params });
  return unwrap(response.data);
}

export async function getPaymentSummary(order?: string): Promise<PaymentSummary> {
  const response = await api.get<PaymentSummary>("billing/payments/summary/", {
    params: order ? { order } : undefined,
  });
  return response.data;
}

export async function refreshPayment(paymentId: number): Promise<Payment> {
  const response = await api.post<Payment>(`billing/payments/${paymentId}/refresh/`);
  return response.data;
}

export async function getAsaasIntegrationHealth(): Promise<AsaasIntegrationHealth> {
  const response = await api.get<AsaasIntegrationHealth>("billing/integrations/asaas/health/");
  return response.data;
}
