"use client";

import { useDeferredValue, useState } from "react";
import { Edit3, PackagePlus, Plus, Trash2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { useAuth } from "@/contexts/auth";
import {
  usePatientProfessionals,
  usePatients,
} from "@/features/patients/hooks/use-patients";
import {
  AGENDA_QUERY_KEYS,
  useCreatePackage,
  usePackages,
  useRooms,
} from "../hooks/use-agenda";
import { toDateInput } from "../lib/calendar.mjs";
import { agendaService } from "../services/agenda.service";
import type {
  CreateAppointmentPayload,
  CreatePackagePayload,
  PatientPackage,
} from "../types";
import {
  Field,
  FilterSelect,
  PaginationSummary,
  SearchInput,
  SectionLabel,
  StatusBadge,
  TableShell,
  Toggle,
  Toolbar,
  fieldClass,
  formatDate,
} from "./agenda-ui";

export function PackagesPanel() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<PatientPackage>();
  const deferredSearch = useDeferredValue(search);
  const { data: page, isLoading } = usePackages({
    search: deferredSearch || undefined,
    status: status || undefined,
    page_size: 50,
  });
  const rows = page?.results || [];

  return (
    <section className="space-y-4">
      <Toolbar>
        <SearchInput value={search} onChange={setSearch} placeholder="Pacote ou paciente..." />
        <FilterSelect value={status} onChange={setStatus} label="Status">
          <option value="">Status: todos</option>
          <option value="active">Ativo</option>
          <option value="paused">Pausado</option>
          <option value="completed">Sem saldo</option>
          <option value="expired">Expirado</option>
          <option value="cancelled">Cancelado</option>
        </FilterSelect>
        <Button
          className="ml-auto"
          size="sm"
          leftIcon={<PackagePlus className="size-4" />}
          onClick={() => setCreating(true)}
        >
          Novo pacote
        </Button>
      </Toolbar>

      <TableShell loading={isLoading} empty={!rows.length} emptyText="Nenhum pacote encontrado.">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-secondary/30 text-[11px] uppercase tracking-wide text-muted-foreground">
            <tr>
              {[
                "Paciente",
                "Profissional",
                "Pacote",
                "Sessões",
                "Criação",
                "Validade",
                "Status",
                "Ações",
              ].map((label) => (
                <th key={label} className="px-4 py-3 font-semibold">{label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const progress = row.sessions_contracted
                ? Math.min((row.sessions_used / row.sessions_contracted) * 100, 100)
                : 0;
              return (
                <tr key={row.id} className="border-t border-border hover:bg-secondary/15">
                  <td className="px-4 py-4 font-semibold">{row.patient_name}</td>
                  <td className="px-4 py-4 text-muted-foreground">{row.therapist_name}</td>
                  <td className="px-4 py-4">{row.name}</td>
                  <td className="min-w-52 px-4 py-4">
                    <div className="flex justify-between text-xs">
                      <strong>{row.sessions_used}/{row.sessions_contracted}</strong>
                      <span className={row.remaining_sessions ? "text-muted-foreground" : "text-destructive"}>
                        {row.remaining_sessions ? `${row.remaining_sessions} restantes` : "Sem saldo"}
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-secondary">
                      <div className="h-full rounded-full bg-primary" style={{ width: `${progress}%` }} />
                    </div>
                  </td>
                  <td className="px-4 py-4 text-muted-foreground">{formatDate(row.created_at)}</td>
                  <td className="px-4 py-4 text-muted-foreground">{row.valid_until ? formatDate(row.valid_until) : "Sem limite"}</td>
                  <td className="px-4 py-4"><StatusBadge status={row.status} /></td>
                  <td className="px-4 py-4">
                    <Button size="icon" variant="ghost" onClick={() => setEditing(row)} aria-label="Editar sessões">
                      <Edit3 className="size-4" />
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </TableShell>
      <PaginationSummary page={page?.pagination} />
      <CreatePackageModal open={creating} onClose={() => setCreating(false)} />
      <PackageSessionsModal packageItem={editing} onClose={() => setEditing(undefined)} />
    </section>
  );
}

function CreatePackageModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user } = useAuth();
  const mutation = useCreatePackage();
  const { data: patientsPage } = usePatients({ status: "active", page_size: 100 });
  const { data: professionals = [] } = usePatientProfessionals();
  const { data: rooms = [] } = useRooms();
  const [form, setForm] = useState({
    patient: "",
    therapist: String(user?.id || ""),
    name: "",
    sessions: "10",
    totalValue: "0.00",
    description: "",
    autoSchedule: true,
    firstDate: toDateInput(new Date()),
    time: "09:00",
    frequency: "weekly",
    duration: "50",
    modality: "in_person",
    room: "",
    reminder: true,
    generateCharge: false,
    sendCharge: false,
  });
  const patients = patientsPage?.results || [];
  const unitValue = Number(form.sessions) > 0
    ? Number(form.totalValue || 0) / Number(form.sessions)
    : 0;

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const first = new Date(`${form.firstDate}T${form.time}:00`);
    const payload: CreatePackagePayload = {
      patient: Number(form.patient),
      therapist: form.therapist ? Number(form.therapist) : undefined,
      name: form.name,
      sessions_contracted: Number(form.sessions),
      total_value: Number(form.totalValue || 0).toFixed(2),
      description: form.description,
      generate_charge: form.generateCharge,
      send_charge: form.sendCharge,
      auto_schedule: form.autoSchedule,
      first_appointment_at: form.autoSchedule ? first.toISOString() : undefined,
      frequency: form.frequency,
      duration_minutes: Number(form.duration),
      modality: form.modality as CreatePackagePayload["modality"],
      room: form.modality === "online" || !form.room ? null : Number(form.room),
      appointment_type: "psychotherapy",
      send_whatsapp_reminder: form.reminder,
    };
    mutation.mutate(payload, { onSuccess: onClose });
  }

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Novo pacote de atendimentos"
      description="Crie o pacote e gere as sessões automaticamente."
      className="max-w-2xl"
    >
      <form onSubmit={submit} className="space-y-5">
        <section className="space-y-3">
          <SectionLabel>Paciente e profissional</SectionLabel>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Paciente *">
              <select value={form.patient} onChange={(event) => setForm((current) => ({ ...current, patient: event.target.value }))} className={fieldClass} required>
                <option value="">Selecione</option>
                {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.social_name || patient.full_name}</option>)}
              </select>
            </Field>
            <Field label="Profissional *">
              <select value={form.therapist} onChange={(event) => setForm((current) => ({ ...current, therapist: event.target.value }))} className={fieldClass} disabled={user?.role === "therapist"} required>
                <option value="">Selecione</option>
                {professionals.map((professional) => <option key={professional.id} value={professional.id}>{professional.full_name}</option>)}
              </select>
            </Field>
          </div>
          <Field label="Nome do pacote *">
            <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="Ex.: Pacote 10 sessões" className={fieldClass} required />
          </Field>
        </section>

        <section className="space-y-3 border-t border-border pt-4">
          <SectionLabel>Sessões e valor</SectionLabel>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Quantidade">
              <input type="number" min={1} value={form.sessions} onChange={(event) => setForm((current) => ({ ...current, sessions: event.target.value }))} className={fieldClass} />
            </Field>
            <Field label="Valor total">
              <input inputMode="decimal" value={form.totalValue} onChange={(event) => setForm((current) => ({ ...current, totalValue: event.target.value.replace(",", ".") }))} className={fieldClass} />
            </Field>
            <Field label="Por sessão">
              <input value={unitValue.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} disabled className={fieldClass} />
            </Field>
          </div>
          <Field label="Descrição">
            <textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} rows={3} className="w-full rounded-md border border-border bg-background p-3 text-sm" />
          </Field>
        </section>

        <section className="space-y-3 border-t border-border pt-4">
          <Toggle checked={form.autoSchedule} onChange={(value) => setForm((current) => ({ ...current, autoSchedule: value }))} label="Agendar sessões automaticamente" />
          {form.autoSchedule && (
            <div className="grid gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4 sm:grid-cols-2">
              <Field label="Primeiro atendimento">
                <input type="date" value={form.firstDate} onChange={(event) => setForm((current) => ({ ...current, firstDate: event.target.value }))} className={fieldClass} />
              </Field>
              <Field label="Horário">
                <input type="time" value={form.time} onChange={(event) => setForm((current) => ({ ...current, time: event.target.value }))} className={fieldClass} />
              </Field>
              <Field label="Frequência">
                <select value={form.frequency} onChange={(event) => setForm((current) => ({ ...current, frequency: event.target.value }))} className={fieldClass}>
                  <option value="weekly">Semanal</option>
                  <option value="biweekly">Quinzenal</option>
                  <option value="monthly">Mensal</option>
                </select>
              </Field>
              <Field label="Duração">
                <select value={form.duration} onChange={(event) => setForm((current) => ({ ...current, duration: event.target.value }))} className={fieldClass}>
                  {[30, 45, 50, 60, 90].map((value) => <option key={value} value={value}>{value} min</option>)}
                </select>
              </Field>
              <Field label="Modalidade">
                <select value={form.modality} onChange={(event) => setForm((current) => ({ ...current, modality: event.target.value, room: event.target.value === "online" ? "" : current.room }))} className={fieldClass}>
                  <option value="in_person">Presencial</option>
                  <option value="online">Online</option>
                  <option value="hybrid">Híbrida</option>
                </select>
              </Field>
              <Field label="Sala">
                <select value={form.room} onChange={(event) => setForm((current) => ({ ...current, room: event.target.value }))} disabled={form.modality === "online"} className={fieldClass}>
                  <option value="">Sem sala</option>
                  {rooms.map((room) => <option key={room.id} value={room.id}>{room.name}</option>)}
                </select>
              </Field>
            </div>
          )}
          <Toggle checked={form.reminder} onChange={(value) => setForm((current) => ({ ...current, reminder: value }))} label="Enviar lembretes automáticos" />
          <Toggle checked={form.generateCharge} onChange={(value) => setForm((current) => ({ ...current, generateCharge: value }))} label="Gerar cobrança no financeiro" />
          <Toggle checked={form.sendCharge} onChange={(value) => setForm((current) => ({ ...current, sendCharge: value }))} label="Marcar cobrança para envio" />
        </section>

        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button type="button" variant="outline" onClick={onClose}>Cancelar</Button>
          <Button type="submit" isLoading={mutation.isPending}>Criar pacote</Button>
        </div>
      </form>
    </Modal>
  );
}

function PackageSessionsModal({
  packageItem,
  onClose,
}: {
  packageItem?: PatientPackage;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [adding, setAdding] = useState(false);
  const [date, setDate] = useState(toDateInput(new Date()));
  const [time, setTime] = useState("09:00");
  const removeMutation = useMutation({
    mutationFn: agendaService.packages.removeSession,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.packages });
      await queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.appointments });
      toast.success("Sessão removida e saldo recalculado.");
    },
  });
  const addMutation = useMutation({
    mutationFn: () => {
      const start = new Date(`${date}T${time}:00`);
      const payload: CreateAppointmentPayload = {
        patient: packageItem!.patient,
        therapist: packageItem!.therapist,
        start_time: start.toISOString(),
        end_time: new Date(start.getTime() + 50 * 60_000).toISOString(),
        modality: "in_person",
        appointment_type: "psychotherapy",
        session_value: packageItem!.unit_value,
        package: packageItem!.id,
      };
      return agendaService.packages.addSession(packageItem!.id, payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.packages });
      await queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.appointments });
      toast.success("Sessão adicionada.");
      setAdding(false);
    },
  });

  return (
    <Modal
      isOpen={Boolean(packageItem)}
      onClose={onClose}
      title={packageItem ? `Editar sessões – ${packageItem.name}` : "Editar sessões"}
      description={packageItem ? `${packageItem.patient_name} · ${packageItem.sessions_used}/${packageItem.sessions_contracted} sessões` : undefined}
      className="max-w-2xl"
    >
      <div className="space-y-3">
        <div className="max-h-[55vh] space-y-2 overflow-y-auto pr-1">
          {packageItem?.sessions.map((session, index) => (
            <div key={session.id} className="flex items-center gap-3 rounded-lg border border-border p-3">
              <span className="w-6 text-center text-xs font-semibold text-muted-foreground">{index + 1}</span>
              <div className="grid flex-1 grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                <span>{formatDate(session.scheduled_for)}</span>
                <span>{new Date(session.scheduled_for).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</span>
                <StatusBadge status={session.status} />
              </div>
              <Button size="icon" variant="ghost" aria-label="Remover sessão" disabled={session.status === "completed"} onClick={() => removeMutation.mutate(session.id)}>
                <Trash2 className="size-4" />
              </Button>
            </div>
          ))}
          {!packageItem?.sessions.length && <p className="py-8 text-center text-sm text-muted-foreground">Nenhuma sessão vinculada.</p>}
        </div>

        {adding ? (
          <div className="grid grid-cols-2 gap-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
            <Field label="Data"><input type="date" value={date} onChange={(event) => setDate(event.target.value)} className={fieldClass} /></Field>
            <Field label="Horário"><input type="time" value={time} onChange={(event) => setTime(event.target.value)} className={fieldClass} /></Field>
            <div className="col-span-2 flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={() => setAdding(false)}>Cancelar</Button>
              <Button size="sm" isLoading={addMutation.isPending} onClick={() => addMutation.mutate()}>Adicionar</Button>
            </div>
          </div>
        ) : (
          <Button variant="outline" className="w-full border-dashed" leftIcon={<Plus className="size-4" />} onClick={() => setAdding(true)} disabled={!packageItem?.remaining_sessions}>
            Adicionar sessão
          </Button>
        )}
        <div className="flex justify-end border-t border-border pt-4"><Button variant="outline" onClick={onClose}>Fechar</Button></div>
      </div>
    </Modal>
  );
}
