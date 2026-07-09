import { api } from "@/lib/api";
import type { CheckoutPayload, CheckoutPreview, Payment, Plan, Subscription } from "./types";

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function listPlans(): Promise<Plan[]> {
  const response = await api.get<Paginated<Plan> | Plan[]>("billing/plans/");
  return Array.isArray(response.data) ? response.data : response.data.results;
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
  const response = await api.post<CheckoutPreview>("billing/checkout/create/", payload);
  return response.data;
}

export async function createSubscription(planId: number): Promise<Subscription> {
  const response = await api.post<Subscription>("billing/subscription/create/", { plan_id: planId });
  return response.data;
}

export async function changePlan(planId: number): Promise<Subscription> {
  const response = await api.post<Subscription>("billing/subscription/change-plan/", { plan_id: planId });
  return response.data;
}

export async function cancelSubscription(): Promise<Subscription> {
  const response = await api.post<Subscription>("billing/subscription/cancel/");
  return response.data;
}

export async function listPayments(): Promise<Payment[]> {
  const response = await api.get<Paginated<Payment> | Payment[]>("billing/payments/");
  return Array.isArray(response.data) ? response.data : response.data.results;
}
