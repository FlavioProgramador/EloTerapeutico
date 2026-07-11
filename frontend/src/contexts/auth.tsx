"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCookie, setCookie, deleteCookie } from "cookies-next";
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

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (updatedUser: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function safeRedirectFromQuery() {
  if (typeof window === "undefined") return "/dashboard";
  const params = new URLSearchParams(window.location.search);
  const candidate = params.get("next") || params.get("redirect");
  if (candidate && candidate.startsWith("/") && !candidate.startsWith("//")) {
    return candidate;
  }
  return "/dashboard";
}

async function resolvePostLoginRedirect() {
  const requested = safeRedirectFromQuery();

  // Checkout e gestão da cobrança precisam permanecer acessíveis mesmo antes
  // da ativação do plano.
  if (requested.startsWith("/checkout") || requested.startsWith("/billing")) {
    return requested;
  }

  try {
    const response = await api.get<{ subscription: SubscriptionSnapshot | null }>(
      "billing/subscription/me/",
    );
    const subscription = response.data.subscription;
    if (subscription?.has_access) return requested;
    if (
      subscription &&
      ["PENDING", "PAST_DUE", "SUSPENDED"].includes(subscription.status)
    ) {
      return "/billing";
    }
    return "/planos";
  } catch {
    return "/planos";
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user;

  const fetchUserProfile = async () => {
    try {
      const response = await api.get("auth/me/");
      setUser(response.data);
      setCookie("auth_role", response.data.role, {
        maxAge: 7 * 24 * 60 * 60,
        path: "/",
        sameSite: "lax",
      });
    } catch (error) {
      console.error("Falha ao buscar perfil do usuário:", error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = getCookie("auth_token");
    const initAuth = async () => {
      if (token) {
        await fetchUserProfile();
      } else {
        setIsLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
      const response = await api.post("auth/login/", credentials);
      const { access, refresh, user: userData } = response.data;

      setCookie("auth_token", access, {
        maxAge: 30 * 60,
        path: "/",
        sameSite: "lax",
      });

      setCookie("auth_refresh_token", refresh, {
        maxAge: 7 * 24 * 60 * 60,
        path: "/",
        sameSite: "lax",
      });

      if (userData) {
        setUser(userData);
        setCookie("auth_role", userData.role, {
          maxAge: 7 * 24 * 60 * 60,
          path: "/",
          sameSite: "lax",
        });
      } else {
        await fetchUserProfile();
      }

      const destination = await resolvePostLoginRedirect();
      setIsLoading(false);
      router.push(destination);
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      const refreshToken = getCookie("auth_refresh_token");
      if (refreshToken) {
        await api.post("auth/logout/", { refresh: refreshToken });
      }
    } catch (error) {
      console.error("Erro no logout no servidor:", error);
    } finally {
      deleteCookie("auth_token", { path: "/" });
      deleteCookie("auth_refresh_token", { path: "/" });
      deleteCookie("auth_role", { path: "/" });
      setUser(null);
      setIsLoading(false);
      router.push("/login");
    }
  };

  const updateUser = (updatedUser: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...updatedUser });
    }
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
