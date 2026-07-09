export type BillingCycle = "MONTHLY" | "YEARLY";
export type SubscriptionStatus = "TRIALING" | "PENDING" | "ACTIVE" | "PAST_DUE" | "CANCELED" | "EXPIRED";
export type PaymentStatus = "PENDING" | "CONFIRMED" | "RECEIVED" | "OVERDUE" | "REFUNDED" | "CANCELED" | "FAILED";

export interface PlanFeatures {
  agenda: boolean;
  patients: boolean;
  clinical_records: boolean;
  financial: boolean;
  documents: boolean;
  forms: boolean;
  reports: boolean;
  ai: boolean;
}

export interface Plan {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: string;
  currency: string;
  billing_cycle: BillingCycle;
  max_patients: number | null;
  max_storage_mb: number | null;
  features: PlanFeatures;
}

export interface Subscription {
  id: number;
  plan: Plan;
  status: SubscriptionStatus;
  started_at: string | null;
  trial_ends_at: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  canceled_at: string | null;
  gateway_name: string;
  gateway_status: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: number;
  amount: string;
  currency: string;
  status: PaymentStatus;
  due_date: string | null;
  paid_at: string | null;
  invoice_url: string;
  bank_slip_url: string;
  created_at: string;
}
