import axios from "axios";
import { getCookie, setCookie, deleteCookie } from "cookies-next";

// Define a URL base para a API a partir das variáveis de ambiente
// Utiliza fallback de desenvolvimento local caso não esteja configurada
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor de Requisições: Injeta o token JWT de acesso em todas as chamadas
api.interceptors.request.use(
  (config) => {
    // Tenta obter o token dos cookies
    const token = getCookie("auth_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Controle de enfileiramento de requisições simultâneas durante a renovação do token
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

// Interceptor de Respostas: Intercepta erros 401 (não autorizado) e faz a renovação silenciosa do token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Se o erro for 401 e a requisição ainda não foi tentada novamente,
    // e também não é a própria chamada de login/refresh para evitar loop
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("auth/login") &&
      !originalRequest.url?.includes("auth/token/refresh")
    ) {
      if (isRefreshing) {
        // Enfileira a requisição atual enquanto outra chamada renova o token
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      // Obtém o token de refresh nos cookies
      const refreshToken = getCookie("auth_refresh_token");

      if (!refreshToken) {
        isRefreshing = false;
        // Sem token de refresh: limpa tudo e força redirecionamento
        deleteCookie("auth_token");
        deleteCookie("auth_refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        // Executa a requisição de refresh usando uma instância limpa do axios para evitar interceptores
        const response = await axios.post(`${API_URL}auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access, refresh } = response.data;

        // Armazena os novos tokens nos cookies de forma segura
        setCookie("auth_token", access, {
          maxAge: 30 * 60, // 30 minutos
          path: "/",
          sameSite: "lax",
        });

        if (refresh) {
          setCookie("auth_refresh_token", refresh, {
            maxAge: 7 * 24 * 60 * 60, // 7 dias
            path: "/",
            sameSite: "lax",
          });
        }

        // Atualiza cabeçalhos padrões e da requisição que falhou
        api.defaults.headers.common["Authorization"] = `Bearer ${access}`;
        originalRequest.headers["Authorization"] = `Bearer ${access}`;

        // Executa todas as requisições que estavam travadas na fila
        processQueue(null, access);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;

        // Se falhar a renovação do token, desloga e redireciona para a tela de login
        deleteCookie("auth_token");
        deleteCookie("auth_refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
