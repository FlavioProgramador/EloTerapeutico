"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Calendar as CalendarIcon,
  Check,
  Download,
  ExternalLink,
  FileText,
  Loader2,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { useAuth } from "@/contexts/auth";

import {
  cancelSubscription,
  getMySubscription,
  getPaymentSummary,
  listPayments,
  listPlans,
  refreshPayment,
  resumeSubscription,
  scheduleCancellation,
} from "./api";
import type {
  BillingInterval,
  Payment,
  PaymentSummary,
  Plan,
  PlanPrice,
  Subscription,
} from "./types";

type Mode = "plans" | "subscription" | "payments" | "pending" | "success" | "upgrade";
type Action = number | "cancel" | "schedule" | "resume" | `payment-${number}` | null;
type PaymentFilter = "ALL" | "PENDING" | "PAID" | "OVERDUE" | "REFUNDED";

const statusLabel: Record<string, string> = {
  TRIALING: "Teste gratuito",
  PENDING: "Pendente",
  ACTIVE: "Ativa",
  PAST_DUE: "Em atraso",
  SUSPENDED: "Suspensa",
  CANCELED: "Cancelada",
  EXPIRED: "Expirada",
  AUTHORIZED: "Autorizado",
  CONFIRMED: "Confirmado",
  RECEIVED: "Recebido",
  OVERDUE: "Vencido",
  REFUNDED: "Estornado",
  PARTIALLY_REFUNDED: "Estorno parcial",
  REFUND_IN_PROGRESS: "Estorno em andamento",
  CHARGEBACK: "Chargeback",
  CHARGEBACK_DISPUTE: "Chargeback em disputa",
  FAILED: "Falhou",
  RESTORED: "Restaurado",
  AWAITING_RISK_ANALYSIS: "Em análise",
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

function currency(value: string | number, currencyCode = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: currencyCode }).format(Number(value));
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  const normalized = value.length === 10 ? `${value}T00:00:00` : value;
  return new Intl.DateTimeFormat("pt-BR").format(new Date(normalized));
}

function extractError(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || "Não foi possível concluir a operação.";
  }
  return "Não foi possível concluir a operação.";
}

function paymentMatchesFilter(payment: Payment, filter: PaymentFilter) {
  if (filter === "ALL") return true;
  if (filter === "PAID") return ["CONFIRMED", "RECEIVED"].includes(payment.status);
  if (filter === "PENDING") return ["PENDING", "AUTHORIZED", "AWAITING_RISK_ANALYSIS"].includes(payment.status);
  if (filter === "OVERDUE") return payment.status === "OVERDUE";
  return ["REFUNDED", "PARTIALLY_REFUNDED", "REFUND_IN_PROGRESS"].includes(payment.status);
}

function preferredPrice(plan: Plan, interval: BillingInterval): PlanPrice | undefined {
  const prices = plan.prices.filter((price) => price.available && price.billing_interval === interval);
  if (interval === "YEARLY") {
    return prices.find((price) => price.billing_model === "INSTALLMENT")
      || prices.find((price) => price.billing_model === "ONE_TIME")
      || prices[0];
  }
  return prices.find((price) => price.billing_model === "RECURRING") || prices[0];
}

export function BillingShell({ mode }: { mode: Mode }) {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [summary, setSummary] = useState<PaymentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<Action>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPlans, setShowPlans] = useState(false);
  const [interval, setInterval] = useState<BillingInterval>("MONTHLY");
  const [paymentFilter, setPaymentFilter] = useState<PaymentFilter>("ALL");
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const shouldLoadPlans = useMemo(() => ["plans", "subscription", "upgrade"].includes(mode), [mode]);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [plansData, subscriptionData, paymentsData, summaryData] = await Promise.all([
          shouldLoadPlans ? listPlans() : Promise.resolve([]),
          mode !== "plans" ? getMySubscription().catch(() => null) : Promise.resolve(null),
          mode === "payments" ? listPayments() : Promise.resolve([]),
          mode === "payments" ? getPaymentSummary() : Promise.resolve(null),
        ]);
        if (!mounted) return;
        setPlans(plansData);
        setSubscription(subscriptionData);
        setPayments(paymentsData);
        setSummary(summaryData);
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

  const filteredPayments = useMemo(
    () => payments.filter((payment) => paymentMatchesFilter(payment, paymentFilter)),
    [paymentFilter, payments],
  );

  function handleSubscribe(planId: number) {
    const plan = plans.find((item) => item.id === planId);
    if (!plan) {
      setError("Plano não encontrado para checkout.");
      return;
    }
    const checkoutPath = `/checkout?plan=${encodeURIComponent(plan.slug)}&interval=${interval}`;
    if (!authLoading && !isAuthenticated) {
      window.location.href = `/register?next=${encodeURIComponent(checkoutPath)}`;
      return;
    }
    setActionLoading(planId);
    window.location.href = checkoutPath;
  }

  async function handleScheduleCancellation() {
    if (!window.confirm("Deseja cancelar a renovação? O acesso continuará até o fim do período já pago.")) return;
    setActionLoading("schedule");
    setError(null);
    setSuccess(null);
    try {
      const next = await scheduleCancellation();
      setSubscription(next);
      setSuccess("Cancelamento agendado. Seu acesso continuará até o fim do período atual.");
    } catch (err) {
      setError(extractError(err));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleResume() {
    setActionLoading("resume");
    setError(null);
    setSuccess(null);
    try {
      const next = await resumeSubscription();
      setSubscription(next);
      setSuccess("Renovação retomada com sucesso.");
    } catch (err) {
      setError(extractError(err));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleImmediateCancel() {
    if (!window.confirm("Cancelar imediatamente pode retirar o acesso agora. Confirme somente se esta é sua intenção.")) return;
    setActionLoading("cancel");
    setError(null);
    setSuccess(null);
    try {
      const next = await cancelSubscription();
      setSubscription(next);
      setSuccess("Assinatura cancelada.");
    } catch (err) {
      setError(extractError(err));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleRefreshPayment(paymentId: number) {
    setActionLoading(`payment-${paymentId}`);
    setError(null);
    try {
      const updated = await refreshPayment(paymentId);
      setPayments((current) => current.map((payment) => (payment.id === updated.id ? updated : payment)));
      setSummary(await getPaymentSummary());
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
      <section className="space-y-8">
        <Header title="Minhas faturas" description="Acompanhe parcelas, vencimentos, comprovantes e links de pagamento." />
        {error && <Alert>{error}</Alert>}

        {summary && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Total contratado" value={currency(summary.total_amount)} />
            <Metric label="Total pago" value={currency(summary.paid_amount)} />
            <Metric label="Parcelas pagas" value={`${summary.paid_installments} de ${summary.total_installments}`} />
            <Metric label="Próximo vencimento" value={formatDate(summary.next_due_date)} danger={summary.overdue_installments > 0} />
          </div>
        )}

        <div className="flex flex-wrap gap-2" aria-label="Filtrar faturas">
          {(["ALL", "PENDING", "PAID", "OVERDUE", "REFUNDED"] as PaymentFilter[]).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setPaymentFilter(filter)}
              className={`rounded-xl px-4 py-2 text-sm font-bold transition ${paymentFilter === filter ? "bg-primary text-primary-foreground" : "border border-border bg-card hover:bg-muted"}`}
            >
              {{ ALL: "Todas", PENDING: "Pendentes", PAID: "Pagas", OVERDUE: "Vencidas", REFUNDED: "Estornadas" }[filter]}
            </button>
          ))}
        </div>

        <div className="mx-auto max-w-5xl">
          {filteredPayments.length === 0 ? (
            <EmptyState title="Nenhuma fatura encontrada" description="Não existem faturas com o filtro selecionado." />
          ) : (
            <div className="space-y-4">
              {filteredPayments.map((payment) => (
                <article key={payment.id} className="group rounded-3xl border border-border bg-card p-5 shadow-sm transition hover:border-primary/30 hover:shadow-md">
                  <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
                    <div className="flex items-start gap-4">
                      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-muted/50 text-muted-foreground transition-colors group-hover:bg-primary/10 group-hover:text-primary">
                        <FileText className="h-6 w-6" />
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <strong className="text-lg text-foreground">{payment.installment_label}</strong>
                          <Badge status={payment.status}>{statusLabel[payment.status] || payment.status}</Badge>
                        </div>
                        <p className="mt-1 text-xl font-extrabold">{currency(payment.amount, payment.currency)}</p>
                        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1.5"><CalendarIcon className="h-3.5 w-3.5" /> Vencimento: {formatDate(payment.due_date)}</span>
                          {payment.paid_at && <span className="flex items-center gap-1.5"><Check className="h-3.5 w-3.5 text-success" /> Pago em: {formatDate(payment.paid_at)}</span>}
                          {payment.invoice_number && <span>Fatura: {payment.invoice_number}</span>}
                          <span>{payment.billing_type === "UNDEFINED" ? "Forma não informada" : payment.billing_type.replace("CREDIT_CARD", "Cartão")}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => handleRefreshPayment(payment.id)}
                        disabled={actionLoading === `payment-${payment.id}`}
                        className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2.5 text-sm font-bold hover:bg-muted disabled:opacity-60"
                        aria-label={`Atualizar ${payment.installment_label}`}
                      >
                        {actionLoading === `payment-${payment.id}` ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                        Atualizar
                      </button>
                      {payment.invoice_url && <a href={payment.invoice_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl bg-primary/10 px-4 py-2.5 text-sm font-bold text-primary hover:bg-primary/20"><ExternalLink className="h-4 w-4" /> Fatura</a>}
                      {!payment.invoice_url && payment.bank_slip_url && <a href={payment.bank_slip_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl bg-primary/10 px-4 py-2.5 text-sm font-bold text-primary hover:bg-primary/20"><Download className="h-4 w-4" /> Boleto</a>}
                      {payment.transaction_receipt_url && <a href={payment.transaction_receipt_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-sm font-bold hover:bg-muted"><Download className="h-4 w-4" /> Comprovante</a>}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    );
  }

  if (mode === "subscription") {
    const order = subscription?.billing_order;
    const isAnnualPaid = order?.billing_interval === "YEARLY" && order.status === "PAID";
    return (
      <section className="space-y-8">
        <Header title="Minha assinatura" description="Gerencie o período de acesso, renovação, plano e cobranças." />
        {error && <Alert>{error}</Alert>}
        {success && <Success>{success}</Success>}

        <div className="mx-auto max-w-5xl">
          <div className="rounded-3xl border border-border bg-card p-6 shadow-sm md:p-8">
            {subscription ? (
              <div className="space-y-7">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-3xl font-extrabold tracking-tight text-foreground">{subscription.plan.name}</h2>
                      <Badge status={subscription.status}>{statusLabel[subscription.status] || subscription.status}</Badge>
                    </div>
                    <p className="mt-2 text-sm font-medium text-muted-foreground">{subscription.plan.description}</p>
                    {order?.plan_price && <p className="mt-2 text-sm font-semibold text-primary">{order.plan_price.name} · {currency(order.total_amount, order.currency)}</p>}
                  </div>
                  <div className={`rounded-2xl px-4 py-3 text-sm font-bold ${subscription.has_access ? "bg-success-soft text-success" : "bg-danger-soft text-danger"}`}>
                    {subscription.has_access ? "Acesso liberado" : "Acesso restrito"}
                  </div>
                </div>

                {subscription.cancel_at_period_end && (
                  <div className="flex gap-3 rounded-2xl border border-warning/20 bg-warning-soft p-4 text-sm text-warning">
                    <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0" />
                    <div><strong>Cancelamento agendado</strong><p className="mt-1">O acesso permanecerá disponível até {formatDate(subscription.access_ends_at)}.</p></div>
                  </div>
                )}

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <Info label={isAnnualPaid ? "Acesso válido até" : "Fim do período"} value={formatDate(subscription.access_ends_at || subscription.current_period_end)} />
                  <Info label="Modalidade" value={order ? `${order.billing_interval === "MONTHLY" ? "Mensal" : "Anual"} · ${order.billing_model === "INSTALLMENT" ? "Parcelado" : order.billing_model === "ONE_TIME" ? "À vista" : "Recorrente"}` : "Legada"} />
                  <Info label="Parcelas" value={order ? `${order.paid_installments} de ${order.installment_count} pagas` : "—"} />
                  <Info label="Gateway" value={subscription.gateway_name} />
                </div>

                {subscription.status === "PAST_DUE" && <div className="rounded-2xl border border-danger/20 bg-danger-soft p-4 text-sm text-danger">Há uma cobrança vencida. O período de tolerância termina em {formatDate(subscription.grace_period_ends_at)}.</div>}

                <div className="flex flex-wrap gap-3 border-t border-border pt-5">
                  <Link href="/dashboard/assinatura/faturas" className="rounded-xl bg-primary/10 px-5 py-2.5 text-sm font-bold text-primary shadow-sm transition hover:bg-primary/20">Ver faturas</Link>
                  <button onClick={() => setShowPlans(!showPlans)} className="rounded-xl border border-border bg-background px-5 py-2.5 text-sm font-bold text-foreground transition hover:bg-muted">{showPlans ? "Ocultar planos" : "Alterar plano"}</button>
                  {subscription.cancel_at_period_end ? (
                    <button onClick={handleResume} disabled={actionLoading === "resume"} className="ml-auto inline-flex items-center gap-2 rounded-xl border border-primary/20 px-5 py-2.5 text-sm font-bold text-primary hover:bg-primary/10 disabled:opacity-60">
                      {actionLoading === "resume" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />} Retomar renovação
                    </button>
                  ) : (
                    <button onClick={handleScheduleCancellation} disabled={actionLoading === "schedule"} className="ml-auto rounded-xl border border-danger/20 px-5 py-2.5 text-sm font-bold text-danger hover:bg-danger-soft disabled:opacity-60">{actionLoading === "schedule" ? "Agendando..." : "Cancelar no fim do período"}</button>
                  )}
                </div>

                <details className="rounded-2xl border border-border bg-muted/20 p-4">
                  <summary className="cursor-pointer text-sm font-bold text-muted-foreground">Opções avançadas</summary>
                  <p className="mt-3 text-sm text-muted-foreground">O cancelamento imediato pode retirar o acesso antes do fim do período. Estornos seguem uma política separada.</p>
                  <button onClick={handleImmediateCancel} disabled={actionLoading === "cancel"} className="mt-3 rounded-xl border border-danger/20 px-4 py-2 text-sm font-bold text-danger hover:bg-danger-soft disabled:opacity-60">{actionLoading === "cancel" ? "Cancelando..." : "Cancelar imediatamente"}</button>
                </details>
              </div>
            ) : (
              <EmptyState title="Nenhuma assinatura operacional" description="Escolha um plano para liberar os módulos do Elo Terapêutico." actionHref="/planos" actionLabel="Ver planos" />
            )}
          </div>
        </div>

        {showPlans && subscription && (
          <div className="mt-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="mb-6 text-center"><h3 className="text-2xl font-bold text-foreground">Planos disponíveis</h3><p className="mt-2 text-sm text-muted-foreground">O plano atual será preservado até a confirmação do novo checkout.</p></div>
            <BillingIntervalToggle interval={interval} onChange={setInterval} />
            <PlanGrid plans={plans} subscription={subscription} interval={interval} onSelect={handleSubscribe} actionLoading={actionLoading} />
          </div>
        )}
      </section>
    );
  }

  if (mode === "pending" || mode === "success" || mode === "upgrade") {
    const copy = {
      pending: { title: "Pagamento em processamento", description: "A contratação foi criada. O backend aguarda a confirmação do Asaas para liberar o acesso." },
      success: { title: subscription?.status === "ACTIVE" ? "Assinatura ativa" : "Aguardando confirmação", description: subscription?.status === "ACTIVE" ? "Seu plano já está liberado." : "Acompanhe o pagamento na área de faturas." },
      upgrade: { title: "Recurso disponível em outro plano", description: "Escolha um plano superior. Sua assinatura atual será preservada até a confirmação da nova contratação." },
    }[mode];
    return (
      <section className="mx-auto flex min-h-[520px] max-w-3xl items-center justify-center px-4 py-12">
        <div className="rounded-3xl border border-border bg-card p-8 text-center shadow-sm">
          <ShieldCheck className="mx-auto h-10 w-10 text-primary" />
          <Badge status={subscription?.status || "PENDING"}>{mode === "upgrade" ? "Upgrade" : statusLabel[subscription?.status || "PENDING"]}</Badge>
          <h1 className="mt-5 text-3xl font-bold text-foreground">{copy.title}</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-muted-foreground">{copy.description}</p>
          <div className="mt-6 flex flex-wrap justify-center gap-3"><Link href="/dashboard/assinatura" className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground shadow-sm hover:opacity-90">Ver assinatura</Link><Link href="/dashboard/assinatura/faturas" className="rounded-xl border border-border px-5 py-2.5 text-sm font-bold text-foreground hover:bg-muted">Ver faturas</Link></div>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-8 px-4 py-10 md:px-8 lg:px-12">
      <div className="mx-auto max-w-4xl text-center"><Badge>Planos Elo Terapêutico</Badge><h1 className="mt-5 text-4xl font-extrabold tracking-tight text-foreground md:text-5xl">Escolha a modalidade ideal para seu consultório</h1><p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted-foreground">Compare mensal, anual à vista e anual parcelado. Dados clínicos nunca são enviados ao gateway.</p></div>
      {error && <div className="mx-auto max-w-4xl"><Alert>{error}</Alert></div>}
      <BillingIntervalToggle interval={interval} onChange={setInterval} />
      <PlanGrid plans={plans} subscription={subscription} interval={interval} onSelect={handleSubscribe} actionLoading={actionLoading} />
    </section>
  );
}

function BillingIntervalToggle({ interval, onChange }: { interval: BillingInterval; onChange: (value: BillingInterval) => void }) {
  return <div className="mx-auto mb-7 grid max-w-sm grid-cols-2 gap-1 rounded-2xl bg-muted/50 p-1.5">{(["MONTHLY", "YEARLY"] as BillingInterval[]).map((item) => <button key={item} type="button" onClick={() => onChange(item)} className={`rounded-xl px-4 py-3 text-sm font-bold transition ${interval === item ? "bg-card text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>{item === "MONTHLY" ? "Mensal" : "Anual"}</button>)}</div>;
}

function PlanGrid({ plans, subscription, interval, onSelect, actionLoading }: { plans: Plan[]; subscription: Subscription | null; interval: BillingInterval; onSelect: (planId: number) => void; actionLoading: Action }) {
  const available = plans.map((plan) => ({ plan, price: preferredPrice(plan, interval) })).filter((entry): entry is { plan: Plan; price: PlanPrice } => Boolean(entry.price));
  if (available.length === 0) return <EmptyState title="Nenhum plano disponível" description="Cadastre preços ativos no admin para esta modalidade." />;
  return <div className="grid gap-6 lg:grid-cols-3">{available.map(({ plan, price }, index) => {
    const recommended = plan.slug === "profissional";
    const current = subscription?.plan.id === plan.id && subscription.billing_order?.plan_price.id === price.id;
    return <article key={`${plan.id}-${price.id}`} className={`group relative flex flex-col rounded-3xl border bg-card p-7 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg ${recommended ? "border-primary/50" : "border-border"}`} style={{ animationDelay: `${index * 100}ms` }}>
      {recommended && <div className="absolute inset-x-0 -top-4 mx-auto w-fit rounded-full bg-primary px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-primary-foreground shadow-sm">Recomendado</div>}
      {current && <div className="absolute right-5 top-5 rounded-full bg-muted/60 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">Plano atual</div>}
      <h2 className="mt-2 text-xl font-bold text-foreground">{plan.name}</h2><p className="mt-3 min-h-[3rem] text-sm leading-relaxed text-muted-foreground">{plan.description}</p>
      <div className="mt-6"><span className="text-4xl font-extrabold tracking-tight text-foreground">{currency(price.total_amount, price.currency)}</span><span className="ml-1 text-sm font-medium text-muted-foreground">/{interval === "MONTHLY" ? "mês" : "ano"}</span>{price.billing_model === "INSTALLMENT" && <p className="mt-2 text-sm font-bold text-primary">Até {price.max_installments}x de {currency(price.installment_amount_from_max, price.currency)}</p>}{Number(price.discount_percentage) > 0 && <p className="mt-1 text-sm font-bold text-success">Economize {price.discount_percentage}%</p>}</div>
      <div className="my-7 h-px w-full bg-border" />
      <ul className="mb-8 flex-1 space-y-3.5 text-sm text-muted-foreground">{Object.entries(plan.features).filter(([, enabled]) => enabled).map(([key]) => <li key={key} className="flex items-start gap-3"><span className="mt-0.5 rounded-full bg-primary/10 p-1"><Check className="h-3 w-3 text-primary" strokeWidth={3} /></span><span className="font-medium text-foreground/80">{featureLabels[key as keyof Plan["features"]]}</span></li>)}<li className="flex items-start gap-3"><span className="mt-0.5 rounded-full bg-primary/10 p-1"><Check className="h-3 w-3 text-primary" strokeWidth={3} /></span><span className="font-medium text-foreground/80">{plan.max_patients ? `Até ${plan.max_patients} pacientes` : "Pacientes ilimitados"}</span></li></ul>
      <button disabled={current || actionLoading === plan.id} onClick={() => onSelect(plan.id)} className={`mt-auto w-full rounded-2xl px-4 py-3.5 text-sm font-bold shadow-sm transition active:scale-[0.98] disabled:cursor-not-allowed ${current ? "bg-muted/50 text-muted-foreground" : recommended ? "bg-primary text-primary-foreground hover:opacity-90" : "bg-primary/10 text-primary hover:bg-primary/20"}`}>{current ? "Sua modalidade atual" : actionLoading === plan.id ? "Abrindo checkout..." : `Assinar ${plan.name}`}</button>
    </article>;
  })}</div>;
}

function Header({ title, description }: { title: string; description: string }) {
  return <div><Badge>Assinaturas</Badge><h1 className="mt-4 text-3xl font-bold text-foreground">{title}</h1><p className="mt-2 text-sm text-muted-foreground">{description}</p></div>;
}

function Badge({ children, status }: { children: React.ReactNode; status?: string }) {
  const danger = status && ["OVERDUE", "PAST_DUE", "SUSPENDED", "FAILED", "CHARGEBACK"].includes(status);
  const success = status && ["ACTIVE", "CONFIRMED", "RECEIVED", "PAID"].includes(status);
  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold ${danger ? "border-danger/20 bg-danger-soft text-danger" : success ? "border-success/20 bg-success-soft text-success" : "border-primary/20 bg-primary/10 text-primary"}`}>{children}</span>;
}

function Alert({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm font-semibold text-danger">{children}</div>;
}

function Success({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl border border-success/20 bg-success-soft px-4 py-3 text-sm font-semibold text-success">{children}</div>;
}

function EmptyState({ title, description, actionHref, actionLabel }: { title: string; description: string; actionHref?: string; actionLabel?: string }) {
  return <div className="rounded-3xl border border-dashed border-border bg-card p-8 text-center"><h2 className="text-lg font-bold text-foreground">{title}</h2><p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">{description}</p>{actionHref && actionLabel && <Link href={actionHref} className="mt-5 inline-flex rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">{actionLabel}</Link>}</div>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="rounded-2xl border border-border bg-muted/40 px-4 py-3"><dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</dt><dd className="mt-1 font-semibold text-foreground">{value}</dd></div>;
}

function Metric({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return <div className="rounded-3xl border border-border bg-card p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p><p className={`mt-2 text-2xl font-extrabold ${danger ? "text-danger" : "text-foreground"}`}>{value}</p></div>;
}
