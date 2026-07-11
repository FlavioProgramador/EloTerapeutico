import axios from "axios";
import { getCookie, setCookie, deleteCookie } from "cookies-next";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = getCookie("auth_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 402) {
      const code = String(error.response?.data?.error?.code || "SUBSCRIPTION_REQUIRED");
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
      return Promise.reject(error);
    }

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("auth/login") &&
      !originalRequest.url?.includes("auth/token/refresh")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getCookie("auth_refresh_token");

      if (!refreshToken) {
        isRefreshing = false;
        deleteCookie("auth_token");
        deleteCookie("auth_refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_URL}auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access, refresh } = response.data;

        setCookie("auth_token", access, {
          maxAge: 30 * 60,
          path: "/",
          sameSite: "lax",
        });

        if (refresh) {
          setCookie("auth_refresh_token", refresh, {
            maxAge: 7 * 24 * 60 * 60,
            path: "/",
            sameSite: "lax",
          });
        }

        api.defaults.headers.common["Authorization"] = `Bearer ${access}`;
        originalRequest.headers["Authorization"] = `Bearer ${access}`;

        processQueue(null, access);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;

        deleteCookie("auth_token");
        deleteCookie("auth_refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);
