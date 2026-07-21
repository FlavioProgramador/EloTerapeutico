"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Eye,
  FileText,
  FlaskConical,
  Loader2,
  MessageSquare,
  Plus,
  Power,
  Search,
  Send,
  Settings2,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { getPublicIntegrationError } from "@/lib/errors/public-error";
import { maskEmail, maskPhone } from "@/lib/privacy/masks";
import { cn } from "@/lib/utils";
import { ChannelConfigurationModal } from "./channel-configuration-modal";
import {
  communicationChannelLabel as channelLabel,
  communicationConnectionStatusLabel,
  communicationStatusLabel as statusLabel,
} from "./communications.utils";
import {
  useCommunicationAutomations,
  useCommunicationChannels,
  useCommunicationDashboard,
  useCommunications,
  useCommunicationTemplates,
  useTestCommunicationChannelConnection,
  useToggleCommunicationAutomation,
  useToggleCommunicationChannel,
} from "./use-communications";
import { CommunicationDrawer } from "./communication-drawer";
import {
  channelIcon,
  formatDate,
  Metric,
  statusTone,
} from "./communications-ui";
import { NewCommunicationModal } from "./new-communication-modal";
import type {
  ChannelConnectionStatus,
  CommunicationChannelConfig,
} from "./types";

type Tab = "overview" | "history" | "templates" | "automations" | "channels";

function channelStatusTone(status: ChannelConnectionStatus) {
  if (status === "configured")
    return "border-success/20 bg-success/10 text-success";
  if (status === "error" || status === "unavailable")
    return "border-danger/20 bg-danger/10 text-danger";
  if (status === "validating")
    return "border-primary/20 bg-primary/10 text-primary";
  return "border-warning/20 bg-warning/10 text-warning";
}

function readableProvider(config: CommunicationChannelConfig) {
  return (
    config.available_providers.find(
      (provider) => provider.id === config.provider,
    )?.label ||
    config.provider ||
    "Selecione um provedor"
  );
}

function maskRecipient(value?: string | null) {
  if (!value) return "Destino protegido";
  return value.includes("@") ? maskEmail(value) : maskPhone(value);
}

export function CommunicationsPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [period, setPeriod] = useState("30");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [channel, setChannel] = useState("");
  const [newOpen, setNewOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedChannel, setSelectedChannel] =
    useState<CommunicationChannelConfig | null>(null);
  const dashboard = useCommunicationDashboard(period);
  const communications = useCommunications({
    search,
    status,
    channel,
    page_size: 50,
  });
  const templates = useCommunicationTemplates();
  const automations = useCommunicationAutomations();
  const channels = useCommunicationChannels();
  const toggleAutomation = useToggleCommunicationAutomation();
  const testChannel = useTestCommunicationChannelConnection();
  const toggleChannel = useToggleCommunicationChannel();
  const maxChannel = useMemo(
    () =>
      Math.max(
        1,
        ...(dashboard.data?.by_channel.map((item) => item.total) ?? [1]),
      ),
    [dashboard.data],
  );
  const tabs: Array<[Tab, string]> = [
    ["overview", "Visão geral"],
    ["history", "Histórico"],
    ["templates", "Templates"],
    ["automations", "Automações"],
    ["channels", "Canais"],
  ];

  async function quickTest(config: CommunicationChannelConfig) {
    try {
      await testChannel.mutateAsync(config.channel);
      toast.success(`${channelLabel[config.channel]} validado com sucesso.`);
    } catch {
      toast.error(
        "Não foi possível validar o canal. Abra Configurar para revisar os campos.",
      );
    }
  }

  async function quickToggle(config: CommunicationChannelConfig) {
    try {
      await toggleChannel.mutateAsync({
        channel: config.channel,
        active: !config.is_active,
      });
      toast.success(config.is_active ? "Canal desativado." : "Canal ativado.");
    } catch {
      toast.error("Teste a configuração com sucesso antes de ativar o canal.");
    }
  }

  return (
    <main className="min-h-full bg-background p-4 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-primary">
              <MessageSquare className="h-4 w-4" aria-hidden="true" />
              Central operacional
            </div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-foreground">
              Comunicações
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Centralize mensagens, lembretes e notificações dos seus pacientes.
            </p>
          </div>
          <Button onClick={() => setNewOpen(true)}>
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
            Nova comunicação
          </Button>
        </header>

        <nav
          className="mt-7 flex gap-1 overflow-x-auto rounded-xl border border-border bg-card p-1"
          aria-label="Seções de comunicações"
        >
          {tabs.map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => setTab(value)}
              className={cn(
                "whitespace-nowrap rounded-lg px-4 py-2 text-xs font-semibold transition",
                tab === value
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground",
              )}
              aria-current={tab === value ? "page" : undefined}
            >
              {label}
            </button>
          ))}
        </nav>

        {tab === "overview" && (
          <section className="mt-6 grid gap-6">
            <div className="flex justify-end">
              <label htmlFor="communications-period" className="sr-only">
                Período dos indicadores
              </label>
              <select
                id="communications-period"
                value={period}
                onChange={(event) => setPeriod(event.target.value)}
                className="h-11 rounded-lg border border-input bg-card px-3 text-base"
              >
                <option value="7">Esta semana</option>
                <option value="30">Últimos 30 dias</option>
                <option value="90">Últimos 90 dias</option>
              </select>
            </div>
            {dashboard.isLoading && (
              <div className="flex min-h-56 items-center justify-center text-sm text-muted-foreground">
                <Loader2
                  className="mr-2 h-5 w-5 animate-spin"
                  aria-hidden="true"
                />
                Carregando indicadores...
              </div>
            )}
            {dashboard.isError && (
              <div
                className="rounded-xl border border-danger/20 bg-danger/5 p-5 text-sm text-danger"
                role="alert"
              >
                Não foi possível carregar os indicadores.
              </div>
            )}
            {dashboard.data && (
              <>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
                  <Metric
                    title="Enviadas no período"
                    value={dashboard.data.metrics.total}
                    icon={Send}
                    detail="Registros criados"
                  />
                  <Metric
                    title="Agendadas"
                    value={dashboard.data.metrics.scheduled}
                    icon={CalendarClock}
                    detail="Aguardando o horário"
                  />
                  <Metric
                    title="Entregues"
                    value={dashboard.data.metrics.delivered}
                    icon={CheckCircle2}
                    detail="Inclui lidas e respondidas"
                  />
                  <Metric
                    title="Falhas"
                    value={dashboard.data.metrics.failed}
                    icon={AlertTriangle}
                    detail="Ocorrências registradas"
                  />
                  <Metric
                    title="Taxa de sucesso"
                    value={`${dashboard.data.metrics.success_rate}%`}
                    icon={ShieldCheck}
                    detail="Enviadas ou entregues"
                  />
                </div>
                <div className="grid gap-4 lg:grid-cols-2">
                  <Card>
                    <CardContent className="p-5">
                      <h2 className="text-sm font-bold">
                        Comunicações por canal
                      </h2>
                      <div className="mt-5 grid gap-4">
                        {dashboard.data.by_channel.length === 0 && (
                          <p className="text-xs text-muted-foreground">
                            Nenhuma comunicação registrada neste período.
                          </p>
                        )}
                        {dashboard.data.by_channel.map((item) => (
                          <div key={item.channel}>
                            <div className="mb-1 flex justify-between text-xs">
                              <span>{channelLabel[item.channel]}</span>
                              <b>{item.total}</b>
                            </div>
                            <div className="h-2 rounded-full bg-secondary">
                              <div
                                className="h-2 rounded-full bg-primary"
                                style={{
                                  width: `${Math.max(6, (item.total / maxChannel) * 100)}%`,
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-5">
                      <h2 className="text-sm font-bold">Status da operação</h2>
                      <div className="mt-5 flex flex-wrap gap-2">
                        {dashboard.data.by_status.length === 0 && (
                          <p className="text-xs text-muted-foreground">
                            Nenhuma comunicação registrada neste período.
                          </p>
                        )}
                        {dashboard.data.by_status.map((item) => (
                          <span
                            key={item.status}
                            className={cn(
                              "rounded-full border px-3 py-1.5 text-xs font-bold",
                              statusTone(item.status),
                            )}
                          >
                            {statusLabel[item.status]}: {item.total}
                          </span>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            )}
          </section>
        )}

        {tab === "history" && (
          <section className="mt-6">
            <div className="grid gap-3 rounded-xl border border-border bg-card p-4 md:grid-cols-[1fr_180px_180px]">
              <label className="relative">
                <span className="sr-only">Buscar comunicações</span>
                <Search
                  className="absolute left-3 top-3.5 h-4 w-4 text-muted-foreground"
                  aria-hidden="true"
                />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar paciente, assunto ou origem..."
                  className="h-11 w-full rounded-lg border border-input bg-background pl-10 pr-3 text-base"
                />
              </label>
              <label>
                <span className="sr-only">Filtrar por canal</span>
                <select
                  value={channel}
                  onChange={(event) => setChannel(event.target.value)}
                  className="h-11 w-full rounded-lg border border-input bg-background px-3 text-base"
                >
                  <option value="">Todos os canais</option>
                  {Object.entries(channelLabel).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="sr-only">Filtrar por status</span>
                <select
                  value={status}
                  onChange={(event) => setStatus(event.target.value)}
                  className="h-11 w-full rounded-lg border border-input bg-background px-3 text-base"
                >
                  <option value="">Todos os status</option>
                  {Object.entries(statusLabel).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="mt-4 overflow-hidden rounded-xl border border-border bg-card">
              {communications.isLoading && (
                <div className="flex min-h-64 items-center justify-center text-sm text-muted-foreground">
                  <Loader2
                    className="mr-2 h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                  Carregando histórico...
                </div>
              )}
              {communications.isError && (
                <div className="p-6 text-sm text-danger" role="alert">
                  Não foi possível carregar o histórico.
                </div>
              )}
              {communications.data?.results.length === 0 && (
                <div className="grid min-h-64 place-items-center">
                  <EmptyState
                    icon={<MessageSquare className="h-6 w-6" />}
                    title="Nenhuma comunicação encontrada"
                    description="As mensagens, lembretes e notificações aparecerão aqui."
                  />
                </div>
              )}
              {!!communications.data?.results.length && (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[900px] text-left text-xs">
                    <thead className="border-b border-border bg-secondary/40 text-muted-foreground">
                      <tr>
                        <th className="px-4 py-3">Paciente</th>
                        <th className="px-4 py-3">Canal</th>
                        <th className="px-4 py-3">Assunto</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Data</th>
                        <th className="px-4 py-3">Ação</th>
                      </tr>
                    </thead>
                    <tbody>
                      {communications.data.results.map((item) => {
                        const Icon = channelIcon(item.channel);
                        return (
                          <tr
                            key={item.public_id}
                            className="border-b border-border/70 last:border-0"
                          >
                            <td className="px-4 py-4 font-semibold">
                              {item.patient_name || "Sistema"}
                              <p className="mt-1 text-xs font-normal text-muted-foreground">
                                {maskRecipient(item.recipient)}
                              </p>
                            </td>
                            <td className="px-4 py-4">
                              <span className="inline-flex items-center gap-2">
                                <Icon
                                  className="h-4 w-4 text-primary"
                                  aria-hidden="true"
                                />
                                {channelLabel[item.channel]}
                              </span>
                            </td>
                            <td className="max-w-xs truncate px-4 py-4">
                              {item.subject || "Sem assunto"}
                            </td>
                            <td className="px-4 py-4">
                              <span
                                className={cn(
                                  "rounded-full border px-2.5 py-1 text-xs font-bold",
                                  statusTone(item.status),
                                )}
                              >
                                {statusLabel[item.status]}
                              </span>
                            </td>
                            <td className="px-4 py-4 text-muted-foreground">
                              {formatDate(item.scheduled_at || item.created_at)}
                            </td>
                            <td className="px-4 py-4">
                              <button
                                type="button"
                                onClick={() => setSelectedId(item.public_id)}
                                className="inline-flex items-center gap-1 rounded-lg px-2 py-1.5 font-semibold text-primary hover:bg-primary/10"
                              >
                                <Eye className="h-3.5 w-3.5" aria-hidden="true" />
                                Detalhes
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        )}

        {tab === "templates" && (
          <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {templates.isLoading && (
              <p className="text-sm text-muted-foreground">
                Carregando templates...
              </p>
            )}
            {templates.data?.map((template) => (
              <Card key={template.id}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary">
                      <FileText className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span className="rounded-full border border-border px-2 py-1 text-xs">
                      {template.is_system_template ? "Sistema" : "Personalizado"}
                    </span>
                  </div>
                  <h2 className="mt-4 text-sm font-bold">{template.name}</h2>
                  <p className="mt-2 line-clamp-3 text-xs text-muted-foreground">
                    {template.body_template}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-1">
                    {template.allowed_variables.slice(0, 4).map((variable) => (
                      <span
                        key={variable}
                        className="rounded bg-secondary px-2 py-1 text-xs text-muted-foreground"
                      >{`{{${variable}}}`}</span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </section>
        )}

        {tab === "automations" && (
          <section className="mt-6 grid gap-3">
            {automations.isLoading && (
              <p className="text-sm text-muted-foreground">
                Carregando automações...
              </p>
            )}
            {automations.data?.map((automation) => (
              <div
                key={automation.id}
                className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <Clock3
                      className="h-4 w-4 text-primary"
                      aria-hidden="true"
                    />
                    <h2 className="text-sm font-bold">{automation.name}</h2>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {automation.event_type} · {automation.template_name} ·{" "}
                    {automation.delay_value} {automation.delay_unit}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Falhas registradas: {automation.failures}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={toggleAutomation.isPending}
                  onClick={async () => {
                    try {
                      await toggleAutomation.mutateAsync({
                        id: automation.id,
                        active: !automation.is_active,
                      });
                      toast.success(
                        automation.is_active
                          ? "Automação desativada."
                          : "Automação ativada.",
                      );
                    } catch {
                      toast.error(
                        "Revise o canal e o modelo antes de ativar.",
                      );
                    }
                  }}
                  className={cn(
                    "rounded-full border px-4 py-2 text-xs font-bold",
                    automation.is_active
                      ? "border-success/20 bg-success/10 text-success"
                      : "border-border bg-secondary text-muted-foreground",
                  )}
                >
                  {automation.is_active ? "Ativa" : "Desativada"}
                </button>
              </div>
            ))}
          </section>
        )}

        {tab === "channels" && (
          <section className="mt-6">
            {channels.isLoading && (
              <div className="flex min-h-64 items-center justify-center text-sm text-muted-foreground">
                <Loader2
                  className="mr-2 h-5 w-5 animate-spin"
                  aria-hidden="true"
                />
                Carregando canais...
              </div>
            )}
            {channels.isError && (
              <div
                className="rounded-xl border border-danger/20 bg-danger/5 p-5 text-sm text-danger"
                role="alert"
              >
                Não foi possível carregar os canais.
              </div>
            )}
            {channels.data?.length === 0 && (
              <div className="grid min-h-64 place-items-center">
                <EmptyState
                  icon={<Settings2 className="h-6 w-6" />}
                  title="Nenhum canal disponível"
                  description="Atualize a página ou verifique sua permissão de acesso."
                />
              </div>
            )}
            {!!channels.data?.length && (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {channels.data.map((item) => {
                  const Icon = channelIcon(item.channel);
                  return (
                    <Card key={item.channel} className="overflow-hidden">
                      <CardContent className="p-0">
                        <div className="p-5">
                          <div className="flex items-start justify-between gap-3">
                            <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary">
                              <Icon className="h-5 w-5" aria-hidden="true" />
                            </span>
                            <span
                              className={cn(
                                "rounded-full border px-2.5 py-1 text-xs font-bold",
                                channelStatusTone(item.connection_status),
                              )}
                            >
                              {
                                communicationConnectionStatusLabel[
                                  item.connection_status
                                ]
                              }
                            </span>
                          </div>
                          <h2 className="mt-4 text-sm font-bold">
                            {channelLabel[item.channel]}
                          </h2>
                          <p className="mt-2 text-xs text-muted-foreground">
                            Provedor:{" "}
                            <span className="font-semibold text-foreground">
                              {readableProvider(item)}
                            </span>
                          </p>
                          <div className="mt-4 grid gap-2 rounded-xl border border-border bg-secondary/30 p-3 text-xs">
                            <div className="flex justify-between gap-3">
                              <span className="text-muted-foreground">
                                Operação
                              </span>
                              <b
                                className={
                                  item.is_active
                                    ? "text-success"
                                    : "text-muted-foreground"
                                }
                              >
                                {item.is_active ? "Ativo" : "Inativo"}
                              </b>
                            </div>
                            <div className="flex justify-between gap-3">
                              <span className="text-muted-foreground">
                                Última verificação
                              </span>
                              <b>
                                {item.last_tested_at
                                  ? formatDate(item.last_tested_at)
                                  : "Não realizada"}
                              </b>
                            </div>
                            {item.last_error && (
                              <div
                                className="border-t border-border pt-2 text-danger"
                                role="alert"
                              >
                                <AlertTriangle
                                  className="mr-1 inline h-3.5 w-3.5"
                                  aria-hidden="true"
                                />
                                {getPublicIntegrationError(item.last_error)}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2 border-t border-border bg-secondary/20 p-4">
                          <Button
                            variant="outline"
                            onClick={() => setSelectedChannel(item)}
                          >
                            <Settings2
                              className="mr-2 h-4 w-4"
                              aria-hidden="true"
                            />
                            Configurar
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => quickTest(item)}
                            disabled={
                              testChannel.isPending ||
                              item.connection_status === "not_configured" ||
                              item.connection_status === "incomplete"
                            }
                          >
                            <FlaskConical
                              className="mr-2 h-4 w-4"
                              aria-hidden="true"
                            />
                            Testar
                          </Button>
                          <Button
                            className="col-span-2"
                            variant={item.is_active ? "outline" : "primary"}
                            onClick={() => quickToggle(item)}
                            disabled={
                              toggleChannel.isPending ||
                              (!item.is_active &&
                                item.connection_status !== "configured")
                            }
                          >
                            <Power
                              className="mr-2 h-4 w-4"
                              aria-hidden="true"
                            />
                            {item.is_active
                              ? "Desativar canal"
                              : "Ativar canal"}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </section>
        )}
      </div>
      {newOpen && <NewCommunicationModal onClose={() => setNewOpen(false)} />}
      {selectedId && (
        <CommunicationDrawer
          id={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
      {selectedChannel && (
        <ChannelConfigurationModal
          channel={selectedChannel}
          onClose={() => setSelectedChannel(null)}
        />
      )}
    </main>
  );
}
