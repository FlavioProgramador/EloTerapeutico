import * as React from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: "default" | "underline";
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = "text",
      label,
      error,
      leftIcon,
      rightIcon,
      id,
      variant = "default",
      ...props
    },
    ref,
  ) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const errorId = `${inputId}-error`;
    const ariaDescribedBy = [props["aria-describedby"], error ? errorId : null]
      .filter(Boolean)
      .join(" ");

    return (
      <div className="flex w-full flex-col gap-1.5 group">
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              "font-semibold transition-colors",
              variant === "underline"
                ? "text-xs uppercase tracking-wider text-muted-foreground group-focus-within:text-primary"
                : "text-sm text-foreground"
            )}
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className={cn(
              "pointer-events-none absolute flex items-center justify-center transition-colors",
              variant === "default" ? "left-3.5 text-muted-foreground" : "left-0 text-muted-foreground group-focus-within:text-primary"
            )}>
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            type={type}
            id={inputId}
            aria-describedby={ariaDescribedBy || undefined}
            aria-invalid={error ? "true" : props["aria-invalid"]}
            className={cn(
              "h-11 w-full text-base text-text-primary transition-all duration-150",
              "placeholder:text-text-muted/60 focus:outline-none",
              "[&:-webkit-autofill]:[transition:background-color_9999s_ease-in-out_0s] [&:-webkit-autofill]:[-webkit-text-fill-color:#1a1a1a]",
              variant === "default" && [
                "rounded-lg border border-input bg-card px-3.5",
                "focus:border-primary focus:ring-4 focus:ring-primary-soft",
                "disabled:bg-background-subtle",
                error && "border-danger focus:border-danger focus:ring-danger-soft",
              ],
              variant === "underline" && [
                "rounded-none border-0 border-b-2 border-border bg-transparent px-0 py-2 !outline-none focus:!outline-none",
                "focus:border-primary focus:border-b-primary focus:ring-0",
                error && "border-danger focus:border-danger focus:border-b-danger",
              ],
              "disabled:cursor-not-allowed disabled:text-text-muted disabled:opacity-60",
              leftIcon && (variant === "default" ? "pl-10.5" : "pl-8"),
              rightIcon && (variant === "default" ? "pr-10.5" : "pr-8"),
              className,
            )}
            {...props}
          />
          {rightIcon && (
            <div className={cn(
              "absolute flex items-center justify-center transition-colors",
              variant === "default" ? "right-3.5 text-text-muted" : "right-0 text-muted-foreground group-focus-within:text-primary"
            )}>
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <span
            id={errorId}
            className="text-sm font-medium text-danger"
            role="alert"
          >
            {error}
          </span>
        )}
      </div>
    );
  },
);

Input.displayName = "Input";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const errorId = `${inputId}-error`;
    const ariaDescribedBy = [props["aria-describedby"], error ? errorId : null]
      .filter(Boolean)
      .join(" ");

    return (
      <div className="flex w-full flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-semibold text-foreground"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          aria-describedby={ariaDescribedBy || undefined}
          aria-invalid={error ? "true" : props["aria-invalid"]}
          className={cn(
            "min-h-[100px] w-full resize-y rounded-lg border border-input bg-card p-3.5 text-base text-text-primary transition-all duration-150",
            "placeholder:text-text-muted/60",
            "focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary-soft",
            "disabled:cursor-not-allowed disabled:bg-background-subtle disabled:text-text-muted disabled:opacity-60",
            error && "border-danger focus:border-danger focus:ring-danger-soft",
            className,
          )}
          {...props}
        />
        {error && (
          <span
            id={errorId}
            className="text-sm font-medium text-danger"
            role="alert"
          >
            {error}
          </span>
        )}
      </div>
    );
  },
);

Textarea.displayName = "Textarea";

export { Input, Textarea };
