"use client";

import { X } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

import { Button } from "@/components/ui/button";

interface Props {
  open: boolean;
  title: string;
  dirty: boolean;
  submitting: boolean;
  submitLabel: string;
  onClose: () => void;
  onSubmit: () => void;
  children: ReactNode;
}

export function PatientFormDrawerShell(props: Props) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!props.open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") props.onClose();
      if (event.key !== "Tab" || !panelRef.current) return;
      const items = panelRef.current.querySelectorAll<HTMLElement>(
        "button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex='-1'])",
      );
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [props]);

  if (!props.open || typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-[120] flex justify-end" role="presentation">
      <button
        type="button"
        className="absolute inset-0 bg-black/65 backdrop-blur-[1px]"
        aria-label="Fechar formulário"
        onClick={props.onClose}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={props.title}
        className="relative flex h-dvh w-full flex-col border-l border-border bg-background shadow-2xl md:w-[68vw] xl:w-[44vw] xl:min-w-[620px]"
      >
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-5">
          <h2 className="text-base font-semibold text-foreground">
            {props.title}
          </h2>
          <button
            type="button"
            onClick={props.onClose}
            className="grid h-9 w-9 place-items-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
            aria-label="Fechar"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {props.children}
        </div>

        <footer className="flex shrink-0 justify-end gap-2 border-t border-border bg-background px-5 py-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={props.onClose}
            disabled={props.submitting}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={props.onSubmit}
            isLoading={props.submitting}
          >
            {props.submitLabel}
          </Button>
        </footer>
      </div>
    </div>,
    document.body,
  );
}
