import * as React from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
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
      <div className="flex w-full flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-semibold text-foreground"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="pointer-events-none absolute left-3.5 flex items-center justify-center text-muted-foreground">
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
              "h-11 w-full rounded-lg border border-input bg-card px-3.5 text-base text-text-primary transition-all duration-150",
              "placeholder:text-text-muted/60",
              "focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary-soft",
              "disabled:cursor-not-allowed disabled:bg-background-subtle disabled:text-text-muted disabled:opacity-60",
              leftIcon && "pl-10.5",
              rightIcon && "pr-10.5",
              error &&
                "border-danger focus:border-danger focus:ring-danger-soft",
              className,
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3.5 flex items-center justify-center text-text-muted">
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
