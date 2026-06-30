import * as React from "react";

import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
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
            className={cn(
              "h-11 w-full rounded-md border border-input bg-background px-3.5 text-base text-foreground transition",
              "placeholder:text-muted-foreground/60",
              "focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring/20",
              "disabled:cursor-not-allowed disabled:bg-muted disabled:opacity-60",
              leftIcon && "pl-10.5",
              rightIcon && "pr-10.5",
              error &&
                "border-destructive focus:border-destructive focus:ring-destructive/15",
              className,
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3.5 flex items-center justify-center text-muted-foreground">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <span className="text-sm font-medium text-destructive" role="alert">
            {error}
          </span>
        )}
      </div>
    );
  },
);

Input.displayName = "Input";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;

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
          className={cn(
            "min-h-[100px] w-full resize-y rounded-md border border-input bg-background p-3.5 text-base text-foreground transition",
            "placeholder:text-muted-foreground/60",
            "focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring/20",
            "disabled:cursor-not-allowed disabled:bg-muted disabled:opacity-60",
            error &&
              "border-destructive focus:border-destructive focus:ring-destructive/15",
            className,
          )}
          {...props}
        />
        {error && (
          <span className="text-sm font-medium text-destructive" role="alert">
            {error}
          </span>
        )}
      </div>
    );
  },
);

Textarea.displayName = "Textarea";

export { Input, Textarea };
