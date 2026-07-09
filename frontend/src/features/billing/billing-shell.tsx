"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Check, Loader2 } from "lucide-react";

import {
  cancelSubscription,
  changePlan,
  createSubscription,
  getMySubscription,
  listPayments,
  listPlans,
} from "./api";
import type { Payment, Plan, Subscription } from "./types";

type Mode = "plans" | "subscription" | "payments" | "pending" | "success" | "upgrade";

const statusLabel: Record<string, string> = {
  TRIALING: "Teste gratuito",
  PENDING: "Pagamento pendente",
  ACTIVE: "Ativa",
  PAST_DUE: "Em atraso",
  CANCELED: "Cancelada",
  EXPIRED: "Expirada",
  CONFIRMED: "Confirmado",
  RECEIVED: "Recebido",
  OVERDUE: "Vencido",
  REFUNDED: "Estornado",
  FAILED: "Falhou",
};

const featureLabels: Record<keyof Plan["features"], string> = {
  agenda: "Agenda",
  patients: "Pacientes",
  clinical_records: "Prontuário",
  financial: "Financeiro",
  documents: "Documentos",
  forms: "Formulários",
  reports: "Relatórios",
  ai: "IA",
};

function currency(value: string, currencyCode = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: currencyCode }).format(Number(value));
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR").format(new Date(value));
}

function extractError(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || "Não foi possível concluir a operação.";
  }
  return "Não foi possível concluir a operação.";
}

export function BillingShell({ mode }: { mode: Mode }) {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | "cancel" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const shouldLoadPlans = useMemo(() => ["plans", "subscription", "upgrade"].includes(mode), [mode]);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [plansData, subscriptionData, paymentsData] = await Promise.all([
          shouldLoadPlans ? listPlans() : Promise.resolve([]),
          mode !== "plans" ? getMySubscription().catch(() => null) : Promise.resolve(null),
          mode === "payments" ? listPayments() : Promise.resolve([]),
        ]);
        if (!mounted) return;
        setPlans(plansData);
        setSubscription(subscriptionData);
        setPayments(paymentsData);
      } catch (err) {
        if (mounted) setError(extractError(err));
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [mode, shouldLoadPlans]);

  async function handleSubscribe(planId: number, isChange = false) {
    setActionLoading(planId);
    setError(null);
    try {
      const next = isChange ? await changePlan(planId) : await createSubscription(planId);
      setSubscription(next);
      window.location.href = "/billing/pendente";
    } catch (err) {
      setError(extractError(err));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleCancel() {
    setActionLoading("cancel");
    setError(null);
    try {
      const next = await cancelSubscription();
      setSubscription(next);
    } catch (err) {
      setError(extractError(err));
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <section className="flex min-h-[420px] items-center justify-center rounded-3xl border border-border bg-card">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Carregando informações de assinatura...
        </div>
      </section>
    );
  }

  if (mode === "payments") {
    return (
      <section className="space-y-6">
        <Header title="Faturas" description="Acompanhe cobranças, vencimentos e links enviados pelo gateway." />
        {error && <Alert>{error}</Alert>}
        <div className="overflow-hidden rounded-3xl border border-border bg-card">
          {payments.length === 0 ? (
            <EmptyState title="Nenhuma fatura encontrada" description="As faturas aparecerão aqui quando o Asaas criar cobranças para sua assinatura." />
          ) : (
            <div className="divide-y divide-border">
              {payments.map((payment) => (
                <div key={payment.id} className="grid gap-3 p-5 md:grid-cols-5 md:items-center">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{currency(payment.amount, payment.currency)}</p>
                    <p className="text-xs text-muted-foreground">Vencimento: {formatDate(payment.due_date)}</p>
                  </div>
                  <Badge>{statusLabel[payment.status] || payment.status}</Badge>
                  <p className="text-xs text-muted-foreground">Pago em: {formatDate(payment.paid_at)}</p>
                  <div className="md:col-span-2 md:text-right">
                    {payment.invoice_url || payment.bank_slip_url ? (
                      <a className="text-sm font-semibold text-primary hover:underline" href={payment.invoice_url || payment.bank_slip_url} target="_blank" rel="noreferrer">
                        Abrir fatura
                      </a>
                    ) : (
                      <span className="text-xs text-muted-foreground">Link indisponível</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    );
  }

  if (mode === "subscription") {
    return (
      <section className="space-y-6">
        <Header title="Assinatura" description="Gerencie seu plano, status de cobrança e acesso aos módulos." />
        {error && <Alert>{error}</Alert>}
        <div className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
          <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
            {subscription ? (
              <div className="space-y-4">
                <Badge>{statusLabel[subscription.status] || subscription.status}</Badge>
                <div>
                  <h2 className="text-2xl font-bold text-foreground">{subscription.plan.name}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{subscription.plan.description}</p>
                </div>
                <dl className="space-y-3 text-sm">
                  <Info label="Próxima cobrança" value={formatDate(subscription.current_period_end)} />
                  <Info label="Fim do teste" value={formatDate(subscription.trial_ends_at)} />
                  <Info label="Gateway" value={subscription.gateway_name} />
                </dl>
                <div className="flex flex-wrap gap-3 pt-2">
                  <Link href="/dashboard/configuracoes/faturas" className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-muted">
                    Ver faturas
                  </Link>
                  <button onClick={handleCancel} disabled={actionLoading === "cancel"} className="rounded-xl border border-danger/30 px-4 py-2 text-sm font-semibold text-danger hover:bg-danger-soft disabled:opacity-60">
                    {actionLoading === "cancel" ? "Cancelando..." : "Cancelar assinatura"}
                  </button>
                </div>
              </div>
            ) : (
              <EmptyState title="Nenhuma assinatura ativa" description="Escolha um plano para liberar os módulos do Elo Terapêutico." actionHref="/planos" actionLabel="Ver planos" />
            )}
          </div>
          <PlanGrid plans={plans} subscription={subscription} onSelect={(planId) => handleSubscribe(planId, Boolean(subscription))} actionLoading={actionLoading} />
        </div>
      </section>
    );
  }

  if (mode === "pending" || mode === "success" || mode === "upgrade") {
    const copy = {
      pending: {
        title: "Pagamento em processamento",
        description: "Sua assinatura foi criada. A liberação definitiva acontece quando o webhook do Asaas confirmar o pagamento no backend.",
      },
      success: {
        title: subscription?.status === "ACTIVE" ? "Assinatura ativa" : "Ainda aguardando confirmação",
        description: subscription?.status === "ACTIVE" ? "Seu plano já está liberado para uso." : "O gateway ainda não confirmou o pagamento. Você pode acompanhar o status na área de assinatura.",
      },
      upgrade: {
        title: "Recurso disponível em outro plano",
        description: "Este módulo faz parte de um plano superior. Altere seu plano para liberar o acesso sem perder seus dados já cadastrados.",
      },
    }[mode];
    return (
      <section className="mx-auto flex min-h-[520px] max-w-3xl items-center justify-center px-4 py-12">
        <div className="rounded-3xl border border-border bg-card p-8 text-center shadow-sm">
          <Badge>{mode === "upgrade" ? "Upgrade" : statusLabel[subscription?.status || "PENDING"] || "Billing"}</Badge>
          <h1 className="mt-5 text-3xl font-bold text-foreground">{copy.title}</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-muted-foreground">{copy.description}</p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link href="/dashboard/configuracoes/assinatura" className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground shadow-sm hover:opacity-90">
              Ver assinatura
            </Link>
            <Link href="/planos" className="rounded-xl border border-border px-5 py-2.5 text-sm font-bold text-foreground hover:bg-muted">
              Ver planos
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-8 px-4 py-10 md:px-8 lg:px-12">
      <div className="mx-auto max-w-4xl text-center">
        <Badge>Planos Elo Terapêutico</Badge>
        <h1 className="mt-5 text-4xl font-extrabold tracking-tight text-foreground md:text-5xl">Escolha o plano ideal para seu consultório</h1>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted-foreground">A cobrança é da assinatura do terapeuta no SaaS. Dados clínicos não são enviados ao gateway.</p>
      </div>
      {error && <div className="mx-auto max-w-4xl"><Alert>{error}</Alert></div>}
      <PlanGrid plans={plans} subscription={subscription} onSelect={(planId) => handleSubscribe(planId, false)} actionLoading={actionLoading} />
    </section>
  );
}

function PlanGrid({ plans, subscription, onSelect, actionLoading }: { plans: Plan[]; subscription: Subscription | null; onSelect: (planId: number) => void; actionLoading: number | "cancel" | null }) {
  if (plans.length === 0) return <EmptyState title="Nenhum plano disponível" description="Cadastre planos ativos no admin para exibir esta tela." />;
  return (
    <div className="grid gap-5 lg:grid-cols-3">
      {plans.map((plan) => {
        const recommended = plan.slug === "profissional";
        const current = subscription?.plan.id === plan.id;
        return (
          <article key={plan.id} className={`relative rounded-3xl border bg-card p-6 shadow-sm ${recommended ? "border-primary/50 ring-2 ring-primary/10" : "border-border"}`}>
            {recommended && <span className="absolute right-5 top-5 rounded-full bg-primary/10 px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-primary">Recomendado</span>}
            <h2 className="text-xl font-bold text-foreground">{plan.name}</h2>
            <p className="mt-2 min-h-12 text-sm leading-6 text-muted-foreground">{plan.description}</p>
            <div className="mt-5 flex items-end gap-1">
              <span className="text-3xl font-extrabold text-foreground">{currency(plan.price, plan.currency)}</span>
              <span className="pb-1 text-xs text-muted-foreground">/{plan.billing_cycle === "MONTHLY" ? "mês" : "ano"}</span>
            </div>
            <ul className="mt-6 space-y-2 text-sm text-muted-foreground">
              {Object.entries(plan.features).filter(([, enabled]) => enabled).map(([key]) => (
                <li key={key} className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> {featureLabels[key as keyof Plan["features"]]}</li>
              ))}
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> {plan.max_patients ? `Até ${plan.max_patients} pacientes` : "Pacientes ilimitados"}</li>
            </ul>
            <button disabled={current || actionLoading === plan.id} onClick={() => onSelect(plan.id)} className="mt-6 w-full rounded-xl bg-primary px-4 py-3 text-sm font-bold text-primary-foreground shadow-sm hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60">
              {current ? "Plano atual" : actionLoading === plan.id ? "Processando..." : "Assinar plano"}
            </button>
          </article>
        );
      })}
    </div>
  );
}

function Header({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <Badge>Billing</Badge>
      <h1 className="mt-4 text-3xl font-bold text-foreground">{title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">{children}</span>;
}

function Alert({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm font-semibold text-danger">{children}</div>;
}

function EmptyState({ title, description, actionHref, actionLabel }: { title: string; description: string; actionHref?: string; actionLabel?: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-border bg-card p-8 text-center">
      <h2 className="text-lg font-bold text-foreground">{title}</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">{description}</p>
      {actionHref && actionLabel && <Link href={actionHref} className="mt-5 inline-flex rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">{actionLabel}</Link>}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-border bg-muted/40 px-4 py-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-semibold text-foreground">{value}</dd>
    </div>
  );
}
