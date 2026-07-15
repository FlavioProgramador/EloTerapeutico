"use client";

import { useMemo, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  CalendarDays,
  ChevronRight,
  DollarSign,
  Eye,
  EyeOff,
  RefreshCw,
  WalletCards,
  X,
} from "lucide-react";

import { motion, Variants } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/auth";
import {
  useAppointments,
  useTodayAppointments,
} from "@/features/agenda/hooks/use-agenda";
import {
  useFinancialSummary,
  useTransactions,
} from "@/features/financeiro/hooks/use-financeiro";
import { financeiroService } from "@/features/financeiro/services/financeiro.service";
import { cn } from "@/lib/utils";

const money = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});
const numberValue = (value?: string | number | null) => Number(value ?? 0) || 0;
const monthAt = (offset: number) => {
  const today = new Date();
  return new Date(today.getFullYear(), today.getMonth() + offset, 1);
};

const metricVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.215, 0.61, 0.355, 1] },
  },
};

function Metric({
  title,
  value,
  note,
  icon: Icon,
  tone = "primary",
}: {
  title: string;
  value: string;
  note: string;
  icon: typeof DollarSign;
  tone?: "primary" | "success" | "warning" | "danger";
}) {
  const tones = {
    primary: "bg-primary/10 text-primary border border-primary/20",
    success: "bg-success/10 text-success border border-success/20",
    warning: "bg-warning/10 text-warning border border-warning/20",
    danger: "bg-danger/10 text-danger border border-danger/20",
  };

  return (
    <motion.div
      variants={metricVariants}
      whileHover={{ y: -4 }}
      className="transition-all duration-200"
    >
      <Card className="hover:shadow-md hover:border-border-strong transition-all duration-200">
        <CardContent className="flex min-h-32 justify-between p-5">
          <div>
            <p className="text-xs font-semibold text-muted-foreground">
              {title}
            </p>
            <p className="mt-4 text-2xl font-bold text-foreground">{value}</p>
            <p className="mt-1 text-[11px] text-muted-foreground">{note}</p>
          </div>
          <span
            className={cn(
              "grid h-9 w-9 place-items-center rounded-lg",
              tones[tone],
            )}
          >
            <Icon className="h-4 w-4" />
          </span>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function Bars({
  values,
  labels,
  barClassName = "bg-primary/75",
}: {
  values: number[];
  labels: string[];
  barClassName?: string;
}) {
  const max = Math.max(1, ...values);
  return (
    <div className="mt-5 flex h-52 items-end gap-3 border-b border-l border-border px-3 pb-7">
      {values.map((value, index) => {
        const heightPercent = Math.max(2, (value / max) * 100);
        return (
          <div
            key={`${labels[index]}-${index}`}
            className="relative flex h-full flex-1 items-end justify-center"
          >
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: `${heightPercent}%` }}
              transition={{
                duration: 0.6,
                ease: "easeOut",
                delay: index * 0.05,
              }}
              className={cn(
                "w-7 rounded-t hover:brightness-110 cursor-pointer transition-all",
                barClassName,
              )}
              title={String(value)}
            />
            <span className="absolute -bottom-6 text-[10px] text-muted-foreground">
              {labels[index]}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function DashboardHome() {
  const router = useRouter();
  const { user } = useAuth();
  const [showValues, setShowValues] = useState(false);
  const [dismissed, setDismissed] = useState(
    () =>
      typeof window !== "undefined" &&
      localStorage.getItem("dashboard-setup-dismissed") === "true",
  );
  const now = useMemo(() => new Date(), []);
  const start = useMemo(
    () => new Date(now.getFullYear(), now.getMonth(), 1).toISOString(),
    [now],
  );
  const end = useMemo(
    () =>
      new Date(
        now.getFullYear(),
        now.getMonth() + 1,
        0,
        23,
        59,
        59,
      ).toISOString(),
    [now],
  );
  const references = useMemo(() => [-5, -4, -3, -2, -1, 0].map(monthAt), []);

  const today = useTodayAppointments();
  const appointments = useAppointments({
    start_time_gte: start,
    start_time_lte: end,
    page_size: 100,
  });
  const pending = useTransactions({ payment_status: "pending" });
  const summary = useFinancialSummary(now.getFullYear(), now.getMonth() + 1);
  const history = useQueries({
    queries: references.map((date) => ({
      queryKey: [
        "dashboard",
        "summary",
        date.getFullYear(),
        date.getMonth() + 1,
      ],
      queryFn: () =>
        financeiroService.getSummary(date.getFullYear(), date.getMonth() + 1),
      staleTime: 60_000,
    })),
  });

  const hideSetup = () => {
    localStorage.setItem("dashboard-setup-dismissed", "true");
    setDismissed(true);
  };
  const displayMoney = (value: number) =>
    showValues ? money.format(value) : "R$ ••••";
  const completed = (appointments.data ?? []).filter(
    (item) => item.status === "completed",
  );
  const overdue = (pending.data ?? []).filter(
    (item) =>
      item.due_date && new Date(`${item.due_date}T00:00:00`) < new Date(),
  );
  const overdueTotal = overdue.reduce(
    (total, item) => total + numberValue(item.amount),
    0,
  );
  const weekdayCounts = useMemo(() => {
    const counts = [0, 0, 0, 0, 0, 0, 0];
    completed.forEach((item) => {
      counts[new Date(item.start_time).getDay()] += 1;
    });
    return [
      counts[1],
      counts[2],
      counts[3],
      counts[4],
      counts[5],
      counts[6],
      counts[0],
    ];
  }, [completed]);
  const incomeHistory = history.map((item) =>
    numberValue(item.data?.total_income),
  );
  const monthLabels = references.map((date) =>
    date.toLocaleDateString("pt-BR", { month: "short" }).replace(".", ""),
  );
  const setup = [
    {
      title: "Personalize sua clínica",
      note: "Nome, telefone e registro profissional",
      done: Boolean(
        user?.full_name &&
        user?.phone &&
        (user.role !== "therapist" || user.crp),
      ),
    },
    {
      title: "Adicione dados bancários",
      note: "PIX e/ou conta para cobranças",
      done: (pending.data ?? []).some((item) => Boolean(item.payment_method)),
      action: "/dashboard/financeiro",
    },
    {
      title: "Conecte o WhatsApp",
      note: "Lembretes automáticos e cobrança",
      done: false,
    },
    {
      title: "Crie templates de documentos",
      note: "Recibos, declarações e relatórios",
      done: false,
      action: "/dashboard/documentos",
    },
  ];
  const setupDone = setup.filter((item) => item.done).length;
  const loading =
    today.isLoading ||
    appointments.isLoading ||
    pending.isLoading ||
    summary.isLoading ||
    history.some((item) => item.isLoading);
  const failed =
    today.isError ||
    appointments.isError ||
    pending.isError ||
    summary.isError ||
    history.some((item) => item.isError);

  if (loading)
    return (
      <div className="h-[42rem] animate-pulse rounded-xl border border-border bg-card" />
    );
  if (failed)
    return (
      <div className="grid min-h-[28rem] place-items-center rounded-xl border border-dashed border-border bg-card p-8 text-center">
        <div>
          <AlertTriangle className="mx-auto h-8 w-8 text-warning" />
          <h1 className="mt-4 text-lg font-bold">
            Não foi possível carregar o Dashboard
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Verifique a conexão com a API e tente novamente.
          </p>
          <Button
            className="mt-5"
            onClick={() => window.location.reload()}
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            Recarregar
          </Button>
        </div>
      </div>
    );

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
  };

  const sectionVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: "easeOut" },
    },
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="space-y-5"
    >
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Visão geral da sua clínica
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowValues((value) => !value)}
          leftIcon={
            showValues ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )
          }
        >
          {showValues ? "Ocultar valores" : "Mostrar valores"}
        </Button>
      </header>

      {!dismissed && (
        <motion.div variants={sectionVariants}>
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader className="flex flex-row items-start justify-between pb-3">
              <div>
                <CardTitle className="text-base">
                  Configure sua clínica
                </CardTitle>
                <p className="mt-1 text-xs text-muted-foreground">
                  {setupDone} de {setup.length} passos concluídos
                </p>
              </div>
              <button
                type="button"
                onClick={hideSetup}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" /> Dispensar
              </button>
            </CardHeader>
            <CardContent>
              <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${(setupDone / setup.length) * 100}%` }}
                />
              </div>
              <div className="divide-y divide-border">
                {setup.map((item) => (
                  <button
                    type="button"
                    key={item.title}
                    disabled={!item.action}
                    onClick={() => item.action && router.push(item.action)}
                    className="flex w-full items-center gap-3 py-3 text-left disabled:cursor-default"
                  >
                    <span
                      className={cn(
                        "h-4 w-4 rounded-full border",
                        item.done
                          ? "border-success bg-success"
                          : "border-border-strong",
                      )}
                    />
                    <span className="flex-1">
                      <strong className="block text-xs">{item.title}</strong>
                      <span className="block text-[11px] text-muted-foreground">
                        {item.note}
                      </span>
                    </span>
                    {item.action && (
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    )}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Grid de Métricas com Staggered Fade-in */}
      <motion.section
        variants={containerVariants}
        className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
      >
        <Metric
          title="Faturamento mensal"
          value={displayMoney(numberValue(summary.data?.total_income))}
          note="Receitas pagas neste mês"
          icon={DollarSign}
        />
        <Metric
          title="Consultas realizadas"
          value={String(completed.length)}
          note="Concluídas neste mês"
          icon={CalendarDays}
          tone="success"
        />
        <Metric
          title="A receber"
          value={displayMoney(numberValue(summary.data?.total_pending))}
          note="Pendente neste mês"
          icon={WalletCards}
          tone="warning"
        />
        <Metric
          title="Inadimplência"
          value={displayMoney(overdueTotal)}
          note={`${overdue.length} cobrança(s) vencida(s)`}
          icon={AlertTriangle}
          tone="danger"
        />
      </motion.section>

      {/* Gráficos */}
      <motion.section
        variants={sectionVariants}
        className="grid gap-4 xl:grid-cols-2"
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Fluxo de caixa</CardTitle>
            <p className="text-xs text-muted-foreground">
              Receitas pagas nos últimos 6 meses
            </p>
          </CardHeader>
          <CardContent>
            <Bars values={incomeHistory} labels={monthLabels} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Consultas por dia</CardTitle>
            <p className="text-xs text-muted-foreground">
              Atendimentos concluídos neste mês
            </p>
          </CardHeader>
          <CardContent>
            <Bars
              values={weekdayCounts}
              labels={["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]}
              barClassName="bg-success/75"
            />
          </CardContent>
        </Card>
      </motion.section>

      {/* Consultas Hoje e Alertas */}
      <motion.section
        variants={sectionVariants}
        className="grid gap-4 xl:grid-cols-2"
      >
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">Consultas de hoje</CardTitle>
              <p className="mt-1 text-xs text-muted-foreground">
                Agenda do dia
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => router.push("/dashboard/agenda")}
            >
              Ver agenda
            </Button>
          </CardHeader>
          <CardContent>
            {(today.data ?? []).length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                Nenhuma consulta hoje.
              </p>
            ) : (
              <div className="divide-y divide-border">
                {(today.data ?? []).slice(0, 6).map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() =>
                      router.push(`/dashboard/agenda?appointment=${item.id}`)
                    }
                    className="flex w-full items-center gap-3 py-3 text-left hover:bg-secondary/40 transition-colors"
                  >
                    <strong className="w-12 text-xs">
                      {new Date(item.start_time).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </strong>
                    <span className="flex-1 text-xs font-semibold">
                      {item.patient_name || "Paciente"}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {item.status_display || item.status}
                    </span>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-base">
              Alertas{" "}
              <span className="rounded-full border px-2 py-0.5 text-xs text-muted-foreground">
                {overdue.length}
              </span>
            </CardTitle>
            <p className="text-xs text-muted-foreground">Cobranças vencidas</p>
          </CardHeader>
          <CardContent>
            {overdue.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                Nenhum alerta pendente.
              </p>
            ) : (
              <div className="divide-y divide-border">
                {overdue.slice(0, 6).map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() =>
                      router.push(
                        `/dashboard/financeiro?transaction=${item.id}`,
                      )
                    }
                    className="flex w-full items-center gap-3 py-3 text-left hover:bg-secondary/40 transition-colors"
                  >
                    <AlertTriangle className="h-4 w-4 text-warning" />
                    <span className="flex-1">
                      <strong className="block text-xs">
                        {item.patient_name || item.description}
                      </strong>
                      <span className="block text-[10px] text-muted-foreground">
                        Venceu em{" "}
                        {new Date(
                          `${item.due_date}T00:00:00`,
                        ).toLocaleDateString("pt-BR")}
                      </span>
                    </span>
                    <strong className="text-xs">
                      {displayMoney(numberValue(item.amount))}
                    </strong>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.section>
    </motion.div>
  );
}
