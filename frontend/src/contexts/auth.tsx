"use client";

import axios from "axios";
import { useRouter } from "next/navigation";
import React, { createContext, useContext, useEffect, useState } from "react";

import {
  resolvePostLoginDestination,
  safeInternalPath,
  type AccessSubscriptionStatus,
} from "@/lib/auth-flow";
import { clearClientAuthState, getCsrfToken } from "@/lib/auth-session";
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
  clinic_name?: string;
  onboarding_completed?: boolean;
  default_session_value?: string;
}

interface SubscriptionSnapshot {
  status: AccessSubscriptionStatus;
  has_access: boolean;
}

interface EntitlementSnapshot {
  allowed: boolean;
  code: string;
  redirect_to?: string | null;
  onboarding_required?: boolean;
  subscription: SubscriptionSnapshot | null;
}

interface BrowserSessionSnapshot {
  authenticated: boolean;
  csrf_token: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  updateUser: (updatedUser: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function requestedPathFromQuery(): string {
  if (typeof window === "undefined") return "/dashboard";
  const params = new URLSearchParams(window.location.search);
  return safeInternalPath(params.get("next") || params.get("redirect"));
}

async function resolveRedirectAfterLogin(): Promise<string> {
  const requested = requestedPathFromQuery();
  try {
    const response = await api.get<EntitlementSnapshot>("billing/entitlement/");
    const entitlement = response.data;
    return resolvePostLoginDestination({
      requested,
      entitlementAllowed: entitlement.allowed,
      subscriptionStatus: entitlement.subscription?.status,
      entitlementRedirect: entitlement.redirect_to,
      onboardingRequired: entitlement.onboarding_required,
    });
  } catch {
    return resolvePostLoginDestination({
      requested,
      entitlementAllowed: false,
      subscriptionStatus: null,
      entitlementRedirect: "/planos",
      onboardingRequired: false,
    });
  }
}

async function readBrowserSession(): Promise<BrowserSessionSnapshot> {
  const response = await axios.get<BrowserSessionSnapshot>("/api/auth/session/", {
    withCredentials: true,
    headers: { Accept: "application/json" },
  });
  return response.data;
}

async function postAuthAction(path: string): Promise<void> {
  const csrfToken = getCsrfToken();
  if (!csrfToken) return;
  await axios.post(
    path,
    {},
    {
      withCredentials: true,
      headers: { "X-CSRF-Token": csrfToken },
    },
  );
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = Boolean(user);

  const fetchUserProfile = async (): Promise<User> => {
    const response = await api.get<User>("auth/me/");
    setUser(response.data);
    return response.data;
  };

  useEffect(() => {
    let mounted = true;
    const initAuth = async () => {
      try {
        const session = await readBrowserSession();
        if (!session.authenticated) return;
        await fetchUserProfile();
      } catch {
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
    setUser(null);
    try {
      await axios.post("/api/auth/login/", credentials, {
        withCredentials: true,
        headers: { "Content-Type": "application/json" },
      });
      await fetchUserProfile();
      router.replace(await resolveRedirectAfterLogin());
    } catch (error) {
      clearClientAuthState();
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await postAuthAction("/api/auth/logout/");
    } finally {
      clearClientAuthState();
      setUser(null);
      setIsLoading(false);
      router.replace("/login");
    }
  };

  const logoutAll = async () => {
    setIsLoading(true);
    try {
      await postAuthAction("/api/auth/logout-all/");
    } finally {
      clearClientAuthState();
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
        logoutAll,
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
