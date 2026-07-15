import { CalendarDays, FileText, Settings2, UsersRound, X } from "lucide-react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { SafePatientPanelData } from "../panel-contracts";

interface Props {
  data?: SafePatientPanelData;
  loading: boolean;
  onClose?: () => void;
}

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function formatDate(value?: string | null) {
  if (!value) return "Não agendado";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function PatientSidePanel({ data, loading, onClose }: Props) {
  const router = useRouter();

  if (loading) {
    return (
      <aside className="h-[32rem] animate-pulse rounded-xl border border-border bg-card" />
    );
  }

  if (!data) {
    return (
      <aside className="grid min-h-72 place-items-center rounded-xl border border-dashed border-border bg-card p-6">
        <EmptyState
          icon={<UsersRound className="h-6 w-6 text-muted-foreground" />}
          title="Selecione um paciente"
          description="O resumo administrativo aparecerá neste painel."
        />
      </aside>
    );
  }

  const patient = data.patient;
  const attendance = data.follow_up.attendance_percentage;

  return (
    <aside className="overflow-hidden rounded-xl border border-border bg-card xl:sticky xl:top-4">
      <header className="border-b border-border p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-primary/30 bg-primary/10 text-sm font-bold text-primary">
              {initials(patient.display_name)}
            </span>
            <div className="min-w-0">
              <h2 className="truncate text-base font-bold text-foreground">
                {patient.display_name}
              </h2>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {patient.age ? `${patient.age} anos` : "Idade não informada"} •{" "}
                {patient.masked_cpf}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant={patient.status === "active" ? "success" : "outline"}
            >
              {patient.status_display}
            </Badge>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="grid h-8 w-8 place-items-center rounded-md text-muted-foreground transition hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
                aria-label="Fechar painel"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <div className="mt-3 space-y-1 text-[11px] text-muted-foreground">
          <p>{patient.phone || "Telefone não informado"}</p>
          <p className="truncate">{patient.email || "E-mail não informado"}</p>
        </div>
      </header>

      <div className="grid grid-cols-2 border-b border-border">
        <button
          type="button"
          onClick={() => router.push(`/dashboard/patients/${patient.id}`)}
          className="flex items-center justify-center gap-2 border-r border-border px-3 py-3 text-[10px] font-semibold text-foreground hover:bg-primary/8 hover:text-primary"
        >
          <Settings2 className="h-4 w-4" /> Gerenciar cadastro
        </button>
        <button
          type="button"
          onClick={() => router.push(`/dashboard/agenda?patient=${patient.id}`)}
          className="flex items-center justify-center gap-2 px-3 py-3 text-[10px] font-semibold text-foreground hover:bg-primary/8 hover:text-primary"
        >
          <CalendarDays className="h-4 w-4" /> Agendar sessão
        </button>
      </div>

      <div className="space-y-3 p-3">
        <section className="rounded-lg border border-border bg-secondary/25 p-3">
          <div className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground">
            <CalendarDays className="h-3.5 w-3.5 text-primary" /> Próxima sessão
          </div>
          {data.next_session ? (
            <strong className="mt-3 block text-sm text-foreground">
              {formatDate(data.next_session.start_time)}
            </strong>
          ) : (
            <Button
              size="sm"
              variant="outline"
              className="mt-3 w-full"
              onClick={() =>
                router.push(`/dashboard/agenda?patient=${patient.id}`)
              }
            >
              Agendar sessão
            </Button>
          )}
        </section>

        <section className="rounded-lg border border-border bg-secondary/25 p-3">
          <div className="flex items-center justify-between text-[10px] font-semibold text-muted-foreground">
            <span>Acompanhamento</span>
            <span>{data.follow_up.total_sessions} sessões</span>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            <div>
              <strong className="block text-sm text-foreground">
                {attendance ?? "—"}
                {attendance !== null ? "%" : ""}
              </strong>
              <span className="text-[9px] text-muted-foreground">Adesão</span>
            </div>
            <div>
              <strong className="block text-sm text-foreground">
                {data.follow_up.missed_sessions}
              </strong>
              <span className="text-[9px] text-muted-foreground">Faltas</span>
            </div>
            <div>
              <strong className="block text-sm text-foreground">
                {data.follow_up.active_goals}
              </strong>
              <span className="text-[9px] text-muted-foreground">Metas</span>
            </div>
          </div>
        </section>

        {data.can_access_records && (
          <Button
            variant="outline"
            className="w-full"
            onClick={() => router.push(`/dashboard/records/${patient.id}`)}
            leftIcon={<FileText className="h-4 w-4" />}
          >
            Abrir prontuário
          </Button>
        )}
      </div>
    </aside>
  );
}
