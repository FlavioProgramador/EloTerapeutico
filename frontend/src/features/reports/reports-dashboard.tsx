"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BarChart3, CalendarDays, Download, DollarSign, FileText, RefreshCw, TrendingUp, Users } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { reportsService, type ReportParams } from "./report-service";
import type { AppointmentsReport, ChartPoint, PatientsReport, ReportTab } from "./types";

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const percent = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });

const tabs: Array<{ key: ReportTab; label: string; icon: typeof CalendarDays }> = [
  { key: "appointments", label: "Atendimentos", icon: CalendarDays },
  { key: "patients", label: "Pacientes", icon: Users },
  { key: "financial", label: "Financeiro", icon: DollarSign },
  { key: "online-scheduling", label: "Agendamento Online", icon: TrendingUp },
];

const periodOptions = [
  { value: "today", label: "Hoje" },
  { value: "this_week", label: "Esta semana" },
  { value: "this_month", label: "Este mes" },
  { value: "last_30_days", label: "Ultimos 30 dias" },
  { value: "last_90_days", label: "Ultimos 90 dias" },
  { value: "this_year", label: "Este ano" },
  { value: "custom", label: "Personalizado" },
];

function toNumber(value: unknown) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR");
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function MetricCard({ title, value, note, icon: Icon, tone = "primary" }: { title: string; value: string; note?: string; icon: typeof CalendarDays; tone?: "primary" | "success" | "warning" | "danger" }) {
  const tones = {
    primary: "bg-primary/10 text-primary",
    success: "bg-success/10 text-success",
    warning: "bg-warning/10 text-warning",
    danger: "bg-danger/10 text-danger",
  };
  return (
    <Card className="overflow-hidden border-primary/10 bg-card/95">
      <CardContent className="flex min-h-28 items-start justify-between p-5">
        <div>
          <p className="text-xs font-semibold text-muted-foreground">{title}</p>
          <p className="mt-3 text-2xl font-bold tracking-tight text-foreground">{value}</p>
          {note && <p className="mt-1 text-[11px] text-muted-foreground">{note}</p>}
        </div>
        <span className={cn("grid h-10 w-10 place-items-center rounded-xl", tones[tone])}>
          <Icon className="h-4 w-4" />
        </span>
      </CardContent>
    </Card>
  );
}

function EmptyState({ message }: { message: string }) {
  return <div className="grid min-h-44 place-items-center rounded-xl border border-dashed border-border/80 bg-background/20 px-6 text-center text-sm text-muted-foreground">{message}</div>;
}

function ChartCard({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return <Card className={cn("border-primary/10 bg-card/95", className)}><CardHeader className="pb-3"><CardTitle className="text-sm font-bold">{title}</CardTitle></CardHeader><CardContent>{children}</CardContent></Card>;
}

function BarChart({ points, moneyMode = false }: { points: ChartPoint[]; moneyMode?: boolean }) {
  const max = Math.max(1, ...points.map((item) => toNumber(item.value)));
  if (!points.some((item) => toNumber(item.value) > 0)) return <EmptyState message="Nenhum dado para exibir neste periodo." />;
  return (
    <div className="flex h-64 items-end gap-3 border-b border-l border-border px-3 pb-8">
      {points.map((item) => {
        const value = toNumber(item.value);
        return <div key={item.label} className="relative flex h-full flex-1 items-end justify-center"><div className="w-full max-w-14 rounded-t-lg bg-primary/80 shadow-sm shadow-primary/10" style={{ height: `${Math.max(3, (value / max) * 100)}%` }} title={moneyMode ? money.format(value) : String(value)} /><span className="absolute -bottom-7 max-w-20 truncate text-[10px] text-muted-foreground">{item.label}</span></div>;
      })}
    </div>
  );
}

function HorizontalBars({ points, moneyMode = false }: { points: ChartPoint[]; moneyMode?: boolean }) {
  const max = Math.max(1, ...points.map((item) => toNumber(item.value)));
  if (!points.some((item) => toNumber(item.value) > 0)) return <EmptyState message="Nenhum dado para exibir neste periodo." />;
  return <div className="space-y-4">{points.map((item) => { const value = toNumber(item.value); return <div key={item.label} className="grid gap-1.5"><div className="flex items-center justify-between gap-3 text-xs"><span className="truncate text-muted-foreground">{item.label}</span><strong>{moneyMode ? money.format(value) : value}</strong></div><div className="h-2 overflow-hidden rounded-full bg-secondary"><div className="h-full rounded-full bg-primary" style={{ width: `${Math.max(2, (value / max) * 100)}%` }} /></div></div>; })}</div>;
}

function DonutChart({ points }: { points: ChartPoint[] }) {
  const total = points.reduce((sum, item) => sum + toNumber(item.value), 0);
  if (!total) return <EmptyState message="Nenhum dado para exibir neste periodo." />;
  const palette = ["hsl(var(--primary))", "hsl(var(--success))", "hsl(var(--warning))", "hsl(var(--danger))", "hsl(var(--muted-foreground))"];
  const segments = points.map((item, index) => {
    const start = points.slice(0, index).reduce((sum, current) => sum + (toNumber(current.value) / total) * 100, 0);
    const end = start + (toNumber(item.value) / total) * 100;
    return `${palette[index % palette.length]} ${start}% ${end}%`;
  });
  return <div className="grid gap-5 md:grid-cols-[12rem_1fr] md:items-center"><div className="mx-auto grid h-44 w-44 place-items-center rounded-full" style={{ background: `conic-gradient(${segments.join(",")})` }}><div className="grid h-24 w-24 place-items-center rounded-full bg-card text-center"><span className="text-2xl font-bold">{total}</span></div></div><div className="space-y-2">{points.map((item, index) => <div key={item.label} className="flex items-center justify-between gap-3 text-xs"><span className="flex items-center gap-2 text-muted-foreground"><i className="h-2.5 w-2.5 rounded-full" style={{ background: palette[index % palette.length] }} />{item.label}</span><strong>{item.value}</strong></div>)}</div></div>;
}

function TableShell({ children }: { children: React.ReactNode }) {
  return <div className="overflow-x-auto rounded-xl border border-border/80"><table className="w-full min-w-[760px] text-left text-xs">{children}</table></div>;
}

function AppointmentsTab({ data }: { data: AppointmentsReport }) {
  const monthly = data.charts.monthly_evolution.map((row) => ({ label: row.label, value: row.completed + row.cancelled + row.missed }));
  return <div className="space-y-5"><section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4"><MetricCard title="Total de Atendimentos" value={String(data.kpis.total)} note="Realizados, cancelados e faltas" icon={CalendarDays} /><MetricCard title="Taxa de Comparecimento" value={`${percent.format(data.kpis.attendance_rate)}%`} icon={CalendarDays} tone="success" /><MetricCard title="Taxa de Cancelamento" value={`${percent.format(data.kpis.cancellation_rate)}%`} icon={CalendarDays} tone="danger" /><MetricCard title="Taxa de Falta" value={`${percent.format(data.kpis.miss_rate)}%`} icon={AlertTriangle} tone="warning" /></section><section className="grid gap-4 xl:grid-cols-2"><ChartCard title="Distribuicao de Status"><DonutChart points={data.charts.status_distribution} /></ChartCard><ChartCard title="Atendimentos por Sala"><HorizontalBars points={data.charts.by_room} /></ChartCard><ChartCard title="Atendimentos por Convenio"><HorizontalBars points={data.charts.by_insurance} /></ChartCard><ChartCard title="Horarios Mais Ocupados"><BarChart points={data.charts.busy_hours} /></ChartCard><ChartCard title="Evolucao Mensal" className="xl:col-span-2"><BarChart points={monthly} /></ChartCard></section><ChartCard title={`Lista de Atendimentos (${data.table.count} registros)`}>{data.table.results.length === 0 ? <EmptyState message="Nenhum atendimento encontrado para o periodo selecionado." /> : <TableShell><thead className="bg-secondary/50 text-[10px] uppercase text-muted-foreground"><tr><th className="px-4 py-3">Data</th><th>Horario</th><th>Paciente</th><th>Profissional</th><th>Status</th><th>Sala</th><th>Convenio</th><th className="pr-4 text-right">Valor</th></tr></thead><tbody className="divide-y divide-border">{data.table.results.map((row) => <tr key={row.id}><td className="px-4 py-3 font-medium">{formatDate(row.date)}</td><td>{formatDateTime(row.start_time).split(", ")[1]}</td><td>{row.patient}</td><td>{row.professional}</td><td>{row.status_display}</td><td>{row.room}</td><td>{row.insurance}</td><td className="pr-4 text-right font-semibold">{money.format(row.amount)}</td></tr>)}</tbody></TableShell>}</ChartCard></div>;
}

function PatientsTab({ data, riskDays, onRiskDays }: { data: PatientsReport; riskDays: number; onRiskDays: (value: number) => void }) {
  return <div className="space-y-5"><section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4"><MetricCard title="Pacientes Ativos" value={String(data.kpis.active_patients)} icon={Users} /><MetricCard title="Novos no Periodo" value={String(data.kpis.new_patients)} icon={Users} /><MetricCard title="Risco de Evasao" value={String(data.kpis.evasion_risk)} note={`${riskDays}+ dias sem agendamento`} icon={AlertTriangle} tone="warning" /><MetricCard title="Taxa de Retencao" value={`${percent.format(data.kpis.retention_rate)}%`} icon={TrendingUp} tone="success" /></section><section className="grid gap-4 xl:grid-cols-2"><ChartCard title="Novos Pacientes por Mes"><BarChart points={data.charts.new_patients_by_month} /></ChartCard><ChartCard title="Ativos vs Inativos"><DonutChart points={data.charts.active_vs_inactive} /></ChartCard><ChartCard title="Pacientes por Profissional"><HorizontalBars points={data.charts.patients_by_professional} /></ChartCard><ChartCard title="Distribuicao por Faixa Etaria"><BarChart points={data.charts.age_distribution} /></ChartCard></section><ChartCard title={`Pacientes em Risco de Evasao (${data.risk.count} registros)`}><div className="mb-4 flex justify-end"><select className="h-9 rounded-lg border border-input bg-card px-3 text-xs" value={riskDays} onChange={(event) => onRiskDays(Number(event.target.value))}><option value={15}>15+ dias sem agendamento</option><option value={30}>30+ dias sem agendamento</option><option value={60}>60+ dias sem agendamento</option><option value={90}>90+ dias sem agendamento</option></select></div>{data.risk.results.length === 0 ? <EmptyState message="Nenhum paciente em risco de evasao com os criterios selecionados." /> : <TableShell><thead className="bg-secondary/50 text-[10px] uppercase text-muted-foreground"><tr><th className="px-4 py-3">Paciente</th><th>Profissional</th><th>Ultimo atendimento</th><th>Proximo agendamento</th><th>Dias sem consulta</th><th>Status</th><th>Contato</th></tr></thead><tbody className="divide-y divide-border">{data.risk.results.map((row) => <tr key={row.id}><td className="px-4 py-3 font-medium">{row.patient}</td><td>{row.professional}</td><td>{formatDate(row.last_appointment)}</td><td>{formatDate(row.next_appointment)}</td><td>{row.days_without_appointment}</td><td>{row.status_display}</td><td>{row.contact || "-"}</td></tr>)}</tbody></TableShell>}</ChartCard></div>;
}

function FinancialTab({ data }: { data: any }) {
  const transactions = data.transactions?.results ?? [];
  return <div className="space-y-5"><section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4"><MetricCard title="Titulos em Atraso" value={String(data.kpis?.overdue_titles ?? 0)} icon={AlertTriangle} tone="warning" /><MetricCard title="Valor Inadimplente" value={money.format(toNumber(data.kpis?.overdue_value))} icon={FileText} tone="danger" /><MetricCard title="Resultado Operacional" value={money.format(toNumber(data.kpis?.operational_result))} icon={DollarSign} tone="success" /><MetricCard title="Receita Projetada (3m)" value={money.format(toNumber(data.kpis?.projected_revenue_3m))} icon={TrendingUp} /></section><section className="grid gap-4 xl:grid-cols-2"><ChartCard title="Inadimplencia por Paciente">{(data.delinquency_by_patient ?? []).length === 0 ? <EmptyState message="Nenhum titulo em atraso no periodo." /> : <TableShell><thead className="bg-secondary/50 text-[10px] uppercase text-muted-foreground"><tr><th className="px-4 py-3">Paciente</th><th>Valor</th><th>Titulos</th><th>Dias em atraso</th></tr></thead><tbody className="divide-y divide-border">{data.delinquency_by_patient.map((row: any) => <tr key={row.patient}><td className="px-4 py-3 font-medium">{row.patient}</td><td>{money.format(toNumber(row.value))}</td><td>{row.titles}</td><td>{row.days_overdue} dias</td></tr>)}</tbody></TableShell>}</ChartCard><ChartCard title="Faturamento por Convenio"><BarChart points={data.revenue_by_insurance ?? []} moneyMode /></ChartCard><ChartCard title="DRE Simplificado" className="xl:col-span-2"><div className="divide-y divide-border rounded-xl border border-border/80">{[["Receita Bruta", data.dre?.gross_revenue], ["Cancelamentos", data.dre?.cancellations], ["Receita Liquida", data.dre?.net_revenue], ["Despesas", data.dre?.expenses], ["Resultado Operacional", data.dre?.operational_result]].map(([label, value]) => <div key={String(label)} className="flex items-center justify-between px-4 py-3 text-sm"><span className="font-semibold">{label}</span><strong>{money.format(toNumber(value))}</strong></div>)}</div></ChartCard><ChartCard title="Projecao de Receita - Proximos 3 Meses" className="xl:col-span-2"><div className="mb-5 grid gap-3 md:grid-cols-3"><MetricCard title="Mensalidades Ativas" value={`${money.format(toNumber(data.projection?.monthly_active))}/mes`} icon={DollarSign} /><MetricCard title="Pacotes Restantes" value={money.format(toNumber(data.projection?.package_remaining))} icon={FileText} /><MetricCard title="Total Projetado (3m)" value={money.format(toNumber(data.projection?.projected_total_3m))} icon={TrendingUp} /></div><BarChart points={data.projection?.series ?? []} moneyMode /></ChartCard></section><ChartCard title={`Lancamentos Financeiros (${data.transactions?.count ?? 0} registros)`}>{transactions.length === 0 ? <EmptyState message="Nenhum lancamento financeiro encontrado." /> : <TableShell><thead className="bg-secondary/50 text-[10px] uppercase text-muted-foreground"><tr><th className="px-4 py-3">Data</th><th>Tipo</th><th>Descricao</th><th>Paciente</th><th>Categoria</th><th>Convenio</th><th>Valor</th><th>Status</th><th>Vencimento</th><th>Pagamento</th></tr></thead><tbody className="divide-y divide-border">{transactions.map((row: any) => <tr key={row.id}><td className="px-4 py-3 font-medium">{formatDate(row.date)}</td><td>{row.type_display}</td><td>{row.description}</td><td>{row.patient}</td><td>{row.category_display}</td><td>{row.insurance}</td><td className="font-semibold">{money.format(toNumber(row.amount))}</td><td>{row.status_display}</td><td>{formatDate(row.due_date)}</td><td>{row.paid_at ? formatDateTime(row.paid_at) : "-"}</td></tr>)}</tbody></TableShell>}</ChartCard></div>;
}

function OnlineSchedulingTab({ data }: { data: any }) {
  return <div className="space-y-5"><p className="text-sm text-muted-foreground">Acompanhe a performance da pagina publica de agendamento</p>{!data.enabled && <div className="rounded-xl border border-warning/25 bg-warning-soft px-4 py-3 text-sm font-medium text-warning">O agendamento online esta desativado. Ative em Configuracoes.</div>}<section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4"><MetricCard title="Visualizacoes" value={String(data.kpis?.views ?? 0)} note={`${data.kpis?.unique_views ?? 0} unicas`} icon={BarChart3} /><MetricCard title="Solicitacoes" value={String(data.kpis?.requests ?? 0)} note={`${data.kpis?.pending_requests ?? 0} pendentes`} icon={CalendarDays} /><MetricCard title="Conversao" value={`${percent.format(toNumber(data.kpis?.conversion_rate))}%`} note="visitas para solicitacoes" icon={TrendingUp} /><MetricCard title="Tempo medio aprovacao" value={`${data.kpis?.average_approval_minutes ?? 0}min`} icon={CalendarDays} /></section><section className="grid gap-3 md:grid-cols-3"><MetricCard title="Aprovadas" value={String(data.statuses?.approved?.count ?? 0)} note={`${data.statuses?.approved?.percentage ?? 0}%`} icon={CalendarDays} tone="success" /><MetricCard title="Pendentes" value={String(data.statuses?.pending?.count ?? 0)} note={`${data.statuses?.pending?.percentage ?? 0}%`} icon={AlertTriangle} tone="warning" /><MetricCard title="Rejeitadas" value={String(data.statuses?.rejected?.count ?? 0)} note={`${data.statuses?.rejected?.percentage ?? 0}%`} icon={AlertTriangle} tone="danger" /></section></div>;
}

export function ReportsDashboard() {
  const [activeTab, setActiveTab] = useState<ReportTab>("appointments");
  const [period, setPeriod] = useState("this_month");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [riskDays, setRiskDays] = useState(30);

  const params = useMemo<ReportParams>(() => ({ period, start_date: period === "custom" ? startDate : undefined, end_date: period === "custom" ? endDate : undefined, risk_days: riskDays, page_size: 25 }), [period, startDate, endDate, riskDays]);
  const report = useQuery({ queryKey: ["reports", activeTab, params], queryFn: () => reportsService.byTab(activeTab, params), enabled: period !== "custom" || Boolean(startDate && endDate) });

  async function handleExport() {
    try {
      const blob = await reportsService.download(activeTab, "csv", params);
      downloadBlob(blob, `relatorio-${activeTab}.csv`);
      toast.success("Exportacao gerada com sucesso.");
    } catch {
      toast.error("Nao foi possivel exportar o relatorio.");
    }
  }

  return <div className="space-y-6"><header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><div className="flex items-center gap-2"><h1 className="text-2xl font-bold tracking-tight">Relatorios</h1><BarChart3 className="h-4 w-4 text-muted-foreground" /></div><p className="mt-1 text-sm text-muted-foreground">Analise detalhada da clinica por periodo</p></div><div className="flex flex-wrap items-center gap-2"><select className="h-11 rounded-xl border border-input bg-card px-3 text-sm font-semibold" value={period} onChange={(event) => setPeriod(event.target.value)}>{periodOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select>{period === "custom" && <><input type="date" className="h-11 rounded-xl border border-input bg-card px-3 text-sm" value={startDate} onChange={(event) => setStartDate(event.target.value)} /><input type="date" className="h-11 rounded-xl border border-input bg-card px-3 text-sm" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></>}<Button variant="outline" size="sm" leftIcon={<Download className="h-4 w-4" />} onClick={handleExport}>Exportar CSV</Button></div></header><div className="flex gap-1 overflow-x-auto border-b border-border">{tabs.map((tab) => { const Icon = tab.icon; const active = activeTab === tab.key; return <button key={tab.key} type="button" onClick={() => setActiveTab(tab.key)} className={cn("flex min-w-max items-center gap-2 border-b-2 px-4 py-3 text-sm font-semibold transition", active ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground")}><Icon className="h-4 w-4" />{tab.label}</button>; })}</div>{report.isLoading && <div className="h-[34rem] animate-pulse rounded-xl border border-border bg-card" />}{report.isError && <div className="grid min-h-[24rem] place-items-center rounded-xl border border-dashed border-border bg-card p-8 text-center"><div><AlertTriangle className="mx-auto h-8 w-8 text-warning" /><h2 className="mt-4 text-lg font-bold">Nao foi possivel carregar os relatorios</h2><p className="mt-2 text-sm text-muted-foreground">Verifique a conexao com a API e tente novamente.</p><Button className="mt-5" variant="outline" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => report.refetch()}>Tentar novamente</Button></div></div>}{!report.isLoading && !report.isError && report.data && activeTab === "appointments" && <AppointmentsTab data={report.data as AppointmentsReport} />}{!report.isLoading && !report.isError && report.data && activeTab === "patients" && <PatientsTab data={report.data as PatientsReport} riskDays={riskDays} onRiskDays={setRiskDays} />}{!report.isLoading && !report.isError && report.data && activeTab === "financial" && <FinancialTab data={report.data} />}{!report.isLoading && !report.isError && report.data && activeTab === "online-scheduling" && <OnlineSchedulingTab data={report.data} />}</div>;
}
