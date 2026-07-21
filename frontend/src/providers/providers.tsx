"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "sonner";

import { AuthProvider } from "@/contexts/auth";
import { OrganizationProvider } from "@/contexts/organization";
import { ThemeProvider } from "./theme-provider";
import { queryClient } from "./query-client";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <OrganizationProvider>{children}</OrganizationProvider>
        </AuthProvider>
        <Toaster
          position="bottom-right"
          theme="system"
          toastOptions={{
            classNames: {
              toast:
                "bg-popover text-popover-foreground border border-border shadow-xl shadow-black/10",
              title: "font-semibold text-sm",
              description: "text-muted-foreground text-sm",
              success: "border-l-4 border-l-success",
              error: "border-l-4 border-l-destructive",
              warning: "border-l-4 border-l-warning",
              info: "border-l-4 border-l-info",
            },
            duration: 4000,
          }}
        />
        {process.env.NODE_ENV === "development" && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ThemeProvider>
  );
}
