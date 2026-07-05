import type { Dispatch, SetStateAction } from "react";
import { CalendarDays } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { formatMoney, parseMoney, type FinanceFormState, type UnbilledAppointment } from "./financeiro-shared";

export function FinanceBatchDialog({ form, setForm, appointments, loading, creating, copy, onCancel, onConfirm }: { form: FinanceFormState; setForm: Dispatch<SetStateAction<FinanceFormState>>; appointments: UnbilledAppointment[]; loading: boolean; creating: boolean; copy: { loading: string; emptyTitle: string; emptyDescription: string; dateLabel: string; cancel: string; confirm: string }; onCancel: () => void; onConfirm: () => void }) {
  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-dashed border-border p-6">
        {loading ? (
          <p className="text-sm text-muted-foreground">{copy.loading}</p>
        ) : appointments.length === 0 ? (
          <EmptyState icon={<CalendarDays className="h-7 w-7" />} title={copy.emptyTitle} description={copy.emptyDescription} />
        ) : (
          <div className="space-y-3">
            {appointments.map((appointment) => (
              <div key={appointment.id} className="flex items-center justify-between rounded-lg border border-border bg-muted/30 p-3">
                <div><p className="font-medium text-foreground">{appointment.patient_name}</p><p className="text-xs text-muted-foreground">{new Date(appointment.start_time).toLocaleString("pt-BR")}</p></div>
                <span className="font-semibold text-foreground">{formatMoney(parseMoney(appointment.session_value), false)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      <label className="block space-y-2"><span className="text-sm font-medium text-foreground">{copy.dateLabel}</span><Input type="date" value={form.dueDate} onChange={(event) => setForm((current) => ({ ...current, dueDate: event.target.value }))} /></label>
      <div className="flex justify-end gap-2 border-t border-border pt-5"><Button variant="outline" onClick={onCancel}>{copy.cancel}</Button><Button onClick={onConfirm} disabled={appointments.length === 0 || creating}>{copy.confirm} ({appointments.length})</Button></div>
    </div>
  );
}
