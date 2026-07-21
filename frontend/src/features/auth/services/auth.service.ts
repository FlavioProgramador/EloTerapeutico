/**
 * Serviço de autenticação.
 * Credenciais são mantidas exclusivamente pelo BFF em cookies HttpOnly.
 */

import axios from "axios";

import { api } from "@/lib/api";
import { getCsrfToken } from "@/lib/auth-session";
import type { LoginCredentials, User } from "@/types";

interface AuthResponse {
  user?: User;
  message?: string;
  next?: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm: string;
  full_name: string;
  phone?: string;
  role?: "therapist" | "secretary" | "admin";
  crp?: string;
  specialty?: string;
  terms_accepted: boolean;
  privacy_accepted: boolean;
  plan?: string;
  plan_price_slug?: string;
  billing_cycle?: "MONTHLY" | "YEARLY";
  payment_mode?: "RECURRING" | "ONE_TIME" | "INSTALLMENT";
  access_mode?: "TRIAL" | "PAID";
}

function csrfHeaders(): Record<string, string> {
  const token = getCsrfToken();
  return token ? { "X-CSRF-Token": token } : {};
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await axios.post<AuthResponse>(
      "/api/auth/login/",
      credentials,
      { withCredentials: true },
    );
    return response.data;
  },

  logout: async (): Promise<void> => {
    await axios.post(
      "/api/auth/logout/",
      {},
      { withCredentials: true, headers: csrfHeaders() },
    );
  },

  logoutAll: async (): Promise<void> => {
    await axios.post(
      "/api/auth/logout-all/",
      {},
      { withCredentials: true, headers: csrfHeaders() },
    );
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>("auth/me/");
    return response.data;
  },

  refreshSession: async (): Promise<void> => {
    await axios.post(
      "/api/auth/refresh/",
      {},
      { withCredentials: true, headers: csrfHeaders() },
    );
  },

  register: async (data: RegisterPayload): Promise<AuthResponse> => {
    const response = await axios.post<AuthResponse>(
      "/api/auth/register/",
      data,
      { withCredentials: true },
    );
    return response.data;
  },

  requestPasswordReset: async (email: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>(
      "auth/password/reset/",
      { email },
    );
    return response.data;
  },

  confirmPasswordReset: async (data: {
    uidb64: string;
    token: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>(
      "auth/password/reset/confirm/",
      data,
    );
    return response.data;
  },
};
