"use client";

import { CalendarDays } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { formatCurrency } from "../financeiro-formatters";
import { useGenerateCharges } from "../hooks/use-financeiro-dashboard";

interface Item {
  id: number;
  patient_name: string;
  start_time: string;
  session_value: string;
}

interface Props {
  open: boolean;
  appointments: Item[];
  onClose: () => void;
}

export function FinanceiroBillingModal({ open, appointments, onClose }: Props) {
  const mutation = useGenerateCharges();
  const [selected, setSelected] = useState<number[]>([]);
  const [dueDate, setDueDate] = useState(new Date().toISOString().slice(0, 10));

  useEffect(() => {
    if (open) setSelected(appointments.map((item) => item.id));
  }, [open, appointments]);

  const toggle = (id: number) => {
    if (mutation.isPending) return;
    setSelected((items) =>
      items.includes(id) ? items.filter((item) => item !== id) : [...items, id],
    );
  };

  const handleClose = () => {
    if (!mutation.isPending) {
      onClose();
    }
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!selected.length || !dueDate || mutation.isPending) return;

    mutation.mutate(
      { appointmentIds: selected, dueDate },
      { onSuccess: onClose },
    );
  };

  return (
    <Modal
      isOpen={open}
      onClose={handleClose}
      title="Gerar cobranças do mês"
      description="Selecione as sessões realizadas sem cobrança vinculada."
      className="max-w-2xl"
    >
      {appointments.length === 0 ? (
        <>
          <div className="rounded-xl border border-dashed border-border py-12 text-center">
            <CalendarDays
              className="mx-auto h-8 w-8 text-muted-foreground"
              aria-hidden="true"
            />
            <h3 className="mt-3 font-semibold">Nenhuma sessão pendente</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Todas as sessões elegíveis já possuem cobrança.
            </p>
          </div>
          <div className="mt-6 flex justify-end">
            <Button variant="outline" onClick={handleClose}>
              Fechar
            </Button>
          </div>
        </>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Vencimento"
              type="date"
              value={dueDate}
              disabled={mutation.isPending}
              onChange={(event) => setDueDate(event.target.value)}
            />
            <div className="max-h-80 space-y-2 overflow-y-auto">
              {appointments.map((appointment) => {
                const checkboxId = `billing-session-${appointment.id}`;
                return (
                  <label
                    key={appointment.id}
                    htmlFor={checkboxId}
                    className={`flex items-center gap-3 rounded-lg border border-border p-3 transition-colors ${
                      mutation.isPending
                        ? "cursor-not-allowed opacity-60"
                        : "cursor-pointer hover:bg-muted/50"
                    }`}
                  >
                    <input
                      id={checkboxId}
                      type="checkbox"
                      checked={selected.includes(appointment.id)}
                      disabled={mutation.isPending}
                      onChange={() => toggle(appointment.id)}
                      className="h-4 w-4 rounded border-input text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed"
                    />
                    <span className="min-w-0 flex-1">
                      <strong className="block truncate">
                        {appointment.patient_name}
                      </strong>
                      <small className="text-muted-foreground">
                        {new Date(appointment.start_time).toLocaleDateString(
                          "pt-BR",
                        )}
                      </small>
                    </span>
                    <span className="font-semibold">
                      {formatCurrency(appointment.session_value)}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
          <div className="mt-6 flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={mutation.isPending}
              onClick={handleClose}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!selected.length || !dueDate || mutation.isPending}
              isLoading={mutation.isPending}
            >
              Gerar ({selected.length})
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
