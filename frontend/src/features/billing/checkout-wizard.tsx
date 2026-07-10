"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ArrowLeft, Check, Loader2, ShieldCheck } from "lucide-react";

import { useAuth } from "@/contexts/auth";

import { createCheckout, listPlans, previewCheckout } from "./api";
import type { BillingType, CheckoutPayload, CheckoutPreview, CheckoutType, Plan } from "./types";

const billingTypeLabels: Record<BillingType, string> = {
  PIX: "PIX",
  BOLETO: "Boleto",
  CREDIT_CARD: "Cartão de crédito",
};

const checkoutTypeLabels: Record<CheckoutType, string> = {
  SUBSCRIPTION: "Assinatura",
  ONE_TIME: "Cobrança única",
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

function defaultDueDate() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
}

function currency(value: string, currencyCode = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: currencyCode }).format(Number(value));
}

function extractError(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string; non_field_errors?: string[] } } }).response;
    return response?.data?.detail || response?.data?.non_field_errors?.[0] || "Não foi possível concluir o checkout.";
  }
  return "Não foi possível concluir o checkout.";
}

export function CheckoutWizard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const selectedPlanSlug = searchParams.get("plan") || "profissional";
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [result, setResult] = useState<CheckoutPreview | null>(null);
  const [checkoutType, setCheckoutType] = useState<CheckoutType>("SUBSCRIPTION");
  const [billingType, setBillingType] = useState<BillingType>("PIX");
  const [dueDate, setDueDate] = useState(defaultDueDate);
  const [installmentCount, setInstallmentCount] = useState(1);
  const [description, setDescription] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadPlans() {
      setLoading(true);
      setError(null);
      try {
        const data = await listPlans();
        if (mounted) setPlans(data);
      } catch {
        if (mounted) setError("Não foi possível carregar os planos agora. Tente novamente em instantes.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadPlans();
    return () => {
      mounted = false;
    };
  }, []);

  const selectedPlan = useMemo(() => {
    return plans.find((plan) => plan.slug === selectedPlanSlug) || plans.find((plan) => plan.slug === "profissional") || plans[0];
  }, [plans, selectedPlanSlug]);

  useEffect(() => {
    if (selectedPlan && !description) {
      setDescription(`Assinatura Elo Terapêutico - ${selectedPlan.name}`);
    }
  }, [description, selectedPlan]);

  const payload = useMemo<CheckoutPayload | null>(() => {
    if (!selectedPlan) return null;
    return {
      plan_slug: selectedPlan.slug,
      type: checkoutType,
      billingType,
      cpfCnpj: "",
      dueDate,
      value: selectedPlan.price,
      description,
      cycle: selectedPlan.billing_cycle,
      installmentCount: checkoutType === "ONE_TIME" ? installmentCount : 1,
    };
  }, [billingType, checkoutType, description, dueDate, installmentCount, selectedPlan]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/register?next=/checkout?plan=${selectedPlanSlug}`);
    }
  }, [authLoading, isAuthenticated, router, selectedPlanSlug]);

  if (authLoading || (!isAuthenticated && !authLoading)) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
          <Loader2 className="h-4 w-4 animate-spin" /> Verificando acesso...
        </div>
      </main>
    );
  }

  async function handlePreview() {
    if (!payload) return;
    setSubmitting(true);
    setError(null);
    try {
      const data = await previewCheckout(payload);
      setPreview(data);
      setStep(2);
    } catch (err) {
      setError(extractError(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreate() {
    if (!payload) return;
    setSubmitting(true);
    setError(null);
    try {
      const data = await createCheckout(payload);
      setResult(data);
      setStep(3);
    } catch (err) {
      setError(extractError(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
          <Loader2 className="h-4 w-4 animate-spin" /> Carregando checkout Asaas...
        </div>
      </main>
    );
  }

  if (!selectedPlan) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
        <div className="max-w-md rounded-3xl border border-border bg-card p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto h-8 w-8 text-danger" />
          <h1 className="mt-4 text-xl font-bold">Plano indisponível</h1>
          <p className="mt-2 text-sm text-muted-foreground">Não encontramos planos ativos para iniciar o checkout.</p>
          <Link href="/planos" className="mt-5 inline-flex rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">
            Ver planos
          </Link>
        </div>
      </main>
    );
  }

  const activePreview = preview || result;

  return (
    <main className="min-h-screen bg-background px-4 py-8 text-foreground md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <Link href="/planos" className="inline-flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Voltar para planos
        </Link>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-border bg-card p-6 shadow-sm md:p-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">Checkout Asaas</span>
                <h1 className="mt-4 text-3xl font-bold tracking-tight md:text-4xl">Finalize sua assinatura</h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  Configure a cobrança no sandbox do Asaas. O plano só será liberado depois que o backend receber o webhook de confirmação.
                </p>
              </div>
              <StepIndicator step={step} />
            </div>

            {error && (
              <div className="mt-6 rounded-2xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm font-semibold text-danger">
                {error}
              </div>
            )}

            {step === 1 && (
              <div className="mt-8 space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <ReadonlyField label="Valor" value={currency(selectedPlan.price, selectedPlan.currency)} />
                  <ReadonlyField label="Plano" value={selectedPlan.name} />
                </div>

                <label className="block space-y-2">
                  <span className="text-sm font-semibold">Descrição</span>
                  <input
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                    placeholder="Descrição da cobrança"
                  />
                </label>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-3">
                    <span className="text-sm font-semibold">Tipo</span>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {(["SUBSCRIPTION", "ONE_TIME"] as CheckoutType[]).map((item) => (
                        <button
                          key={item}
                          type="button"
                          onClick={() => setCheckoutType(item)}
                          className={`rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition ${checkoutType === item ? "border-primary bg-primary/10 text-primary" : "border-border bg-background text-foreground hover:bg-muted"}`}
                        >
                          {checkoutTypeLabels[item]}
                        </button>
                      ))}
                    </div>
                  </div>

                  <label className="block space-y-2">
                    <span className="text-sm font-semibold">Vencimento</span>
                    <input
                      type="date"
                      value={dueDate}
                      onChange={(event) => setDueDate(event.target.value)}
                      className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                    />
                  </label>
                </div>

                {checkoutType === "ONE_TIME" && (
                  <label className="block space-y-2">
                    <span className="text-sm font-semibold">Parcelamento</span>
                    <select
                      value={installmentCount}
                      onChange={(event) => setInstallmentCount(Number(event.target.value))}
                      className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                    >
                      {Array.from({ length: 12 }, (_, index) => index + 1).map((count) => (
                        <option key={count} value={count}>
                          {count === 1 ? "À vista" : `${count} parcelas`}
                        </option>
                      ))}
                    </select>
                  </label>
                )}

                <div className="space-y-3">
                  <span className="text-sm font-semibold">Forma de pagamento</span>
                  <div className="grid gap-3 md:grid-cols-3">
                    {(["PIX", "BOLETO", "CREDIT_CARD"] as BillingType[]).map((item) => {
                      const disabled = item === "CREDIT_CARD";
                      return (
                        <button
                          key={item}
                          type="button"
                          disabled={disabled}
                          onClick={() => setBillingType(item)}
                          className={`rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55 ${billingType === item ? "border-primary bg-primary/10 text-primary" : "border-border bg-background text-foreground hover:bg-muted"}`}
                        >
                          {billingTypeLabels[item]}
                          {disabled && <small className="mt-1 block text-xs font-medium text-muted-foreground">Via checkout/tokenização futura</small>}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <Notice />

                <button
                  type="button"
                  onClick={handlePreview}
                  disabled={submitting}
                  className="inline-flex w-full items-center justify-center rounded-2xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground shadow-sm transition hover:opacity-90 disabled:opacity-60 md:w-auto"
                >
                  {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Revisar checkout
                </button>
              </div>
            )}

            {step === 2 && activePreview && (
              <div className="mt-8 space-y-6">
                <ReviewRow label="Gateway" value={`${activePreview.gateway} ${activePreview.environment === "SANDBOX" ? "Sandbox" : "Produção"}`} />
                <ReviewRow label="Plano" value={activePreview.plan.name} />
                <ReviewRow label="Tipo" value={checkoutTypeLabels[activePreview.checkout.type]} />
                <ReviewRow label="Valor" value={currency(activePreview.checkout.value, activePreview.plan.currency)} />
                <ReviewRow label="Vencimento" value={new Intl.DateTimeFormat("pt-BR").format(new Date(`${activePreview.checkout.dueDate}T00:00:00`))} />
                <ReviewRow label="Forma de pagamento" value={billingTypeLabels[activePreview.checkout.billingType]} />
                <ReviewRow label="Descrição" value={activePreview.checkout.description} />

                <Notice />
                <div className="rounded-2xl border border-warning/20 bg-warning-soft px-4 py-3 text-sm font-semibold text-warning">
                  Nada no frontend ativa o plano. A assinatura será criada como PENDING e só vira ACTIVE após webhook do Asaas.
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <button type="button" onClick={() => setStep(1)} className="rounded-2xl border border-border px-5 py-3 text-sm font-bold hover:bg-muted">
                    Editar dados
                  </button>
                  <button
                    type="button"
                    onClick={handleCreate}
                    disabled={submitting}
                    className="inline-flex items-center justify-center rounded-2xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-60"
                  >
                    {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Criar no Asaas Sandbox
                  </button>
                </div>
              </div>
            )}

            {step === 3 && result && (
              <div className="mt-8 rounded-3xl border border-primary/20 bg-primary/5 p-6">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-primary/10 p-2 text-primary">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">Checkout criado com segurança</h2>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      {result.subscription
                        ? "A assinatura foi salva como PENDING. Aguarde a confirmação do pagamento pelo webhook do Asaas para liberar os módulos do plano."
                        : "A cobrança única foi criada no Asaas. Acompanhe o link de cobrança retornado pelo gateway."}
                    </p>
                    <div className="mt-5 flex flex-wrap gap-3">
                      <Link href="/billing/pendente" className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">
                        Acompanhar assinatura
                      </Link>
                      {result.payment?.invoiceUrl && (
                        <a href={result.payment.invoiceUrl} target="_blank" rel="noreferrer" className="rounded-xl border border-border px-5 py-2.5 text-sm font-bold hover:bg-muted">
                          Abrir cobrança
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <aside className="space-y-4">
            <PlanSummary plan={selectedPlan} />
            <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
              <h2 className="text-lg font-bold">Fluxo seguro</h2>
              <ol className="mt-4 space-y-3 text-sm text-muted-foreground">
                <li>1. Você confirma os dados do checkout.</li>
                <li>2. O backend cria customer e subscription no Asaas.</li>
                <li>3. A assinatura local nasce como PENDING.</li>
                <li>4. O webhook do Asaas confirma o pagamento.</li>
                <li>5. O backend libera os módulos do plano.</li>
              </ol>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

function StepIndicator({ step }: { step: 1 | 2 | 3 }) {
  return (
    <div className="flex items-center gap-2">
      {[1, 2, 3].map((item) => (
        <span key={item} className={`grid h-8 w-8 place-items-center rounded-full text-xs font-bold ${step >= item ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
          {step > item ? <Check className="h-4 w-4" /> : item}
        </span>
      ))}
    </div>
  );
}

function ReadonlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-muted/40 px-4 py-3">
      <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</span>
      <p className="mt-1 text-sm font-bold text-foreground">{value}</p>
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-border bg-muted/30 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <strong className="text-sm text-foreground">{value}</strong>
    </div>
  );
}

function Notice() {
  return (
    <div className="rounded-2xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm font-semibold text-primary">
      Os pagamentos serão processados pelo Asaas.
    </div>
  );
}

function PlanSummary({ plan }: { plan: Plan }) {
  return (
    <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">Plano selecionado</span>
      <h2 className="mt-4 text-2xl font-bold">{plan.name}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{plan.description}</p>
      <div className="mt-5 flex items-end gap-1">
        <strong className="text-3xl font-extrabold">{currency(plan.price, plan.currency)}</strong>
        <span className="pb-1 text-xs text-muted-foreground">/{plan.billing_cycle === "MONTHLY" ? "mês" : "ano"}</span>
      </div>
      <ul className="mt-5 space-y-2 text-sm text-muted-foreground">
        {Object.entries(plan.features)
          .filter(([, enabled]) => enabled)
          .slice(0, 6)
          .map(([key]) => (
            <li key={key} className="flex items-center gap-2">
              <Check className="h-4 w-4 text-primary" /> {featureLabels[key as keyof Plan["features"]]}
            </li>
          ))}
        <li className="flex items-center gap-2">
          <Check className="h-4 w-4 text-primary" /> {plan.max_patients ? `Até ${plan.max_patients} pacientes` : "Pacientes ilimitados"}
        </li>
      </ul>
    </div>
  );
}
