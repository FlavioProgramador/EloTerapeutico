export type AccessSubscriptionStatus =
  | "TRIALING"
  | "PENDING"
  | "ACTIVE"
  | "PAST_DUE"
  | "SUSPENDED"
  | "CANCELED"
  | "EXPIRED";

export interface ApiErrorEnvelope {
  detail?: string;
  non_field_errors?: unknown[];
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
}

export function safeInternalPath(
  candidate: string | null | undefined,
  fallback = "/dashboard",
): string {
  if (!candidate || !candidate.startsWith("/") || candidate.startsWith("//")) {
    return fallback;
  }
  return candidate;
}

export function resolvePostLoginDestination(input: {
  requested: string;
  entitlementAllowed: boolean;
  subscriptionStatus?: AccessSubscriptionStatus | null;
  entitlementRedirect?: string | null;
}): string {
  const requested = safeInternalPath(input.requested);
  const billingDestination =
    requested.startsWith("/checkout") || requested.startsWith("/billing");

  if (input.entitlementAllowed || billingDestination) {
    return requested;
  }

  if (
    input.subscriptionStatus &&
    ["PENDING", "PAST_DUE", "SUSPENDED"].includes(input.subscriptionStatus)
  ) {
    return "/billing";
  }

  return safeInternalPath(input.entitlementRedirect, "/planos");
}

function firstDetail(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return value;
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = firstDetail(item);
      if (found) return found;
    }
  }
  if (value && typeof value === "object") {
    for (const item of Object.values(value as Record<string, unknown>)) {
      const found = firstDetail(item);
      if (found) return found;
    }
  }
  return null;
}

export function extractApiErrorMessage(
  payload: ApiErrorEnvelope | null | undefined,
  fallback: string,
): string {
  if (typeof payload?.error?.message === "string" && payload.error.message.trim()) {
    return payload.error.message;
  }
  if (typeof payload?.detail === "string" && payload.detail.trim()) {
    return payload.detail;
  }
  const nonField = firstDetail(payload?.non_field_errors);
  if (nonField) return nonField;
  const fieldDetail = firstDetail(payload?.error?.details);
  return fieldDetail || fallback;
}

export function createSingleFlight<T>(): (
  factory: () => Promise<T>,
) => Promise<T> {
  let active: Promise<T> | null = null;

  return (factory) => {
    if (active) return active;
    active = factory().finally(() => {
      active = null;
    });
    return active;
  };
}

export function prepareRetryRequest<T extends {
  headers: Record<string, unknown>;
  data?: unknown;
}>(request: T, accessToken: string): T {
  request.headers.Authorization = `Bearer ${accessToken}`;
  return request;
}
