"use client";

import { useMemo, useState, useEffect, useId } from "react";
import { Check, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { formatCurrency } from "../financeiro-formatters";
import type { Patient } from "@/types";

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

export function FinanceiroNewBillingModal({
  open,
  onClose,
  patients,
  unbilled,
}: Props) {
  const [patientId, setPatientId] = useState<number | "">("");
  const [dueDate, setDueDate] = useState("");
  const [paymentLink, setPaymentLink] = useState("");
  const [notes, setNotes] = useState("");
  const [sendWhatsApp, setSendWhatsApp] = useState(false);
  const [valueBase, setValueBase] = useState<"session" | "patient">("session");
  const [selectedSessions, setSelectedSessions] = useState<number[]>([]);

  const baseId = useId();
  const patientSelectId = `${baseId}-patient`;
  const dueDateId = `${baseId}-due-date`;
  const paymentLinkId = `${baseId}-payment-link`;
  const paymentLinkHintId = `${baseId}-payment-link-hint`;
  const notesId = `${baseId}-notes`;
  const sendWhatsAppCheckboxId = `${baseId}-send-whatsapp`;

  useEffect(() => {
    if (open) {
      setPatientId("");
      setDueDate(new Date().toISOString().slice(0, 10));
      setPaymentLink("");
      setNotes("");
      setSendWhatsApp(false);
      setValueBase("session");
      setSelectedSessions([]);
    }
  }, [open]);

  const patientUnbilled = useMemo(() => {
    if (!patientId) return [];
    return unbilled.filter((u) => u.patient_id === Number(patientId));
  }, [unbilled, patientId]);

  useEffect(() => {
    if (patientId) {
      // Auto-select all sessions when a patient is chosen
      setSelectedSessions(patientUnbilled.map((s) => s.id));
    } else {
      setSelectedSessions([]);
    }
  }, [patientId, patientUnbilled]);

  const toggleSession = (id: number) => {
    setSelectedSessions((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  };

  const toggleAll = () => {
    if (selectedSessions.length === patientUnbilled.length) {
      setSelectedSessions([]);
    } else {
      setSelectedSessions(patientUnbilled.map((s) => s.id));
    }
  };

  const selectedPatient = patients.find((p) => p.id === Number(patientId));
  const patientDefaultValue = "0.00"; // Should come from patient data if available, stubbed here

  const totalValue = selectedSessions.reduce((acc, id) => {
    const session = patientUnbilled.find((s) => s.id === id);
    if (!session) return acc;
    const val =
      valueBase === "session"
        ? parseFloat(session.session_value)
        : parseFloat(patientDefaultValue);
    return acc + (isNaN(val) ? 0 : val);
  }, 0);

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Nova Cobrança"
      description="Selecione o paciente e as sessões para gerar uma cobrança"
      className="max-w-2xl"
    >
      <div className="space-y-6 pt-2">
        <div className="space-y-1.5">
          <label htmlFor={patientSelectId} className="text-sm font-semibold">Paciente</label>
          <select
            id={patientSelectId}
            value={patientId}
            onChange={(e) =>
              setPatientId(e.target.value ? Number(e.target.value) : "")
            }
            className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
          >
            <option value="">Selecione um paciente</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.full_name}
              </option>
            ))}
          </select>
        </div>

        {patientId !== "" && (
          <div className="space-y-4">
            <div className="space-y-3">
              <label className="text-sm font-semibold">
                Base do valor por sessão
              </label>

              <label
                className={`flex cursor-pointer gap-3 rounded-lg border p-4 transition-colors ${valueBase === "session" ? "border-blue-500 bg-blue-500/10" : "border-border"}`}
              >
                <input
                  type="radio"
                  name="valueBase"
                  className="mt-1"
                  checked={valueBase === "session"}
                  onChange={() => setValueBase("session")}
                />
                <div>
                  <div className="font-semibold text-sm">
                    Valor de cada sessão
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Usa o valor registrado em cada agendamento
                  </div>
                </div>
              </label>

              <label
                className={`flex cursor-pointer gap-3 rounded-lg border p-4 transition-colors ${valueBase === "patient" ? "border-blue-500 bg-blue-500/10" : "border-border"}`}
              >
                <input
                  type="radio"
                  name="valueBase"
                  className="mt-1"
                  checked={valueBase === "patient"}
                  onChange={() => setValueBase("patient")}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">
                      Valor da ficha do paciente
                    </span>
                    {/* Placeholder for missing value warning like in the design */}
                    <span className="text-xs text-destructive">
                      Nenhum valor cadastrado na ficha
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Usa o valor padrão cadastrado na ficha do paciente
                  </div>
                </div>
              </label>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-semibold">
                  Sessões Disponíveis para Cobrança
                </label>
                {patientUnbilled.length > 0 && (
                  <button
                    type="button"
                    onClick={toggleAll}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    {selectedSessions.length === patientUnbilled.length
                      ? "Desmarcar Todas"
                      : "Marcar Todas"}
                  </button>
                )}
              </div>

              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {patientUnbilled.length === 0 ? (
                  <div className="text-sm text-muted-foreground py-4 text-center border rounded-lg border-dashed">
                    Nenhuma sessão pendente para este paciente.
                  </div>
                ) : (
                  patientUnbilled.map((session) => {
                    const isSelected = selectedSessions.includes(session.id);
                    const val =
                      valueBase === "session"
                        ? session.session_value
                        : patientDefaultValue;

                    return (
                      <label
                        key={session.id}
                        className={`flex cursor-pointer items-center justify-between rounded-lg border p-3 transition-colors ${isSelected ? "border-blue-500/50 bg-blue-500/5" : "border-border"}`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSession(session.id)}
                            className="rounded border-input text-blue-500"
                          />
                          <div>
                            <div className="text-sm font-semibold">
                              {new Date(session.start_time).toLocaleDateString(
                                "pt-BR",
                              )}{" "}
                              às{" "}
                              {new Date(session.start_time).toLocaleTimeString(
                                "pt-BR",
                                { hour: "2-digit", minute: "2-digit" },
                              )}
                            </div>
                            <div className="text-xs text-muted-foreground mt-0.5">
                              Consulta
                            </div>
                          </div>
                        </div>
                        <div className="font-semibold text-blue-500 text-sm">
                          {formatCurrency(val)}
                        </div>
                      </label>
                    );
                  })
                )}
              </div>

              {patientUnbilled.length > 0 && (
                <div className="flex items-center justify-between rounded-lg bg-secondary/30 p-4 mt-2">
                  <span className="text-sm font-medium">
                    {selectedSessions.length} sessão(ões) selecionada(s)
                  </span>
                  <span className="text-lg font-bold text-blue-500">
                    {formatCurrency(totalValue.toString())}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="space-y-1.5">
          <label htmlFor={dueDateId} className="text-sm font-semibold">Vencimento</label>
          <Input
            id={dueDateId}
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor={paymentLinkId} className="text-sm font-semibold">Link de pagamento (opcional)</label>
          <Input
            id={paymentLinkId}
            type="url"
            placeholder="https://"
            value={paymentLink}
            aria-describedby={paymentLinkHintId}
            onChange={(e) => setPaymentLink(e.target.value)}
          />
          <p id={paymentLinkHintId} className="text-xs text-muted-foreground mt-1">
            Se informado, será incluído na cobrança via WhatsApp em vez dos
            dados bancários.
          </p>
        </div>

        <div className="space-y-1.5">
          <label htmlFor={notesId} className="text-sm font-semibold">Observações</label>
          <Textarea
            id={notesId}
            placeholder="Ex: Referente às sessões de janeiro/2026"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="resize-none"
          />
        </div>

        <label htmlFor={sendWhatsAppCheckboxId} className="flex items-center gap-2 cursor-pointer pt-2 select-none">
          <input
            id={sendWhatsAppCheckboxId}
            type="checkbox"
            checked={sendWhatsApp}
            onChange={(e) => setSendWhatsApp(e.target.checked)}
            className="rounded border-input text-blue-500"
          />
          <span className="text-sm text-muted-foreground">
            Enviar cobrança via WhatsApp após criar
          </span>
        </label>

        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">
            Criar Cobrança
          </Button>
        </div>
      </div>
    </Modal>
  );
}
