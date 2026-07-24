"use client";

import { useId, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import type { Patient } from "@/types";

import { formatCurrency } from "../financeiro-formatters";
import { useGenerateCharges } from "../hooks/use-financeiro-dashboard";

interface UnbilledItem {
  id: number;
  patient_id: number;
  patient_name: string;
  start_time: string;
  end_time: string;
  session_value: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  patients: Patient[];
  unbilled: UnbilledItem[];
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function FinanceiroNewBillingModal({
  open,
  onClose,
  patients,
  unbilled,
}: Props) {
  const [patientId, setPatientId] = useState<number | "">("");
  const [dueDate, setDueDate] = useState(today);
  const [selectedSessions, setSelectedSessions] = useState<number[]>([]);
  const generateCharges = useGenerateCharges();

  const baseId = useId();
  const patientSelectId = `${baseId}-patient`;
  const dueDateId = `${baseId}-due-date`;

  const patientUnbilled = useMemo(() => {
    if (!patientId) return [];
    return unbilled.filter((item) => item.patient_id === patientId);
  }, [unbilled, patientId]);

  const totalValue = useMemo(
    () =>
      selectedSessions.reduce((total, id) => {
        const session = patientUnbilled.find((item) => item.id === id);
        const value = Number.parseFloat(session?.session_value ?? "0");
        return total + (Number.isFinite(value) ? value : 0);
      }, 0),
    [patientUnbilled, selectedSessions],
  );

  const resetAndClose = () => {
    setPatientId("");
    setDueDate(today());
    setSelectedSessions([]);
    onClose();
  };

  const selectPatient = (rawValue: string) => {
    if (!rawValue) {
      setPatientId("");
      setSelectedSessions([]);
      return;
    }

    const nextPatientId = Number(rawValue);
    setPatientId(nextPatientId);
    setSelectedSessions(
      unbilled
        .filter((item) => item.patient_id === nextPatientId)
        .map((item) => item.id),
    );
  };

  const toggleSession = (id: number) => {
    setSelectedSessions((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id],
    );
  };

  const toggleAll = () => {
    setSelectedSessions((current) =>
      current.length === patientUnbilled.length
        ? []
        : patientUnbilled.map((item) => item.id),
    );
  };

  const submit = () => {
    if (!dueDate || selectedSessions.length === 0) return;
    generateCharges.mutate(
      { appointmentIds: selectedSessions, dueDate },
      { onSuccess: resetAndClose },
    );
  };

  return (
    <Modal
      isOpen={open}
      onClose={resetAndClose}
      title="Nova cobrança"
      description="Selecione o paciente e as sessões que devem gerar lançamentos financeiros."
      className="max-w-2xl"
    >
      <div className="space-y-6 pt-2">
        <div className="space-y-1.5">
          <label htmlFor={patientSelectId} className="text-sm font-semibold">
            Paciente
          </label>
          <select
            id={patientSelectId}
            value={patientId}
            onChange={(event) => selectPatient(event.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
          >
            <option value="">Selecione um paciente</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.full_name}
              </option>
            ))}
          </select>
        </div>

        {patientId !== "" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-semibold">
                Sessões disponíveis para cobrança
              </span>
              {patientUnbilled.length > 0 && (
                <button
                  type="button"
                  onClick={toggleAll}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  {selectedSessions.length === patientUnbilled.length
                    ? "Desmarcar todas"
                    : "Marcar todas"}
                </button>
              )}
            </div>

            <div className="max-h-[300px] space-y-2 overflow-y-auto pr-1">
              {patientUnbilled.length === 0 ? (
                <div className="rounded-lg border border-dashed py-4 text-center text-sm text-muted-foreground">
                  Nenhuma sessão pendente para este paciente.
                </div>
              ) : (
                patientUnbilled.map((session) => {
                  const isSelected = selectedSessions.includes(session.id);
                  const startsAt = new Date(session.start_time);

                  return (
                    <label
                      key={session.id}
                      className={`flex cursor-pointer items-center justify-between rounded-lg border p-3 transition-colors ${
                        isSelected
                          ? "border-blue-500/50 bg-blue-500/5"
                          : "border-border"
                      }`}
                    >
                      <span className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSession(session.id)}
                          className="rounded border-input text-blue-500"
                        />
                        <span>
                          <span className="block text-sm font-semibold">
                            {startsAt.toLocaleDateString("pt-BR")} às{" "}
                            {startsAt.toLocaleTimeString("pt-BR", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            Consulta
                          </span>
                        </span>
                      </span>
                      <span className="text-sm font-semibold text-blue-500">
                        {formatCurrency(session.session_value)}
                      </span>
                    </label>
                  );
                })
              )}
            </div>

            {patientUnbilled.length > 0 && (
              <div className="mt-2 flex items-center justify-between rounded-lg bg-secondary/30 p-4">
                <span className="text-sm font-medium">
                  {selectedSessions.length} sessão(ões) selecionada(s)
                </span>
                <span className="text-lg font-bold text-blue-500">
                  {formatCurrency(totalValue.toFixed(2))}
                </span>
              </div>
            )}
          </div>
        )}

        <div className="space-y-1.5">
          <label htmlFor={dueDateId} className="text-sm font-semibold">
            Vencimento
          </label>
          <Input
            id={dueDateId}
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
          />
        </div>

        <p className="text-xs text-muted-foreground">
          O valor de cada lançamento será o valor registrado na respectiva sessão.
        </p>

        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={resetAndClose}>
            Cancelar
          </Button>
          <Button
            onClick={submit}
            disabled={
              generateCharges.isPending ||
              !dueDate ||
              selectedSessions.length === 0
            }
            className="bg-blue-600 text-white hover:bg-blue-700"
          >
            {generateCharges.isPending ? "Criando..." : "Criar cobrança"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
