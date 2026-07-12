"use client";

import { useMemo, useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Download,
  MoreHorizontal,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { usePatients } from "@/features/patients/hooks/use-patients";
import { cn } from "@/lib/utils";
import {
  useAppointmentTransition,
  useAppointments,
  useRooms,
  useScheduleBlocks,
} from "../hooks/use-agenda";
import {
  addDays,
  periodBounds,
  startOfWeek,
  toDateInput,
} from "../lib/calendar.mjs";
import type { AgendaAppointment, AppointmentFilters } from "../types";
import {
  Field,
  FilterSelect,
  StatusBadge,
  Toolbar,
  formatDateTime,
  fieldClass,
} from "./agenda-ui";
import { DayView, MonthView, WeekView } from "./calendar-views";

export type AgendaView = "day" | "week" | "month";

export function AgendaCalendarPanel({
  selectedDate,
  view,
  onDateChange,
  onViewChange,
  onNewAppointment,
}: {
  selectedDate: Date;
  view: AgendaView;
  onDateChange: (date: Date) => void;
  onViewChange: (view: AgendaView) => void;
  onNewAppointment: (date: Date, time?: string) => void;
}) {
  const [patient, setPatient] = useState("");
  const [room, setRoom] = useState("");
  const [modality, setModality] = useState("");
  const [status, setStatus] = useState("");
  const [detail, setDetail] = useState<AgendaAppointment>();
  const bounds = periodBounds(selectedDate, view);
  const filters: AppointmentFilters = {
    start_time_gte: bounds.start.toISOString(),
    start_time_lte: bounds.end.toISOString(),
    patient: patient ? Number(patient) : undefined,
    room: room ? Number(room) : undefined,
    modality: modality || undefined,
    status: status || undefined,
    page_size: 100,
  };
  const { data: page, isLoading } = useAppointments(filters);
  const { data: blockPage } = useScheduleBlocks({
    start_time_gte: bounds.start.toISOString(),
    start_time_lte: bounds.end.toISOString(),
    page_size: 100,
  });
  const { data: patientsPage } = usePatients({ status: "active", page_size: 100 });
  const { data: rooms = [] } = useRooms();
  const appointments = page?.results || [];
  const blocks = blockPage?.results || [];
  const patients = patientsPage?.results || [];

  const periodLabel = useMemo(() => {
    if (view === "month") {
      return selectedDate.toLocaleDateString("pt-BR", {
        month: "long",
        year: "numeric",
      });
    }
    if (view === "week") {
      const start = startOfWeek(selectedDate);
      const end = addDays(start, 6);
      return `${start.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
      })} – ${end.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })}`;
    }
    return selectedDate.toLocaleDateString("pt-BR", {
      weekday: "long",
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  }, [selectedDate, view]);

  function navigate(direction: number) {
    if (view === "month") {
      onDateChange(
        new Date(
          selectedDate.getFullYear(),
          selectedDate.getMonth() + direction,
          1,
        ),
      );
    } else {
      onDateChange(addDays(selectedDate, direction * (view === "week" ? 7 : 1)));
    }
  }

  function exportCsv() {
    const header = [
      "Data",
      "Início",
      "Fim",
      "Paciente",
      "Profissional",
      "Modalidade",
      "Status",
      "Sala",
    ];
    const rows = appointments.map((item) => [
      toDateInput(item.start_time),
      new Date(item.start_time).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      new Date(item.end_time).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      item.patient_name,
      item.therapist_name,
      item.modality_display,
      item.status_display,
      item.room_name || "Sem sala",
    ]);
    const csv = [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `agenda-${toDateInput(selectedDate)}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast.success("Agenda exportada.");
  }

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex flex-col gap-3 border-b border-border p-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-2">
          <Button size="icon" variant="ghost" onClick={() => navigate(-1)} aria-label="Período anterior">
            <ChevronLeft className="size-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={() => onDateChange(new Date())}>
            Hoje
          </Button>
          <Button size="icon" variant="ghost" onClick={() => navigate(1)} aria-label="Próximo período">
            <ChevronRight className="size-4" />
          </Button>
          <h2 className="ml-2 text-sm font-semibold capitalize">{periodLabel}</h2>
        </div>
        <div className="inline-flex w-fit rounded-lg bg-secondary p-1">
          {(["day", "week", "month"] as const).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => onViewChange(item)}
              className={cn(
                "rounded-md px-4 py-2 text-xs font-semibold transition",
                view === item
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {item === "day" ? "Dia" : item === "week" ? "Semana" : "Mês"}
            </button>
          ))}
        </div>
      </div>

      <Toolbar>
        <CalendarDays className="size-4 text-muted-foreground" />
        <FilterSelect value={patient} onChange={setPatient} label="Paciente">
          <option value="">Paciente: todos</option>
          {patients.map((item) => (
            <option key={item.id} value={item.id}>
              {item.social_name || item.full_name}
            </option>
          ))}
        </FilterSelect>
        <FilterSelect value={room} onChange={setRoom} label="Sala">
          <option value="">Sala: todas</option>
          {rooms.map((item) => (
            <option key={item.id} value={item.id}>{item.name}</option>
          ))}
        </FilterSelect>
        <FilterSelect value={modality} onChange={setModality} label="Modalidade">
          <option value="">Modalidade: todas</option>
          <option value="in_person">Presencial</option>
          <option value="online">Online</option>
          <option value="hybrid">Híbrida</option>
        </FilterSelect>
        <FilterSelect value={status} onChange={setStatus} label="Status">
          <option value="">Status: todos</option>
          <option value="scheduled">Agendado</option>
          <option value="confirmed">Confirmado</option>
          <option value="completed">Realizado</option>
          <option value="missed">Falta</option>
          <option value="cancelled">Cancelado</option>
        </FilterSelect>
        <div className="ml-auto flex items-center gap-3 text-[11px] text-muted-foreground">
          <span><i className="mr-1 inline-block size-2 rounded-full bg-emerald-500" />Confirmado</span>
          <span><i className="mr-1 inline-block size-2 rounded-full bg-amber-500" />Pendente</span>
          <span><i className="mr-1 inline-block size-2 rounded-full bg-sky-500" />Realizado</span>
          <Button size="sm" variant="outline" leftIcon={<Download className="size-3.5" />} onClick={exportCsv}>
            Exportar
          </Button>
        </div>
      </Toolbar>

      <div className="overflow-auto">
        {isLoading ? (
          <div className="grid min-h-[520px] place-items-center text-sm text-muted-foreground">
            Carregando agenda...
          </div>
        ) : view === "month" ? (
          <MonthView
            currentDate={selectedDate}
            appointments={appointments}
            blocks={blocks}
            onSelectDate={(date) => {
              onDateChange(date);
              onViewChange("day");
            }}
            onSelectAppointment={setDetail}
          />
        ) : view === "week" ? (
          <WeekView
            currentDate={selectedDate}
            appointments={appointments}
            blocks={blocks}
            onNewAppointment={onNewAppointment}
            onSelectAppointment={setDetail}
          />
        ) : (
          <DayView
            currentDate={selectedDate}
            appointments={appointments}
            blocks={blocks}
            onNewAppointment={onNewAppointment}
            onSelectAppointment={setDetail}
          />
        )}
      </div>

      <AppointmentDetailModal appointment={detail} onClose={() => setDetail(undefined)} />
    </section>
  );
}

function AppointmentDetailModal({
  appointment,
  onClose,
}: {
  appointment?: AgendaAppointment;
  onClose: () => void;
}) {
  const transition = useAppointmentTransition();
  const [reason, setReason] = useState("");
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  if (!appointment) return null;

  function run(action: "confirm" | "cancel" | "complete" | "mark-no-show") {
    setPendingAction(action);
    transition.mutate(
      {
        id: appointment!.id,
        action,
        payload:
          action === "cancel" ? { cancellation_reason: reason } : undefined,
      },
      {
        onSuccess: onClose,
        onSettled: () => setPendingAction(null),
      },
    );
  }

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Detalhes da consulta"
      description={`${appointment.patient_name} · ${formatDateTime(appointment.start_time)}`}
      className="max-w-lg"
    >
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-3 rounded-lg border border-border p-4">
          <div>
            <strong className="block">{appointment.patient_name}</strong>
            <span className="text-sm text-muted-foreground">
              {appointment.type_display} · {appointment.modality_display}
            </span>
          </div>
          <StatusBadge status={appointment.status} />
        </div>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <Info label="Profissional" value={appointment.therapist_name} />
          <Info label="Duração" value={appointment.duration_display} />
          <Info label="Sala" value={appointment.room_name || "Sem sala"} />
          <Info
            label="Valor"
            value={Number(appointment.session_value).toLocaleString("pt-BR", {
              style: "currency",
              currency: "BRL",
            })}
          />
        </dl>
        {appointment.notes && (
          <div className="rounded-lg bg-secondary/30 p-3 text-sm">
            <strong className="mb-1 block text-xs">Observações</strong>
            {appointment.notes}
          </div>
        )}
        {appointment.status === "scheduled" && (
          <Field label="Motivo do cancelamento">
            <input
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Obrigatório apenas ao cancelar"
              className={fieldClass}
            />
          </Field>
        )}
        <div className="flex flex-wrap justify-end gap-2 border-t border-border pt-4">
          {appointment.status === "scheduled" && (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={() => run("mark-no-show")}
                isLoading={pendingAction === "mark-no-show"}
                disabled={transition.isPending}
              >
                Marcar falta
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => run("cancel")}
                isLoading={pendingAction === "cancel"}
                disabled={transition.isPending || !reason.trim()}
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={() => run("confirm")}
                isLoading={pendingAction === "confirm"}
                disabled={transition.isPending}
              >
                Confirmar
              </Button>
            </>
          )}
          {appointment.status === "confirmed" && (
            <Button
              size="sm"
              onClick={() => run("complete")}
              isLoading={pendingAction === "complete"}
              disabled={transition.isPending}
            >
              Marcar realizada
            </Button>
          )}
          <Button
            size="icon"
            variant="ghost"
            aria-label="Mais ações"
            disabled={transition.isPending}
          >
            <MoreHorizontal className="size-4" />
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <dt className="text-[11px] font-semibold uppercase text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}
