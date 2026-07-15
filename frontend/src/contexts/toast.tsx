"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import {
  X,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: "default" | "success" | "destructive" | "warning" | "info";
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  toast: (toast: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    ({
      title,
      description,
      variant = "default",
      duration = 4000,
    }: Omit<Toast, "id">) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: Toast = { id, title, description, variant, duration };

      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          dismiss(id);
        }, duration);
      }
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <ToastContainer toasts={toasts} dismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error("useToast deve ser usado dentro de um ToastProvider");
  }
  return context;
}

function ToastContainer({
  toasts,
  dismiss,
}: {
  toasts: Toast[];
  dismiss: (id: string) => void;
}) {
  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2.5 w-full max-w-sm pointer-events-none p-4 md:p-0">
      {toasts.map((t) => {
        const icons = {
          default: null,
          success: (
            <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
          ),
          destructive: (
            <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
          ),
          warning: (
            <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
          ),
          info: <Info className="h-5 w-5 text-blue-500 shrink-0" />,
        };

        const bgVariants = {
          default: "bg-card border-border text-foreground",
          success: "bg-card border-emerald-500/20 text-foreground",
          destructive: "bg-card border-destructive/20 text-foreground",
          warning: "bg-card border-amber-500/20 text-foreground",
          info: "bg-card border-blue-500/20 text-foreground",
        };

        return (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-start gap-3 w-full p-4 rounded-xl border shadow-lg glass-effect animate-slide-in-right",
              bgVariants[t.variant || "default"],
            )}
          >
            {t.variant && icons[t.variant]}
            <div className="flex-1 flex flex-col gap-0.5">
              <span className="font-semibold text-sm leading-snug">
                {t.title}
              </span>
              {t.description && (
                <span className="text-xs text-muted-foreground leading-relaxed">
                  {t.description}
                </span>
              )}
            </div>
            <button
              onClick={() => dismiss(t.id)}
              className="text-muted-foreground/60 hover:text-foreground hover:bg-secondary/80 rounded-md p-0.5 transition-all cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
