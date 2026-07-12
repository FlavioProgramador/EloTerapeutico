import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  persistAuthTokens,
} from "@/lib/auth-session";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/";

type RetriableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

type ErrorEnvelope = {
  detail?: string;
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};

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

let refreshPromise: Promise<string> | null = null;
let redirectingToLogin = false;

function normalizeErrorEnvelope(error: AxiosError<ErrorEnvelope>): void {
  const payload = error.response?.data;
  if (payload && !payload.detail && payload.error?.message) {
    payload.detail = payload.error.message;
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

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  const refresh = getRefreshToken();
  if (!refresh) {
    throw new Error("REFRESH_TOKEN_MISSING");
  }

  refreshPromise = axios
    .post<{ access?: string; refresh?: string }>(`${API_URL}auth/token/refresh/`, { refresh })
    .then((response) => {
      const access = response.data.access;
      if (typeof access !== "string" || !access) {
        throw new Error("INVALID_REFRESH_RESPONSE");
      }
      persistAuthTokens(access, response.data.refresh || null);
      api.defaults.headers.common.Authorization = `Bearer ${access}`;
      return access;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (rawError: AxiosError<ErrorEnvelope>) => {
    normalizeErrorEnvelope(rawError);
    const originalRequest = rawError.config as RetriableRequest | undefined;

    if (rawError.response?.status === 402) {
      const code = String(rawError.response.data?.error?.code || "SUBSCRIPTION_REQUIRED");
      const isBillingRequest = String(originalRequest?.url || "").includes("billing/");
      if (typeof window !== "undefined" && !isBillingRequest) {
        const paymentRelated = [
          "PAYMENT_PENDING",
          "PAYMENT_PAST_DUE",
          "SUBSCRIPTION_SUSPENDED",
        ].includes(code);
        const target = paymentRelated ? "/billing" : "/planos";
        window.location.assign(`${target}?reason=${encodeURIComponent(code.toLowerCase())}`);
      }
      return Promise.reject(rawError);
    }

    const isRefreshRequest = originalRequest?.url?.includes("auth/token/refresh/");
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
      originalRequest.headers.Authorization = `Bearer ${access}`;
      // Axios preserva data e headers customizados, inclusive Idempotency-Key.
      return api(originalRequest);
    } catch (refreshError) {
      clearAuthSession();
      redirectToLoginOnce();
      return Promise.reject(refreshError);
    }
  },
);
