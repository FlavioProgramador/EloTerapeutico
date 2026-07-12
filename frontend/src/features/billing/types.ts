export type BillingInterval = "MONTHLY" | "YEARLY";
export type BillingModel = "RECURRING" | "ONE_TIME" | "INSTALLMENT";
export type SubscriptionStatus =
  | "TRIALING"
  | "PENDING"
  | "ACTIVE"
  | "PAST_DUE"
  | "SUSPENDED"
  | "CANCELED"
  | "EXPIRED";
export type PaymentStatus =
  | "PENDING"
  | "AUTHORIZED"
  | "CONFIRMED"
  | "RECEIVED"
  | "OVERDUE"
  | "FAILED"
  | "CANCELED"
  | "REFUNDED"
  | "PARTIALLY_REFUNDED"
  | "REFUND_IN_PROGRESS"
  | "CHARGEBACK"
  | "CHARGEBACK_DISPUTE"
  | "RESTORED"
  | "AWAITING_RISK_ANALYSIS";
export type BillingType = "PIX" | "BOLETO" | "CREDIT_CARD";

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

export interface PlanPrice {
  id: number;
  name: string;
  slug: string;
  currency: string;
  total_amount: string;
  billing_interval: BillingInterval;
  billing_model: BillingModel;
  discount_percentage: string;
  installments_enabled: boolean;
  min_installments: number;
  max_installments: number;
  installment_amount_from_max: string;
  trial_days: number;
  available: boolean;
}

export interface Plan {
  id: number;
  name: string;
  slug: string;
  description: string;
  max_patients: number | null;
  max_storage_mb: number | null;
  features: PlanFeatures;
  prices: PlanPrice[];
  price?: string;
  currency?: string;
  billing_cycle?: BillingInterval;
}

export interface BillingOrder {
  public_id: string;
  status: string;
  billing_model: BillingModel;
  billing_interval: BillingInterval;
  currency: string;
  total_amount: string;
  discount_amount: string;
  installment_count: number;
  installment_amount_estimate: string | null;
  paid_installments: number;
  next_due_date: string | null;
  plan_price: PlanPrice;
  confirmed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  id: number;
  plan: Plan;
  billing_order: BillingOrder | null;
  status: SubscriptionStatus;
  has_access: boolean;
  started_at: string | null;
  access_starts_at: string | null;
  access_ends_at: string | null;
  trial_ends_at: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  grace_period_ends_at: string | null;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  suspended_at: string | null;
  reactivated_at: string | null;
  gateway_name: string;
  gateway_status: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: number;
  order_public_id: string | null;
  amount: string;
  net_amount: string | null;
  interest_amount: string;
  fine_amount: string;
  discount_amount: string;
  currency: string;
  billing_type: BillingType | "UNDEFINED";
  status: PaymentStatus;
  due_date: string | null;
  original_due_date: string | null;
  paid_at: string | null;
  confirmed_at: string | null;
  credit_at: string | null;
  refunded_at: string | null;
  installment_number: number | null;
  installment_count: number;
  installment_label: string;
  invoice_number: string;
  invoice_url: string;
  bank_slip_url: string;
  transaction_receipt_url: string;
  pix_qr_code?: string;
  pix_copy_paste?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentSummary {
  total_amount: string;
  paid_amount: string;
  paid_installments: number;
  total_installments: number;
  next_due_date: string | null;
  overdue_installments: number;
}

export interface CheckoutPayload {
  plan_price_id: number;
  billingType: BillingType;
  cpfCnpj: string;
  name?: string;
  email?: string;
  phone?: string;
  dueDate: string;
  description?: string;
  installmentCount: number;
  creditCardToken?: string;
  idempotency_key?: string;
}

export interface CheckoutPreview {
  gateway: "ASAAS";
  environment: "SANDBOX" | "PRODUCTION";
  notice: string;
  activation_rule: string;
  plan: Plan;
  plan_price: PlanPrice;
  checkout: {
    billingType: BillingType;
    dueDate: string;
    description: string;
    billingModel: BillingModel;
    billingInterval: BillingInterval;
    totalAmount: string;
    installmentCount: number;
    installmentAmountEstimate: string;
    discountPercentage: string;
  };
  order?: BillingOrder;
  subscription?: Subscription;
  payments?: Payment[];
  status?: string;
  idempotent_replay?: boolean;
  payment_url?: string | null;
  invoice_url?: string | null;
  pix?: {
    copy_paste: string | null;
    qr_code: string | null;
  } | null;
}

export interface AsaasIntegrationHealth {
  gateway: "ASAAS";
  connected: boolean;
  configured: boolean;
  environment: "SANDBOX" | "PRODUCTION";
  detail: string;
  error_code: string | null;
  last_webhook_at: string | null;
  pending_events: number;
  failed_events: number;
}
