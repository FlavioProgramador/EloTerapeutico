import { CheckCircle2, MoreHorizontal, RefreshCcw, Trash2, XCircle } from "lucide-react";
import type { TransactionStatus } from "@/types";

export function FinanceActionMenu({ status, open, onToggle, onSelect }: { status: TransactionStatus; open: boolean; onToggle: () => void; onSelect: (action: "pay" | "cancel" | "refund" | "delete") => void }) {
  return (
    <div className="relative">
      <button type="button" onClick={onToggle} className="rounded-md p-2 text-muted-foreground hover:bg-muted" aria-label="Abrir ações"><MoreHorizontal className="h-4 w-4" /></button>
      {open && (
        <div className="absolute right-0 top-10 z-20 w-48 rounded-lg border border-border bg-popover p-1.5 text-left shadow-xl">
          {(status === "pending" || status === "overdue") && <Item icon={CheckCircle2} label="Marcar como pago" onClick={() => onSelect("pay")} />}
          {(status === "pending" || status === "overdue") && <Item icon={XCircle} label="Cancelar" onClick={() => onSelect("cancel")} />}
          {status === "paid" && <Item icon={RefreshCcw} label="Estornar" onClick={() => onSelect("refund")} />}
          <Item icon={Trash2} label="Excluir" onClick={() => onSelect("delete")} danger />
        </div>
      )}
    </div>
  );
}

function Item({ icon: Icon, label, onClick, danger }: { icon: typeof CheckCircle2; label: string; onClick: () => void; danger?: boolean }) {
  return <button type="button" onClick={onClick} className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-muted ${danger ? "text-rose-400" : "text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>;
}
