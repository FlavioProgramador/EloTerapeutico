import { QueryClient } from "@tanstack/react-query";

/**
 * Configuração centralizada do QueryClient.
 * - staleTime: 60s – dados recentes não são refetchados desnecessariamente.
 * - retry: 1 – tenta apenas 1 vez antes de falhar (não spam de requisições).
 * - refetchOnWindowFocus: false – evita refetch ao trocar de aba.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 60 segundos
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});
