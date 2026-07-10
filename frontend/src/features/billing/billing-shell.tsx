"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Check, Loader2, Download, ExternalLink, Calendar as CalendarIcon, FileText } from "lucide-react";
import { useAuth } from "@/contexts/auth";

import {
  cancelSubscription,
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
  const [showPlans, setShowPlans] = useState(false);
  const { isAuthenticated, isLoading: authLoading } = useAuth();

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

  function handleSubscribe(planId: number) {
    const plan = plans.find((item) => item.id === planId);
    if (!plan) {
      setError("Plano não encontrado para checkout.");
      return;
    }

    if (!authLoading && !isAuthenticated) {
      window.location.href = `/register?next=/checkout?plan=${encodeURIComponent(plan.slug)}`;
      return;
    }

    setActionLoading(planId);
    window.location.href = `/checkout?plan=${encodeURIComponent(plan.slug)}`;
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
      <section className="space-y-8">
        <Header title="Minhas Faturas" description="Acompanhe o histórico de cobranças, status e links para pagamento." />
        {error && <Alert>{error}</Alert>}
        
        <div className="mx-auto max-w-4xl">
          {payments.length === 0 ? (
            <EmptyState title="Nenhuma fatura encontrada" description="As faturas aparecerão aqui quando o Asaas começar a gerar cobranças para sua assinatura." />
          ) : (
            <div className="space-y-4">
              {payments.map((payment) => (
                <div key={payment.id} className="group relative flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-3xl border border-border bg-card p-5 shadow-sm transition hover:border-primary/30 hover:shadow-md">
                  <div className="flex items-start gap-4">
                    <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-muted/50 text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                      <FileText className="h-6 w-6" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <span className="text-lg font-bold text-foreground">{currency(payment.amount, payment.currency)}</span>
                        <Badge>{statusLabel[payment.status] || payment.status}</Badge>
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1.5"><CalendarIcon className="h-3.5 w-3.5" /> Vencimento: {formatDate(payment.due_date)}</span>
                        {payment.paid_at && <span className="flex items-center gap-1.5"><Check className="h-3.5 w-3.5 text-success" /> Pago em: {formatDate(payment.paid_at)}</span>}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex shrink-0 items-center gap-2">
                    {payment.invoice_url ? (
                      <a href={payment.invoice_url} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary/10 px-4 py-2.5 text-sm font-bold text-primary transition hover:bg-primary/20">
                        <ExternalLink className="h-4 w-4" /> Acessar Fatura
                      </a>
                    ) : payment.bank_slip_url ? (
                      <a href={payment.bank_slip_url} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary/10 px-4 py-2.5 text-sm font-bold text-primary transition hover:bg-primary/20">
                        <Download className="h-4 w-4" /> Boleto
                      </a>
                    ) : (
                      <span className="inline-flex items-center rounded-xl bg-muted/40 px-4 py-2.5 text-sm font-medium text-muted-foreground">
                        Link indisponível
                      </span>
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
      <section className="space-y-8">
        <Header title="Minha Assinatura" description="Gerencie seu plano atual, status de cobrança e acesse suas faturas." />
        {error && <Alert>{error}</Alert>}
        
        <div className="mx-auto max-w-4xl">
          <div className="rounded-3xl border border-border bg-card p-6 shadow-sm md:p-8">
            {subscription ? (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-3xl font-extrabold tracking-tight text-foreground">{subscription.plan.name}</h2>
                    <p className="mt-1 text-sm font-medium text-muted-foreground">{subscription.plan.description}</p>
                  </div>
                  <Badge>{statusLabel[subscription.status] || subscription.status}</Badge>
                </div>
                
                <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                  <Info label="Próxima cobrança" value={formatDate(subscription.current_period_end)} />
                  <Info label="Fim do teste" value={formatDate(subscription.trial_ends_at)} />
                  <Info label="Gateway" value={subscription.gateway_name} />
                </div>
                
                <div className="flex flex-wrap gap-3 pt-4 border-t border-border">
                  <Link href="/dashboard/assinatura/faturas" className="rounded-xl bg-primary/10 text-primary px-5 py-2.5 text-sm font-bold shadow-sm transition hover:bg-primary/20">
                    Ver faturas
                  </Link>
                  <button onClick={() => setShowPlans(!showPlans)} className="rounded-xl border border-border bg-background px-5 py-2.5 text-sm font-bold text-foreground transition hover:bg-muted">
                    {showPlans ? "Ocultar planos" : "Mudar plano"}
                  </button>
                  <button onClick={handleCancel} disabled={actionLoading === "cancel"} className="rounded-xl border border-danger/20 text-danger px-5 py-2.5 text-sm font-bold transition hover:bg-danger-soft disabled:opacity-60 ml-auto">
                    {actionLoading === "cancel" ? "Cancelando..." : "Cancelar assinatura"}
                  </button>
                </div>
              </div>
            ) : (
              <EmptyState title="Nenhuma assinatura ativa" description="Escolha um plano para liberar os módulos do Elo Terapêutico." actionHref="/planos" actionLabel="Ver planos" />
            )}
          </div>
        </div>

        {showPlans && subscription && (
          <div className="mt-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="mb-6 text-center">
              <h3 className="text-2xl font-bold text-foreground">Planos disponíveis</h3>
              <p className="mt-2 text-sm text-muted-foreground">Escolha um novo plano para fazer upgrade ou downgrade da sua assinatura.</p>
            </div>
            <PlanGrid plans={plans} subscription={subscription} onSelect={handleSubscribe} actionLoading={actionLoading} />
          </div>
        )}
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
            <Link href="/dashboard/assinatura" className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground shadow-sm hover:opacity-90">
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
      <PlanGrid plans={plans} subscription={subscription} onSelect={handleSubscribe} actionLoading={actionLoading} />
    </section>
  );
}

function PlanGrid({ plans, subscription, onSelect, actionLoading }: { plans: Plan[]; subscription: Subscription | null; onSelect: (planId: number) => void; actionLoading: number | "cancel" | null }) {
  if (plans.length === 0) return <EmptyState title="Nenhum plano disponível" description="Cadastre planos ativos no admin para exibir esta tela." />;
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {plans.map((plan, i) => {
        const recommended = plan.slug === "profissional";
        const current = subscription?.plan.id === plan.id;
        
        return (
          <article 
            key={plan.id} 
            className={`group relative flex flex-col rounded-3xl border bg-card p-7 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg ${recommended ? "border-primary/50 shadow-primary/5" : "border-border"}`}
            style={{ animationDelay: `${i * 100}ms` }}
          >
            {recommended && (
              <div className="absolute inset-x-0 -top-4 mx-auto w-fit rounded-full bg-gradient-to-r from-primary/80 to-primary px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-primary-foreground shadow-sm">
                Recomendado
              </div>
            )}
            
            {current && (
              <div className="absolute right-5 top-5 rounded-full bg-muted/60 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                Plano Atual
              </div>
            )}
            
            <h2 className="text-xl font-bold text-foreground mt-2">{plan.name}</h2>
            <p className="mt-3 min-h-[3rem] text-sm leading-relaxed text-muted-foreground">{plan.description}</p>
            
            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-foreground tracking-tight">{currency(plan.price, plan.currency)}</span>
              <span className="text-sm font-medium text-muted-foreground">/{plan.billing_cycle === "MONTHLY" ? "mês" : "ano"}</span>
            </div>
            
            <div className="mt-8 mb-6 h-px w-full bg-gradient-to-r from-transparent via-border to-transparent" />
            
            <ul className="mb-8 space-y-3.5 text-sm text-muted-foreground flex-1">
              {Object.entries(plan.features).filter(([, enabled]) => enabled).map(([key]) => (
                <li key={key} className="flex items-start gap-3">
                  <div className="mt-0.5 rounded-full bg-primary/10 p-1">
                    <Check className="h-3 w-3 text-primary" strokeWidth={3} />
                  </div>
                  <span className="font-medium text-foreground/80">{featureLabels[key as keyof Plan["features"]]}</span>
                </li>
              ))}
              <li className="flex items-start gap-3">
                <div className="mt-0.5 rounded-full bg-primary/10 p-1">
                  <Check className="h-3 w-3 text-primary" strokeWidth={3} />
                </div>
                <span className="font-medium text-foreground/80">{plan.max_patients ? `Até ${plan.max_patients} pacientes` : "Pacientes ilimitados"}</span>
              </li>
            </ul>
            
            <button 
              disabled={current || actionLoading === plan.id} 
              onClick={() => onSelect(plan.id)} 
              className={`mt-auto w-full rounded-2xl px-4 py-3.5 text-sm font-bold shadow-sm transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:pointer-events-none ${
                current 
                  ? "bg-muted/50 text-muted-foreground opacity-100 ring-1 ring-inset ring-border/50" 
                  : recommended
                    ? "bg-primary text-primary-foreground hover:opacity-90 hover:shadow-md"
                    : "bg-primary/10 text-primary hover:bg-primary/20"
              }`}
            >
              {current ? "Sua assinatura atual" : actionLoading === plan.id ? "Abrindo checkout..." : "Assinar " + plan.name}
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
