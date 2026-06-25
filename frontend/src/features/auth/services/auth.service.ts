/**
 * Serviço de autenticação.
 * Encapsula todas as chamadas de API relacionadas à autenticação.
 * Separa a lógica de cookie/state (que fica no AuthContext) da lógica de rede.
 */

import { api } from "@/lib/api";
import type { LoginCredentials, AuthTokens, User } from "@/types";

export const authService = {
  /**
   * Realiza o login e retorna access + refresh tokens (e opcionalmente user).
   */
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>("auth/login/", credentials);
    return response.data;
  },

  /**
   * Realiza o logout e invalida o refresh token no backend.
   */
  logout: async (refreshToken: string): Promise<void> => {
    await api.post("auth/logout/", { refresh: refreshToken });
  },

  /**
   * Busca o perfil do usuário autenticado.
   */
  getMe: async (): Promise<User> => {
    const response = await api.get<User>("auth/me/");
    return response.data;
  },

  /**
   * Renova o access token usando o refresh token.
   */
  refreshToken: async (
    refresh: string
  ): Promise<{ access: string; refresh?: string }> => {
    const response = await api.post("auth/token/refresh/", { refresh });
    return response.data;
  },

  /**
   * Registra um novo usuário.
   */
  register: async (data: {
    email: string;
    password: string;
    full_name: string;
    role?: string;
  }): Promise<User> => {
    const response = await api.post<User>("auth/register/", data);
    return response.data;
  },

  /**
   * Solicita a redefinição de senha (forgot password).
   */
  requestPasswordReset: async (email: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>("auth/password/reset/", { email });
    return response.data;
  },

  /**
   * Confirma a nova senha usando o token e uidb64 recebidos por e-mail.
   */
  confirmPasswordReset: async (data: {
    uidb64: string;
    token: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>("auth/password/reset/confirm/", data);
    return response.data;
  },
};
