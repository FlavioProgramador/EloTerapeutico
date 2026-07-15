import { CalendarDays, Pause, Play, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";

import { formatCurrency, formatDate } from "../financeiro-formatters";
import type { MonthlySubscription } from "../services/financeiro-dashboard.service";

interface Props {
  subscriptions: MonthlySubscription[];
  isLoading: boolean;
  hidden: boolean;
  onCreate: () => void;
  onStatusChange: (id: number, status: MonthlySubscription["status"]) => void;
  actionPending?: boolean;
}

const statusLabel: Record<MonthlySubscription["status"], string> = {
  active: "Ativa",
  paused: "Pausada",
  ended: "Encerrada",
  cancelled: "Cancelada",
};

export function FinanceiroSubscriptionsPanel({
  subscriptions,
  isLoading,
  hidden,
  onCreate,
  onStatusChange,
  actionPending,
}: Props) {
  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-border p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-bold">Mensalidades</h2>
          <p className="text-sm text-muted-foreground">
            Assinaturas mensais com agendamento e cobrança recorrentes
          </p>
        </div>
        <Button
          size="sm"
          onClick={onCreate}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Nova mensalidade
        </Button>
      </div>

      {isLoading ? (
        <div className="p-8 text-center text-sm text-muted-foreground">
          Carregando mensalidades...
        </div>
      ) : subscriptions.length === 0 ? (
        <EmptyState
          icon={<CalendarDays className="h-6 w-6 text-muted-foreground" />}
          title="Nenhuma mensalidade com este status"
          description="Crie uma mensalidade para automatizar cobranças e organizar atendimentos recorrentes."
          action={
            <Button size="sm" onClick={onCreate}>
              Nova mensalidade
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 p-5 lg:grid-cols-2">
          {subscriptions.map((subscription) => (
            <article
              key={subscription.id}
              className="rounded-xl border border-border bg-background p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-bold">{subscription.patient_name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {subscription.frequency_display} •{" "}
                    {subscription.appointment_time.slice(0, 5)}
                  </p>
                </div>
                <Badge
                  variant={
                    subscription.status === "active"
                      ? "success"
                      : subscription.status === "paused"
                        ? "warning"
                        : "muted"
                  }
                >
                  {statusLabel[subscription.status]}
                </Badge>
              </div>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-muted-foreground">Valor mensal</dt>
                  <dd className="font-semibold">
                    {formatCurrency(subscription.monthly_amount, hidden)}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Vencimento</dt>
                  <dd className="font-semibold">Dia {subscription.due_day}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Próxima cobrança</dt>
                  <dd className="font-semibold">
                    {formatDate(subscription.next_billing_date)}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Duração</dt>
                  <dd className="font-semibold">
                    {subscription.duration_minutes} min
                  </dd>
                </div>
              </dl>
              <div className="mt-4 flex justify-end gap-2 border-t border-border pt-3">
                {subscription.status === "active" ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={actionPending}
                    onClick={() => onStatusChange(subscription.id, "paused")}
                    leftIcon={<Pause className="h-4 w-4" />}
                  >
                    Pausar
                  </Button>
                ) : subscription.status === "paused" ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={actionPending}
                    onClick={() => onStatusChange(subscription.id, "active")}
                    leftIcon={<Play className="h-4 w-4" />}
                  >
                    Reativar
                  </Button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}
