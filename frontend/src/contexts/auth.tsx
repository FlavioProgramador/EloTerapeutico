"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  persistAuthRole,
  persistAuthTokens,
} from "@/lib/auth-session";
import { api } from "@/lib/api";
import { LoginCredentials } from "@/types";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "therapist" | "secretary" | "admin";
  specialty?: string;
  crp?: string;
  phone?: string;
  default_session_value?: string;
}

interface SubscriptionSnapshot {
  status: "TRIALING" | "PENDING" | "ACTIVE" | "PAST_DUE" | "SUSPENDED" | "CANCELED" | "EXPIRED";
  has_access: boolean;
}

interface EntitlementSnapshot {
  allowed: boolean;
  code: string;
  redirect_to?: string | null;
  subscription: SubscriptionSnapshot | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (updatedUser: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function safeRedirectFromQuery(): string {
  if (typeof window === "undefined") return "/dashboard";
  const params = new URLSearchParams(window.location.search);
  const candidate = params.get("next") || params.get("redirect");
  if (candidate && candidate.startsWith("/") && !candidate.startsWith("//")) {
    return candidate;
  }
  return "/dashboard";
}

async function resolvePostLoginRedirect(): Promise<string> {
  const requested = safeRedirectFromQuery();
  const billingDestination = requested.startsWith("/checkout") || requested.startsWith("/billing");

  try {
    const response = await api.get<EntitlementSnapshot>("billing/entitlement/");
    const entitlement = response.data;
    if (entitlement.allowed) return requested;
    if (billingDestination) return requested;

    const status = entitlement.subscription?.status;
    if (status && ["PENDING", "PAST_DUE", "SUSPENDED"].includes(status)) {
      return "/billing";
    }
    return entitlement.redirect_to || "/planos";
  } catch {
    return billingDestination ? requested : "/planos";
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = Boolean(user);

  const fetchUserProfile = async (): Promise<User> => {
    const response = await api.get<User>("auth/me/");
    setUser(response.data);
    persistAuthRole(response.data.role);
    return response.data;
  };

  useEffect(() => {
    let mounted = true;
    const initAuth = async () => {
      if (!getAccessToken() && !getRefreshToken()) {
        if (mounted) setIsLoading(false);
        return;
      }
      try {
        await fetchUserProfile();
      } catch {
        clearAuthSession();
        if (mounted) setUser(null);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    void initAuth();
    return () => {
      mounted = false;
    };
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    clearAuthSession();
    setUser(null);
    try {
      const response = await api.post<{ access?: string; refresh?: string }>("auth/login/", credentials);
      const { access, refresh } = response.data;
      if (typeof access !== "string" || !access || typeof refresh !== "string" || !refresh) {
        throw new Error("Resposta de autenticação inválida.");
      }

      persistAuthTokens(access, refresh);
      await fetchUserProfile();
      const destination = await resolvePostLoginRedirect();
      router.replace(destination);
    } catch (error) {
      clearAuthSession();
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await api.post("auth/logout/", { refresh });
      }
    } catch (error) {
      console.error("Erro no logout no servidor:", error);
    } finally {
      clearAuthSession();
      setUser(null);
      setIsLoading(false);
      router.replace("/login");
    }
  };

  const updateUser = (updatedUser: Partial<User>) => {
    setUser((current) => (current ? { ...current, ...updatedUser } : current));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}
