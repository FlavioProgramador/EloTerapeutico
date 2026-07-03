import React from "react";

import { cn } from "@/lib/utils";

type BadgeVariant =
  | "default"
  | "primary"
  | "success"
  | "warning"
  | "destructive"
  | "outline"
  | "muted";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: "border-primary-soft bg-primary-soft text-primary",
  primary: "border-transparent bg-primary text-primary-foreground",
  success: "border-success-soft bg-success-soft text-success",
  warning: "border-warning-soft bg-warning-soft text-warning",
  destructive:
    "border-danger-soft bg-danger-soft text-danger",
  outline: "border-border bg-transparent text-foreground",
  muted: "border-transparent bg-muted text-muted-foreground",
};

export function Badge({
  variant = "default",
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium leading-none transition-colors",
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function getPatientStatusVariant(status: string): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    active: "success",
    evaluation: "warning",
    waiting_return: "outline",
    discharged: "primary",
    inactive: "muted",
    archived: "muted",
    on_hold: "warning",
  };
  return map[status] ?? "outline";
}

export function getAppointmentStatusVariant(status: string): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    scheduled: "default",
    confirmed: "primary",
    completed: "success",
    cancelled: "muted",
    missed: "destructive",
  };
  return map[status] ?? "outline";
}

export function getTransactionStatusVariant(status: string): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    pending: "warning",
    paid: "success",
    overdue: "destructive",
    cancelled: "muted",
    refunded: "outline",
  };
  return map[status] ?? "outline";
}
