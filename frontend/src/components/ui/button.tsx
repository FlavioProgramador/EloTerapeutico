import * as React from "react";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "default"
    | "primary"
    | "secondary"
    | "outline"
    | "destructive"
    | "ghost"
    | "glass";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref,
  ) => {
    const variants = {
      default:
        "bg-primary text-primary-foreground shadow-sm hover:bg-primary-hover active:bg-primary-active",
      primary:
        "bg-primary text-primary-foreground shadow-sm hover:bg-primary-hover active:bg-primary-active",
      secondary:
        "bg-secondary text-secondary-foreground hover:bg-background-subtle active:bg-muted",
      outline:
        "border border-border bg-transparent text-foreground hover:bg-secondary hover:text-secondary-foreground",
      destructive:
        "bg-danger text-primary-foreground shadow-sm hover:bg-danger/95 active:bg-danger/90",
      ghost:
        "text-muted-foreground hover:bg-secondary/70 hover:text-foreground",
      glass:
        "border border-border bg-card text-card-foreground hover:bg-secondary hover:text-secondary-foreground",
    };

    const sizes = {
      sm: "h-9 gap-1.5 px-3 text-sm rounded-md",
      md: "h-11 gap-2 px-5 text-base rounded-lg",
      lg: "h-13 gap-2.5 px-7 text-lg rounded-lg",
      icon: "h-11 w-11 p-0 rounded-lg",
    };

    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={cn(
          "inline-flex select-none items-center justify-center font-semibold transition-all duration-150 ease-out cursor-pointer",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-soft focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          "disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed",
          "active:scale-[0.98]",
          variants[variant],
          sizes[size],
          className,
        )}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <>
            {leftIcon && <span className="flex shrink-0">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="flex shrink-0">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  },
);

Button.displayName = "Button";

export { Button };
