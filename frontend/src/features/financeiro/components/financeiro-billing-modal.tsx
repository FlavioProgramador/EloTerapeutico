"use client";

import { CalendarDays } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { formatCurrency } from "../financeiro-formatters";
import { useGenerateCharges } from "../hooks/use-financeiro-dashboard";

interface Item { id: number; patient_name: string; start_time: string; session_value: string }
interface Props { open: boolean; appointments: Item[]; onClose: () => void }

export function FinanceiroBillingModal({ open, appointments, onClose }: Props) {
  const mutation = useGenerateCharges();
  const [selected, setSelected] = useState<number[]>([]);
  const [dueDate, setDueDate] = useState(new Date().toISOString().slice(0, 10));

  useEffect(() => {
    if (open) setSelected(appointments.map((item) => item.id));
  }, [open, appointments]);

  const toggle = (id: number) => setSelected((items) =>
    items.includes(id) ? items.filter((item) => item !== id) : [...items, id],
  );

  const submit = () => mutation.mutate(
    { appointmentIds: selected, dueDate },
    { onSuccess: onClose },
  );

  return (
    <Modal isOpen={open} onClose={onClose} title="Gerar cobranças do mês" description="Selecione as sessões realizadas sem cobrança vinculada." className="max-w-2xl">
      {appointments.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <CalendarDays className="mx-auto h-8 w-8 text-muted-foreground" />
          <h3 className="mt-3 font-semibold">Nenhuma sessão pendente</h3>
          <p className="mt-1 text-sm text-muted-foreground">Todas as sessões elegíveis já possuem cobrança.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <Input label="Vencimento" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
          <div className="max-h-80 space-y-2 overflow-y-auto">
            {appointments.map((appointment) => (
              <label key={appointment.id} className="flex cursor-pointer items-center gap-3 rounded-lg border border-border p-3">
                <input type="checkbox" checked={selected.includes(appointment.id)} onChange={() => toggle(appointment.id)} />
                <span className="min-w-0 flex-1">
                  <strong className="block truncate">{appointment.patient_name}</strong>
                  <small className="text-muted-foreground">{new Date(appointment.start_time).toLocaleDateString("pt-BR")}</small>
                </span>
                <span className="font-semibold">{formatCurrency(appointment.session_value)}</span>
              </label>
            ))}
          </div>
        </div>
      )}
      <div className="mt-6 flex justify-end gap-2">
        <Button variant="outline" onClick={onClose}>Cancelar</Button>
        <Button disabled={!selected.length || !dueDate} isLoading={mutation.isPending} onClick={submit}>Gerar ({selected.length})</Button>
      </div>
    </Modal>
  );
}
