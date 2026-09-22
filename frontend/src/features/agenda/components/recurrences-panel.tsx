"use client";

import { useDeferredValue, useEffect, useId, useState } from "react";
import { Edit3, Pause, Play, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { useRecurrenceAction, useRecurrences } from "../hooks/use-agenda";
import { agendaService } from "../services/agenda.service";
import type { AppointmentRecurrence } from "../types";
import {
  Field,
  FilterSelect,
  PaginationSummary,
  SearchInput,
  StatusBadge,
  TableShell,
  Toolbar,
  fieldClass,
  formatDate,
} from "./agenda-ui";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { AGENDA_QUERY_KEYS } from "../hooks/use-agenda";

export function RecurrencesPanel() {
  const [search, setSearch] = useState("");
  const [frequency, setFrequency] = useState("");
  const [status, setStatus] = useState("active");
  const [editing, setEditing] = useState<AppointmentRecurrence>();
  const deferredSearch = useDeferredValue(search);
  const { data: page, isLoading } = useRecurrences({
    search: deferredSearch || undefined,
    frequency: frequency || undefined,
    status: status || undefined,
    page_size: 50,
  });
  const action = useRecurrenceAction();
  const rows = page?.results || [];

  return (
    <section className="space-y-4">
      <Toolbar>
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Buscar paciente ou profissional..."
        />
        <FilterSelect
          value={frequency}
          onChange={setFrequency}
          label="Frequência"
        >
          <option value="">Frequência: todas</option>
          <option value="weekly">Semanal</option>
          <option value="biweekly">Quinzenal</option>
          <option value="monthly">Mensal</option>
        </FilterSelect>
        <FilterSelect value={status} onChange={setStatus} label="Status">
          <option value="">Status: todos</option>
          <option value="active">Ativas</option>
          <option value="paused">Pausadas</option>
          <option value="ended">Encerradas</option>
        </FilterSelect>
      </Toolbar>

      <TableShell
        loading={isLoading}
        empty={!rows.length}
        emptyText="Nenhuma recorrência encontrada."
      >
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-secondary/30 text-[11px] uppercase tracking-wide text-muted-foreground">
            <tr>
              {[
                "Paciente",
                "Profissional",
                "Dia/Hora",
                "Frequência",
                "Início",
                "Término",
                "Sessões",
                "Status",
                "Ações",
              ].map((label) => (
                <th key={label} className="px-4 py-3 font-semibold">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                className="border-t border-border hover:bg-secondary/15"
              >
                <td className="px-4 py-4 font-semibold">{row.patient_name}</td>
                <td className="px-4 py-4 text-muted-foreground">
                  {row.therapist_name}
                </td>
                <td className="px-4 py-4">
                  {row.next_occurrence_at
                    ? new Date(row.next_occurrence_at).toLocaleDateString(
                        "pt-BR",
                        { weekday: "short" },
                      )
                    : "—"}{" "}
                  <strong>{row.start_time.slice(0, 5)}</strong>
                </td>
                <td className="px-4 py-4">{row.frequency_display}</td>
                <td className="px-4 py-4 text-muted-foreground">
                  {formatDate(row.starts_on)}
                </td>
                <td className="px-4 py-4 text-muted-foreground">
                  {row.ends_on ? formatDate(row.ends_on) : "Sem limite"}
                </td>
                <td className="px-4 py-4">
                  {row.completed_count} realizadas / {row.occurrences_count}{" "}
                  geradas
                </td>
                <td className="px-4 py-4">
                  <StatusBadge status={row.status} />
                </td>
                <td className="px-4 py-4">
                  <div className="flex justify-end gap-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => setEditing(row)}
                      disabled={action.isPending}
                      aria-label="Editar recorrência"
                    >
                      <Edit3 className="size-4" aria-hidden="true" />
                    </Button>
                    {row.status === "active" ? (
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() =>
                          action.mutate({ id: row.id, action: "pause" })
                        }
                        disabled={action.isPending}
                        aria-label="Pausar"
                      >
                        <Pause className="size-4" aria-hidden="true" />
                      </Button>
                    ) : row.status === "paused" ? (
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() =>
                          action.mutate({ id: row.id, action: "reactivate" })
                        }
                        disabled={action.isPending}
                        aria-label="Reativar"
                      >
                        <Play className="size-4" aria-hidden="true" />
                      </Button>
                    ) : null}
                    {row.status !== "ended" && (
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() =>
                          action.mutate({ id: row.id, action: "end" })
                        }
                        disabled={action.isPending}
                        aria-label="Encerrar"
                      >
                        <Square className="size-4 text-destructive" aria-hidden="true" />
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
      <PaginationSummary page={page?.pagination} />
      <RecurrenceEditModal
        item={editing}
        onClose={() => setEditing(undefined)}
      />
    </section>
  );
}

function RecurrenceEditModal({
  item,
  onClose,
}: {
  item?: AppointmentRecurrence;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const timeInputId = useId();
  const durationSelectId = useId();
  const modalitySelectId = useId();

  const [scope, setScope] = useState<"occurrence" | "following" | "all">(
    "following",
  );
  const [time, setTime] = useState(item?.start_time.slice(0, 5) || "09:00");
  const [duration, setDuration] = useState(
    String(item?.duration_minutes || 50),
  );
  const [modality, setModality] = useState(item?.modality || "in_person");

  useEffect(() => {
    if (item) {
      setTime(item.start_time.slice(0, 5));
      setDuration(String(item.duration_minutes));
      setModality(item.modality);
      setScope("following");
    }
  }, [item]);

  const mutation = useMutation({
    mutationFn: () =>
      agendaService.recurrences.applyChange(item!.id, {
        scope,
        occurrence_id: item!.next_occurrence_id!,
        changes: {
          start_time: time,
          duration_minutes: Number(duration),
          modality,
        },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: AGENDA_QUERY_KEYS.recurrences,
      });
      await queryClient.invalidateQueries({
        queryKey: AGENDA_QUERY_KEYS.appointments,
      });
      toast.success("Recorrência atualizada.");
      onClose();
    },
  });

  const handleClose = () => {
    if (mutation.isPending) return;
    onClose();
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (mutation.isPending || !item?.next_occurrence_id) return;
    mutation.mutate();
  };

  if (!item) return null;
  return (
    <Modal
      isOpen
      onClose={handleClose}
      title="Editar recorrência"
      description={`${item.patient_name} · ${item.frequency_display}`}
      className="max-w-lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <fieldset disabled={mutation.isPending} className="space-y-1.5">
          <legend className="text-xs font-semibold text-foreground">
            Aplicar alteração em
          </legend>
          <div className="space-y-2 rounded-lg border border-border p-3 text-sm">
            {[
              ["occurrence", "Apenas o próximo agendamento"],
              ["following", "Este e os seguintes"],
              ["all", "Todos da recorrência"],
            ].map(([value, label]) => (
              <label key={value} className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name="recurrence-scope"
                  value={value}
                  checked={scope === value}
                  onChange={() => setScope(value as typeof scope)}
                  disabled={mutation.isPending}
                  className="accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                />
                <span className="text-sm font-normal text-foreground">{label}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Horário">
            <input
              id={timeInputId}
              type="time"
              value={time}
              onChange={(event) => setTime(event.target.value)}
              disabled={mutation.isPending}
              className={fieldClass}
            />
          </Field>
          <Field label="Duração">
            <select
              id={durationSelectId}
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
              disabled={mutation.isPending}
              className={fieldClass}
            >
              {[30, 45, 50, 60, 90].map((value) => (
                <option key={value} value={value}>
                  {value} min
                </option>
              ))}
            </select>
          </Field>
        </div>
        <Field label="Modalidade">
          <select
            id={modalitySelectId}
            value={modality}
            onChange={(event) =>
              setModality(
                event.target.value as AppointmentRecurrence["modality"],
              )
            }
            disabled={mutation.isPending}
            className={fieldClass}
          >
            <option value="in_person">Presencial</option>
            <option value="online">Online</option>
            <option value="hybrid">Híbrida</option>
          </select>
        </Field>
        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={mutation.isPending}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            isLoading={mutation.isPending}
            disabled={mutation.isPending || !item.next_occurrence_id}
          >
            Salvar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
