import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import { getStoredOrganizationId } from "@/features/organizations/storage";
import {
  createSingleFlight,
  extractApiErrorMessage,
  type ApiErrorEnvelope,
} from "@/lib/auth-flow";
import { isUnsafeHttpMethod } from "@/lib/auth-constants";
import { clearClientAuthState, getCsrfToken } from "@/lib/auth-session";

const API_URL = "/api/backend/";

type RetriableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    Accept: "application/json",
  },
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    if (isUnsafeHttpMethod(config.method || "GET")) {
      const csrfToken = getCsrfToken();
      if (csrfToken) config.headers.set("X-CSRF-Token", csrfToken);
    }
    const organizationId = getStoredOrganizationId();
    if (organizationId) {
      config.headers.set("X-Organization-ID", organizationId);
    } else {
      config.headers.delete("X-Organization-ID");
    }
    config.headers.delete("Authorization");
    return config;
  },
  (error) => Promise.reject(error),
);

const runRefreshSingleFlight = createSingleFlight<void>();
let redirectingToLogin = false;

function normalizeErrorEnvelope(error: AxiosError<ApiErrorEnvelope>): void {
  const payload = error.response?.data;
  const message = extractApiErrorMessage(payload, "");
  if (payload && !payload.detail && message) {
    payload.detail = message;
  }
}

function redirectToLoginOnce(): void {
  if (typeof window === "undefined" || redirectingToLogin) return;
  redirectingToLogin = true;
  const current = `${window.location.pathname}${window.location.search}`;
  const login = new URL("/login", window.location.origin);
  if (!current.startsWith("/login")) {
    login.searchParams.set("next", current);
  }
  window.location.replace(`${login.pathname}${login.search}`);
}

function refreshSession(): Promise<void> {
  return runRefreshSingleFlight(async () => {
    const csrfToken = getCsrfToken();
    if (!csrfToken) throw new Error("CSRF_TOKEN_MISSING");

    await axios.post(
      "/api/auth/refresh/",
      {},
      {
        withCredentials: true,
        headers: { "X-CSRF-Token": csrfToken },
      },
    );
  });
}

api.interceptors.response.use(
  (response) => response,
  async (rawError: AxiosError<ApiErrorEnvelope>) => {
    normalizeErrorEnvelope(rawError);
    const originalRequest = rawError.config as RetriableRequest | undefined;

    if (rawError.response?.status === 402) {
      const code = String(
        rawError.response.data?.error?.code || "SUBSCRIPTION_REQUIRED",
      );
      const isBillingRequest = String(originalRequest?.url || "").includes(
        "billing/",
      );
      if (typeof window !== "undefined" && !isBillingRequest) {
        let target = "/planos";
        if (code === "PAYMENT_PENDING") {
          target = "/billing/pending";
        } else if (
          code === "PAYMENT_PAST_DUE" ||
          code === "SUBSCRIPTION_SUSPENDED"
        ) {
          target = "/billing/past-due";
        } else if (
          code === "TRIAL_EXPIRED" ||
          code === "SUBSCRIPTION_EXPIRED" ||
          code === "SUBSCRIPTION_CANCELED"
        ) {
          target = "/billing/expired";
        }
        window.location.assign(
          `${target}?reason=${encodeURIComponent(code.toLowerCase())}`,
        );
      }
      return Promise.reject(rawError);
    }

    if (
      rawError.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry
    ) {
      return Promise.reject(rawError);
    }

    originalRequest._retry = true;
    try {
      await refreshSession();
      originalRequest.headers.delete("Authorization");
      return api(originalRequest);
    } catch (refreshError) {
      clearClientAuthState();
      redirectToLoginOnce();
      return Promise.reject(refreshError);
    }
  },
);
