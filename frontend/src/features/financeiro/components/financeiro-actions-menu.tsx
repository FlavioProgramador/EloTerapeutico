"use client";

import {
  MoreHorizontal,
  Trash2,
  Undo,
  CheckCircle2,
  XCircle,
  Pencil,
} from "lucide-react";
import {
  type KeyboardEvent,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import type { FinancialTransaction } from "@/types";

interface Props {
  transaction: FinancialTransaction;
  onEdit?: (id: number) => void;
  onMarkPaid?: (id: number) => void;
  onCancel?: (id: number) => void;
  onDelete?: (id: number) => void;
  onRefund?: (id: number) => void;
}

export function FinanceiroActionsMenu({
  transaction,
  onEdit,
  onMarkPaid,
  onCancel,
  onDelete,
  onRefund,
}: Props) {
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({ left: 0, top: 0 });

  const close = useCallback((restoreFocus = false) => {
    setOpen(false);
    if (restoreFocus) window.setTimeout(() => triggerRef.current?.focus(), 0);
  }, []);

  const updatePosition = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger) return;
    const rect = trigger.getBoundingClientRect();
    const width = 232;
    const estimatedHeight = 150;
    const margin = 8;
    const left = Math.min(
      Math.max(margin, rect.right - width),
      window.innerWidth - width - margin,
    );
    const top =
      rect.bottom + estimatedHeight + margin <= window.innerHeight
        ? rect.bottom + 6
        : Math.max(margin, rect.top - estimatedHeight - 6);
    setPosition({ left, top });
  }, []);

  useLayoutEffect(() => {
    if (!open) return;
    updatePosition();
    window.setTimeout(() => {
      menuRef.current
        ?.querySelector<HTMLButtonElement>("[role='menuitem']")
        ?.focus();
    }, 0);
  }, [open, updatePosition]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        !menuRef.current?.contains(target) &&
        !triggerRef.current?.contains(target)
      ) {
        close();
      }
    };
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close(true);
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [close, open, updatePosition]);

  const onMenuKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Tab") {
      close(true);
      return;
    }

    const items = Array.from(
      menuRef.current?.querySelectorAll<HTMLButtonElement>(
        "[role='menuitem']:not(:disabled)",
      ) ?? [],
    );
    const current = items.indexOf(document.activeElement as HTMLButtonElement);
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      items[(current + step + items.length) % items.length]?.focus();
    }
    if (event.key === "Home") {
      event.preventDefault();
      items[0]?.focus();
    }
    if (event.key === "End") {
      event.preventDefault();
      items.at(-1)?.focus();
    }
  };

  const run = (action: () => void) => {
    close();
    action();
  };

  const itemClass =
    "flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-left text-xs font-medium text-popover-foreground outline-none transition hover:bg-secondary focus-visible:bg-secondary focus-visible:ring-2 focus-visible:ring-ring/40";

  const menu = open ? (
    <div
      ref={menuRef}
      role="menu"
      aria-label={`Ações da transação: ${transaction.description || "Sem descrição"}`}
      onKeyDown={onMenuKeyDown}
      className="fixed z-[100] w-[232px] rounded-xl border border-border bg-popover p-1.5 text-popover-foreground shadow-xl"
      style={{ left: position.left, top: position.top }}
    >
      {(transaction.status === "pending" ||
        transaction.status === "overdue" ||
        transaction.status === "paid") && (
        <div className="py-1 border-b border-border">
          {(transaction.status === "pending" ||
            transaction.status === "overdue") &&
            onMarkPaid && (
              <button
                type="button"
                role="menuitem"
                className={itemClass}
                onClick={() => run(() => onMarkPaid(transaction.id))}
              >
                <CheckCircle2 className="h-4 w-4" /> Marcar como Pago
              </button>
            )}

          {transaction.status === "paid" && onRefund && (
            <button
              type="button"
              role="menuitem"
              className={itemClass}
              onClick={() => run(() => onRefund(transaction.id))}
            >
              <Undo className="h-4 w-4" /> Estornar Pagamento
            </button>
          )}
        </div>
      )}

      <div className="py-1">
        {onEdit && (
          <button
            type="button"
            role="menuitem"
            className={itemClass}
            onClick={() => run(() => onEdit(transaction.id))}
          >
            <Pencil className="h-4 w-4" /> Editar
          </button>
        )}

        {(transaction.status === "pending" ||
          transaction.status === "overdue") &&
          onCancel && (
            <button
              type="button"
              role="menuitem"
              className={itemClass}
              onClick={() => run(() => onCancel(transaction.id))}
            >
              <XCircle className="h-4 w-4" /> Cancelar
            </button>
          )}

        {onDelete && (
          <button
            type="button"
            role="menuitem"
            className={`${itemClass} text-destructive hover:bg-destructive/10 focus-visible:bg-destructive/10`}
            onClick={() => run(() => onDelete(transaction.id))}
          >
            <Trash2 className="h-4 w-4" /> Excluir
          </button>
        )}
      </div>
    </div>
  ) : null;

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={`Abrir ações para ${transaction.description || "transação"}${
          transaction.patient_name ? ` de ${transaction.patient_name}` : ""
        }`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="grid h-9 w-9 place-items-center rounded-md text-muted-foreground transition hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>
      {typeof document !== "undefined" && menu
        ? createPortal(menu, document.body)
        : null}
    </>
  );
}
