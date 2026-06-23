"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCookie, setCookie, deleteCookie } from "cookies-next";
import { api } from "@/lib/api";

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

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: any) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (updatedUser: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user;

  // Busca as informações do perfil do usuário logado
  const fetchUserProfile = async () => {
    try {
      const response = await api.get("auth/me/");
      setUser(response.data);
      // Salva a role em cookie para o Middleware ler
      setCookie("auth_role", response.data.role, {
        maxAge: 7 * 24 * 60 * 60, // 7 dias
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

  // Efeito de inicialização: roda apenas no cliente para recuperar a sessão
  useEffect(() => {
    const token = getCookie("auth_token");
    if (token) {
      fetchUserProfile();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (credentials: any) => {
    setIsLoading(true);
    try {
      const response = await api.post("auth/login/", credentials);
      const { access, refresh, user: userData } = response.data;

      // Armazena os tokens nos cookies de forma segura
      setCookie("auth_token", access, {
        maxAge: 30 * 60, // 30 minutos
        path: "/",
        sameSite: "lax",
      });

      setCookie("auth_refresh_token", refresh, {
        maxAge: 7 * 24 * 60 * 60, // 7 dias
        path: "/",
        sameSite: "lax",
      });

      // Se o login já retornou as informações de usuário
      if (userData) {
        setUser(userData);
        setCookie("auth_role", userData.role, {
          maxAge: 7 * 24 * 60 * 60,
          path: "/",
          sameSite: "lax",
        });
      } else {
        // Fallback caso não retorne o user no payload do login
        await fetchUserProfile();
      }

      router.push("/dashboard");
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
        // Envia requisição de logout para o backend invalidar os tokens
        await api.post("auth/logout/", { refresh: refreshToken });
      }
    } catch (error) {
      console.error("Erro no logout no servidor:", error);
    } finally {
      // Limpa os cookies locais e o estado de qualquer forma
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
