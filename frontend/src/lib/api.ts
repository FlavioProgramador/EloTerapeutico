import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import {
  createSingleFlight,
  extractApiErrorMessage,
  prepareRetryRequest,
  type ApiErrorEnvelope,
} from "@/lib/auth-flow";
import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  persistAuthTokens,
} from "@/lib/auth-session";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/";

type RetriableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

const runRefreshSingleFlight = createSingleFlight<string>();
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

function refreshAccessToken(): Promise<string> {
  return runRefreshSingleFlight(async () => {
    const refresh = getRefreshToken();
    if (!refresh) {
      throw new Error("REFRESH_TOKEN_MISSING");
    }

    const response = await axios.post<{ access?: string; refresh?: string }>(
      `${API_URL}auth/token/refresh/`,
      { refresh },
    );
    const access = response.data.access;
    if (typeof access !== "string" || !access) {
      throw new Error("INVALID_REFRESH_RESPONSE");
    }
    persistAuthTokens(access, response.data.refresh || null);
    api.defaults.headers.common.Authorization = `Bearer ${access}`;
    return access;
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

    const isRefreshRequest = originalRequest?.url?.includes(
      "auth/token/refresh/",
    );
    const isLoginRequest = originalRequest?.url?.includes("auth/login/");
    if (
      rawError.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isRefreshRequest ||
      isLoginRequest
    ) {
      return Promise.reject(rawError);
    }

    originalRequest._retry = true;
    try {
      const access = await refreshAccessToken();
      prepareRetryRequest(
        originalRequest as unknown as {
          headers: Record<string, unknown>;
          data?: unknown;
        },
        access,
      );
      // Axios preserva data e headers customizados, inclusive Idempotency-Key.
      return api(originalRequest);
    } catch (refreshError) {
      clearAuthSession();
      redirectToLoginOnce();
      return Promise.reject(refreshError);
    }
  },
);
