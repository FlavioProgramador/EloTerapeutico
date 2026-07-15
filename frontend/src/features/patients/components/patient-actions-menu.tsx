"use client";

import {
  CalendarPlus,
  ClipboardList,
  Link2,
  MessageCircle,
  MoreHorizontal,
  Pencil,
  RotateCcw,
  Trash2,
  UserRoundX,
} from "lucide-react";
import { useRouter } from "next/navigation";
import {
  type KeyboardEvent,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { toast } from "sonner";

import type { PatientListItem } from "./patient-list-item";

interface Props {
  patient: PatientListItem;
  canManage: boolean;
  canAccessRecords: boolean;
  onEdit: () => void;
  onDeactivate: () => void;
  onRestore: () => void;
  onRemove: () => void;
  onRegistrationLink: () => void;
}

function getWhatsappUrl(value?: string) {
  const digits = value?.replace(/\D/g, "") ?? "";
  if (!digits) return null;
  const normalized = digits.startsWith("55") ? digits : `55${digits}`;
  return `https://wa.me/${normalized}`;
}

export function PatientActionsMenu({
  patient,
  canManage,
  canAccessRecords,
  onEdit,
  onDeactivate,
  onRestore,
  onRemove,
  onRegistrationLink,
}: Props) {
  const router = useRouter();
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
    const estimatedHeight = 350;
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
  const restorable = ["inactive", "archived"].includes(patient.status);

  const menu = open ? (
    <div
      ref={menuRef}
      role="menu"
      aria-label={`Ações de ${patient.display_name}`}
      onKeyDown={onMenuKeyDown}
      className="fixed z-[100] w-[232px] rounded-xl border border-border bg-popover p-1.5 text-popover-foreground shadow-xl"
      style={{ left: position.left, top: position.top }}
    >
      <p className="border-b border-border px-3 py-2 text-xs font-bold text-foreground">
        Ações
      </p>
      <div className="py-1">
        {canAccessRecords && (
          <button
            type="button"
            role="menuitem"
            className={itemClass}
            onClick={() =>
              run(() => router.push(`/dashboard/records/${patient.id}`))
            }
          >
            <ClipboardList className="h-4 w-4" /> Ver Prontuário
          </button>
        )}
        <button
          type="button"
          role="menuitem"
          className={itemClass}
          onClick={() =>
            run(() => router.push(`/dashboard/agenda?patient=${patient.id}`))
          }
        >
          <CalendarPlus className="h-4 w-4" /> Agendar Consulta
        </button>
        <button
          type="button"
          role="menuitem"
          className={itemClass}
          onClick={() =>
            run(() => {
              const url = getWhatsappUrl(patient.whatsapp || patient.phone);
              if (!url) {
                toast.error(
                  "Este paciente não possui WhatsApp ou telefone cadastrado.",
                );
                return;
              }
              window.open(url, "_blank", "noopener,noreferrer");
            })
          }
        >
          <MessageCircle className="h-4 w-4" /> Enviar WhatsApp
        </button>
        {canManage && (
          <button
            type="button"
            role="menuitem"
            className={itemClass}
            onClick={() => run(onRegistrationLink)}
          >
            <Link2 className="h-4 w-4" /> Enviar Link de Cadastro
          </button>
        )}
        {canManage && (
          <button
            type="button"
            role="menuitem"
            className={itemClass}
            onClick={() => run(onEdit)}
          >
            <Pencil className="h-4 w-4" /> Editar Dados
          </button>
        )}
        {canManage && (
          <button
            type="button"
            role="menuitem"
            className={itemClass}
            onClick={() => run(restorable ? onRestore : onDeactivate)}
          >
            {restorable ? (
              <RotateCcw className="h-4 w-4" />
            ) : (
              <UserRoundX className="h-4 w-4" />
            )}
            {restorable ? "Reativar Paciente" : "Inativar Paciente"}
          </button>
        )}
      </div>
      {canManage && (
        <div className="border-t border-border pt-1">
          <button
            type="button"
            role="menuitem"
            className={`${itemClass} text-destructive hover:bg-destructive/10 focus-visible:bg-destructive/10`}
            onClick={() => run(onRemove)}
          >
            <Trash2 className="h-4 w-4" /> Remover Paciente
          </button>
        </div>
      )}
    </div>
  ) : null;

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={`Abrir ações de ${patient.display_name}`}
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
