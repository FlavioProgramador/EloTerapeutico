"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
}: ModalProps) {
  // ESC key listener to close modal
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/40 backdrop-blur-md transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div
        className={cn(
          "w-full max-w-lg bg-card border border-border/60 rounded-xl shadow-xl z-10 flex flex-col relative",
          "animate-scale-in max-h-[90vh] overflow-hidden",
          className
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-border-strong/10 shrink-0">
          <div className="space-y-1">
            <h3 className="text-xl font-bold text-text-primary leading-none">
              {title}
            </h3>
            {description && (
              <p className="text-sm text-text-secondary mt-1.5 leading-normal">
                {description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-text-muted/60 hover:text-text-primary hover:bg-secondary rounded-lg p-1 transition-all cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto text-text-secondary">
          {children}
        </div>
      </div>
    </div>
  );
}
