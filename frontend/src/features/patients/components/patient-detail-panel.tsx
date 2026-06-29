import {
  CalendarDays,
  FileText,
  FolderOpen,
  MessageCircle,
  NotebookPen,
  Sparkles,
  Target,
} from "lucide-react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PatientPanelData } from "../types";

interface Props {
  data?: PatientPanelData;
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

function formatDate(value?: string | null, withTime = false) {
  if (!value) return "Não informado";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(new Date(value));
}

export function PatientDetailPanel({ data, loading, onClose }: Props) {
  const router = useRouter();

  if (loading) {
    return <aside className="h-[42rem] animate-pulse rounded-xl border border-border bg-card" />;
  }

  if (!data) {
    return (
      <aside className="grid min-h-80 place-items-center rounded-xl border border-dashed border-border bg-card p-6 text-center">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Selecione um paciente</h2>
          <p className="mt-2 text-xs text-muted-foreground">
            Os dados de acompanhamento aparecerão aqui sem sair da listagem.
          </p>
        </div>
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
              <h2 className="truncate text-base font-bold text-foreground">{patient.display_name}</h2>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {patient.age ? `${patient.age} anos` : "Idade não informada"} • {patient.masked_cpf}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={patient.status === "active" ? "success" : "outline"}>
              {patient.status_display}
            </Badge>
            {onClose && (
              <button type="button" onClick={onClose} className="rounded-md px-2 py-1 text-muted-foreground hover:bg-secondary" aria-label="Fechar painel">
                ×
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
        <button type="button" onClick={() => router.push(`/dashboard/records/${patient.id}`)} className="flex items-center justify-center gap-2 border-r border-border px-3 py-3 text-[10px] font-semibold text-foreground hover:bg-primary/8 hover:text-primary">
          <NotebookPen className="h-4 w-4" /> Ver prontuário
        </button>
        <button type="button" onClick={() => router.push(`/dashboard/agenda?patient=${patient.id}`)} className="flex items-center justify-center gap-2 px-3 py-3 text-[10px] font-semibold text-foreground hover:bg-primary/8 hover:text-primary">
          <CalendarDays className="h-4 w-4" /> Agendar sessão
        </button>
        <button type="button" onClick={() => router.push(`/dashboard/records/${patient.id}?new=evolution`)} className="flex items-center justify-center gap-2 border-r border-t border-border px-3 py-3 text-[10px] font-semibold text-foreground hover:bg-primary/8 hover:text-primary">
          <FileText className="h-4 w-4" /> Nova evolução
        </button>
        <button type="button" disabled className="flex items-center justify-center gap-2 border-t border-border px-3 py-3 text-[10px] font-semibold text-muted-foreground disabled:cursor-not-allowed disabled:opacity-60">
          <MessageCircle className="h-4 w-4" /> Mensagem indisponível
        </button>
      </div>

      <div className="space-y-3 p-3">
        <section className="rounded-lg border border-border bg-secondary/25 p-3">
          <div className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground">
            <CalendarDays className="h-3.5 w-3.5 text-primary" /> Próxima sessão
          </div>
          {data.next_session ? (
            <div className="mt-3">
              <strong className="text-sm text-foreground">{formatDate(data.next_session.start_time, true)}</strong>
              <p className="mt-1 text-[10px] text-muted-foreground">{patient.modality === "online" ? "Atendimento online" : "Atendimento presencial"}</p>
            </div>
          ) : (
            <div className="mt-3">
              <p className="text-xs text-muted-foreground">Nenhuma sessão futura agendada.</p>
              <Button size="sm" variant="outline" className="mt-3 w-full" onClick={() => router.push(`/dashboard/agenda?patient=${patient.id}`)}>
                Agendar sessão
              </Button>
            </div>
          )}
        </section>

        <section className="rounded-lg border border-border bg-secondary/25 p-3">
          <div className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground">
            <NotebookPen className="h-3.5 w-3.5 text-primary" /> Última evolução
          </div>
          {data.latest_evolution ? (
            <div className="mt-3">
              <p className="text-[10px] text-muted-foreground">{formatDate(data.latest_evolution.session_date)}</p>
              <p className="mt-2 line-clamp-3 text-[11px] leading-5 text-foreground">{data.latest_evolution.summary}</p>
              <button type="button" onClick={() => router.push(`/dashboard/records/${patient.id}`)} className="mt-3 text-[10px] font-semibold text-primary hover:underline">
                Ver evolução completa
              </button>
            </div>
          ) : (
            <p className="mt-3 text-xs text-muted-foreground">Nenhuma evolução registrada.</p>
          )}
        </section>

        <section className="rounded-lg border border-border bg-secondary/25 p-3">
          <div className="flex items-center justify-between text-[10px] font-semibold text-muted-foreground">
            <span className="flex items-center gap-2"><Target className="h-3.5 w-3.5 text-primary" /> Acompanhamento</span>
            <span>{data.follow_up.total_sessions} sessões</span>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            <div><strong className="block text-sm text-foreground">{attendance ?? "—"}{attendance !== null ? "%" : ""}</strong><span className="text-[9px] text-muted-foreground">Adesão</span></div>
            <div><strong className="block text-sm text-foreground">{data.follow_up.missed_sessions}</strong><span className="text-[9px] text-muted-foreground">Faltas</span></div>
            <div><strong className="block text-sm text-foreground">{data.follow_up.active_goals}</strong><span className="text-[9px] text-muted-foreground">Metas</span></div>
          </div>
        </section>

        <section className="rounded-lg border border-border bg-secondary/25 p-3">
          <div className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground">
            <FolderOpen className="h-3.5 w-3.5 text-primary" /> Documentos recentes
          </div>
          {data.recent_documents.length ? (
            <div className="mt-2 divide-y divide-border/70">
              {data.recent_documents.map((document) => (
                <div key={document.id} className="py-2">
                  <p className="truncate text-[11px] font-medium text-foreground">{document.name}</p>
                  <p className="mt-0.5 text-[9px] text-muted-foreground">{document.category} • {formatDate(document.created_at)}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-xs text-muted-foreground">Nenhum documento anexado.</p>
          )}
        </section>

        <section className="rounded-lg border border-dashed border-border bg-secondary/20 p-3">
          <div className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-primary" /> Resumo assistido por IA
          </div>
          <p className="mt-2 text-[10px] leading-4 text-muted-foreground">{data.ai_summary.message}</p>
        </section>
      </div>
    </aside>
  );
}
