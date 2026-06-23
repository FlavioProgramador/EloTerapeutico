"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "sonner";
import { AuthProvider } from "@/contexts/auth";
import { ThemeProvider } from "./theme-provider";
import { queryClient } from "./query-client";

/**
 * Providers raiz da aplicação.
 * Ordem correta de aninhamento:
 * ThemeProvider → QueryClientProvider → AuthProvider → Toaster
 *
 * O Toaster está fora do AuthProvider pois deve ser acessível globalmente,
 * inclusive antes/depois de autenticação.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
        </AuthProvider>
        <Toaster
          position="bottom-right"
          toastOptions={{
            classNames: {
              toast:
                "bg-card text-card-foreground border border-border shadow-lg",
              title: "font-medium text-sm",
              description: "text-muted-foreground text-sm",
              success: "border-l-4 border-l-primary",
              error: "border-l-4 border-l-destructive",
              warning: "border-l-4 border-l-yellow-500",
            },
            duration: 4000,
          }}
          richColors
        />
        {process.env.NODE_ENV === "development" && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ThemeProvider>
  );
}
