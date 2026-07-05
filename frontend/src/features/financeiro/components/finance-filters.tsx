import { Filter, RefreshCcw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { TransactionStatus } from "@/types";

export function FinanceFilters({ patients, status, setStatus, patient, setPatient, search, setSearch, count, onRefresh }: { patients: Array<{ id: number; full_name: string }>; status: "all" | TransactionStatus; setStatus: (status: "all" | TransactionStatus) => void; patient: string; setPatient: (patient: string) => void; search: string; setSearch: (value: string) => void; count: number; onRefresh: () => void }) {
  return (
    <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center">
      <div className="flex items-center gap-2 text-sm text-muted-foreground"><Filter className="h-4 w-4" /> Filtros</div>
      <label className="relative min-w-56 flex-1 lg:max-w-xs"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar paciente ou descrição..." /></label>
      <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={patient} onChange={(event) => setPatient(event.target.value)}><option value="all">Todos os pacientes</option>{patients.map((item) => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select>
      <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={status} onChange={(event) => setStatus(event.target.value as "all" | TransactionStatus)}><option value="all">Todos os status</option><option value="pending">Pendente</option><option value="overdue">Vencido</option><option value="paid">Pago</option><option value="cancelled">Cancelado</option><option value="refunded">Estornado</option></select>
      <Button variant="ghost" size="sm" onClick={onRefresh} aria-label="Atualizar dados"><RefreshCcw className="h-4 w-4" /></Button>
      <span className="ml-auto rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">{count} registro(s)</span>
    </div>
  );
}
