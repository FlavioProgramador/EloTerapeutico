"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  CreditCard,
  FileText,
  Loader2,
  QrCode,
  ShieldCheck,
} from "lucide-react";

import { useAuth } from "@/contexts/auth";

import { createCheckout, listPlans, previewCheckout } from "./api";
import type {
  BillingInterval,
  BillingModel,
  BillingType,
  CheckoutPayload,
  CheckoutPreview,
  Plan,
  PlanPrice,
} from "./types";

const billingTypeLabels: Record<BillingType, string> = {
  PIX: "PIX",
  BOLETO: "Boleto",
  CREDIT_CARD: "Cartão de crédito",
};

const billingModelLabels: Record<BillingModel, string> = {
  RECURRING: "Cobrança recorrente",
  ONE_TIME: "Pagamento anual à vista",
  INSTALLMENT: "Pagamento anual parcelado",
};

const featureLabels: Record<string, string> = {
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR").format(new Date(`${value}T00:00:00`));
}

function extractError(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as {
      response?: { data?: { detail?: string; non_field_errors?: string[]; error?: { details?: Record<string, string[]> } } };
    }).response;
    if (response?.data?.detail) return response.data.detail;
    if (response?.data?.non_field_errors?.[0]) return response.data.non_field_errors[0];
    const details = response?.data?.error?.details;
    if (details) return Object.values(details).flat()[0] || "Não foi possível concluir o checkout.";
  }
  return "Não foi possível concluir o checkout.";
}

function chooseDefaultPrice(plan: Plan, interval: BillingInterval): PlanPrice | undefined {
  const prices = plan.prices.filter((price) => price.available && price.billing_interval === interval);
  if (interval === "YEARLY") {
    return prices.find((price) => price.billing_model === "INSTALLMENT") || prices.find((price) => price.billing_model === "ONE_TIME") || prices[0];
  }
  return prices.find((price) => price.billing_model === "RECURRING") || prices[0];
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
  const [interval, setInterval] = useState<BillingInterval>("MONTHLY");
  const [selectedPriceId, setSelectedPriceId] = useState<number | null>(null);
  const [billingType, setBillingType] = useState<BillingType>("PIX");
  const [dueDate, setDueDate] = useState(defaultDueDate);
  const [installmentCount, setInstallmentCount] = useState(1);
  const [cpfCnpj, setCpfCnpj] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");

  useEffect(() => {
    setIdempotencyKey(crypto.randomUUID());
  }, []);

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

  const selectedPlan = useMemo(
    () => plans.find((plan) => plan.slug === selectedPlanSlug) || plans[0],
    [plans, selectedPlanSlug],
  );

  const intervalPrices = useMemo(
    () => selectedPlan?.prices.filter((price) => price.available && price.billing_interval === interval) || [],
    [interval, selectedPlan],
  );

  const selectedPrice = useMemo(
    () => intervalPrices.find((price) => price.id === selectedPriceId) || intervalPrices[0],
    [intervalPrices, selectedPriceId],
  );

  useEffect(() => {
    if (!selectedPlan) return;
    const price = chooseDefaultPrice(selectedPlan, interval);
    setSelectedPriceId(price?.id ?? null);
  }, [interval, selectedPlan]);

  useEffect(() => {
    if (!selectedPrice) return;
    setInstallmentCount(selectedPrice.billing_model === "INSTALLMENT" ? selectedPrice.max_installments : 1);
  }, [selectedPrice]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/register?next=/checkout?plan=${selectedPlanSlug}`);
    }
  }, [authLoading, isAuthenticated, router, selectedPlanSlug]);

  const payload = useMemo<CheckoutPayload | null>(() => {
    if (!selectedPrice) return null;
    return {
      plan_price_id: selectedPrice.id,
      billingType,
      cpfCnpj,
      name,
      phone,
      dueDate,
      installmentCount: selectedPrice.billing_model === "INSTALLMENT" ? installmentCount : 1,
      description: `Elo Terapêutico — ${selectedPrice.name}`,
      idempotency_key: idempotencyKey,
    };
  }, [billingType, cpfCnpj, dueDate, idempotencyKey, installmentCount, name, phone, selectedPrice]);

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

  if (authLoading || (!isAuthenticated && !authLoading) || loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
          <Loader2 className="h-4 w-4 animate-spin" /> Preparando checkout seguro...
        </div>
      </main>
    );
  }

  if (!selectedPlan || !selectedPrice) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
        <div className="max-w-md rounded-3xl border border-border bg-card p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto h-8 w-8 text-danger" />
          <h1 className="mt-4 text-xl font-bold">Opção de contratação indisponível</h1>
          <p className="mt-2 text-sm text-muted-foreground">Cadastre um preço ativo para este plano no painel administrativo.</p>
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

        <section className="grid gap-6 lg:grid-cols-[1.12fr_0.88fr]">
          <div className="rounded-3xl border border-border bg-card p-6 shadow-sm md:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
                  Checkout seguro Asaas
                </span>
                <h1 className="mt-4 text-3xl font-bold tracking-tight md:text-4xl">Finalize sua assinatura</h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  O plano será liberado somente após a confirmação do pagamento pelo backend.
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
              <div className="mt-8 space-y-7">
                <div>
                  <span className="text-sm font-semibold">Período do plano</span>
                  <div className="mt-3 grid grid-cols-2 gap-2 rounded-2xl bg-muted/50 p-1.5">
                    {(["MONTHLY", "YEARLY"] as BillingInterval[]).map((item) => {
                      const enabled = selectedPlan.prices.some((price) => price.available && price.billing_interval === item);
                      return (
                        <button
                          key={item}
                          type="button"
                          disabled={!enabled}
                          onClick={() => setInterval(item)}
                          className={`rounded-xl px-4 py-3 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-40 ${
                            interval === item ? "bg-card text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"
                          }`}
                        >
                          {item === "MONTHLY" ? "Mensal" : "Anual"}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {intervalPrices.length > 1 && (
                  <div>
                    <span className="text-sm font-semibold">Modalidade</span>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      {intervalPrices.map((price) => (
                        <button
                          key={price.id}
                          type="button"
                          onClick={() => setSelectedPriceId(price.id)}
                          className={`rounded-2xl border p-4 text-left transition ${
                            selectedPrice.id === price.id
                              ? "border-primary bg-primary/10"
                              : "border-border bg-background hover:border-primary/30"
                          }`}
                        >
                          <span className="block text-sm font-bold">{billingModelLabels[price.billing_model]}</span>
                          <span className="mt-1 block text-sm text-muted-foreground">
                            {currency(price.total_amount, price.currency)}
                            {price.billing_model === "INSTALLMENT" && ` em até ${price.max_installments}x`}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2">
                    <span className="text-sm font-semibold">Nome para cobrança</span>
                    <input
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                      placeholder="Seu nome completo"
                    />
                  </label>
                  <label className="block space-y-2">
                    <span className="text-sm font-semibold">CPF ou CNPJ</span>
                    <input
                      value={cpfCnpj}
                      onChange={(event) => setCpfCnpj(event.target.value)}
                      className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                      placeholder="000.000.000-00"
                    />
                  </label>
                  <label className="block space-y-2">
                    <span className="text-sm font-semibold">Telefone</span>
                    <input
                      value={phone}
                      onChange={(event) => setPhone(event.target.value)}
                      className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                      placeholder="(21) 99999-9999"
                    />
                  </label>
                  <label className="block space-y-2">
                    <span className="text-sm font-semibold">Primeiro vencimento</span>
                    <input
                      type="date"
                      value={dueDate}
                      onChange={(event) => setDueDate(event.target.value)}
                      className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                    />
                  </label>
                </div>

                {selectedPrice.billing_model === "INSTALLMENT" && (
                  <label className="block space-y-2">
                    <span className="text-sm font-semibold">Quantidade de parcelas</span>
                    <select
                      value={installmentCount}
                      onChange={(event) => setInstallmentCount(Number(event.target.value))}
                      className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
                    >
                      {Array.from(
                        { length: selectedPrice.max_installments - selectedPrice.min_installments + 1 },
                        (_, index) => selectedPrice.min_installments + index,
                      ).map((count) => (
                        <option key={count} value={count}>
                          {count}x de aproximadamente {currency(String(Number(selectedPrice.total_amount) / count), selectedPrice.currency)}
                        </option>
                      ))}
                    </select>
                  </label>
                )}

                <div>
                  <span className="text-sm font-semibold">Forma de pagamento</span>
                  <div className="mt-3 grid gap-3 md:grid-cols-3">
                    {(["PIX", "BOLETO", "CREDIT_CARD"] as BillingType[]).map((item) => {
                      const disabled = item === "CREDIT_CARD";
                      const Icon = item === "PIX" ? QrCode : item === "BOLETO" ? FileText : CreditCard;
                      return (
                        <button
                          key={item}
                          type="button"
                          disabled={disabled}
                          onClick={() => setBillingType(item)}
                          className={`rounded-2xl border p-4 text-left text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55 ${
                            billingType === item ? "border-primary bg-primary/10 text-primary" : "border-border bg-background hover:bg-muted"
                          }`}
                        >
                          <Icon className="mb-2 h-5 w-5" />
                          {billingTypeLabels[item]}
                          {disabled && <small className="mt-1 block text-xs font-medium text-muted-foreground">Exige checkout/tokenização oficial</small>}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <Notice />
                <button
                  type="button"
                  onClick={handlePreview}
                  disabled={submitting || !cpfCnpj}
                  className="inline-flex w-full items-center justify-center rounded-2xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground shadow-sm transition hover:opacity-90 disabled:opacity-60 md:w-auto"
                >
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Revisar contratação
                </button>
              </div>
            )}

            {step === 2 && activePreview && (
              <div className="mt-8 space-y-5">
                <ReviewRow label="Plano" value={activePreview.plan.name} />
                <ReviewRow label="Modalidade" value={billingModelLabels[activePreview.checkout.billingModel]} />
                <ReviewRow label="Valor total" value={currency(activePreview.checkout.totalAmount, activePreview.plan_price.currency)} />
                <ReviewRow
                  label="Parcelamento"
                  value={
                    activePreview.checkout.installmentCount > 1
                      ? `${activePreview.checkout.installmentCount}x de aproximadamente ${currency(activePreview.checkout.installmentAmountEstimate, activePreview.plan_price.currency)}`
                      : "À vista"
                  }
                />
                <ReviewRow label="Primeiro vencimento" value={formatDate(activePreview.checkout.dueDate)} />
                <ReviewRow label="Forma de pagamento" value={billingTypeLabels[activePreview.checkout.billingType]} />
                <div className="rounded-2xl border border-warning/20 bg-warning-soft px-4 py-3 text-sm font-semibold text-warning">
                  A contratação será criada como pendente e o acesso só será liberado após o webhook do Asaas.
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
                    {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Confirmar contratação
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
                  <div className="flex-1">
                    <h2 className="text-xl font-bold">Contratação criada com segurança</h2>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      {result.payments?.length
                        ? `${result.payments.length} fatura(s) já foram sincronizadas. Acompanhe cada parcela na área de faturas.`
                        : "A contratação está aguardando a primeira cobrança gerada pelo Asaas."}
                    </p>
                    <div className="mt-5 flex flex-wrap gap-3">
                      <Link href="/dashboard/assinatura/faturas" className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">
                        Ver minhas faturas
                      </Link>
                      {result.payments?.[0]?.invoice_url && (
                        <a href={result.payments[0].invoice_url} target="_blank" rel="noreferrer" className="rounded-xl border border-border px-5 py-2.5 text-sm font-bold hover:bg-muted">
                          Abrir primeira cobrança
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <aside className="space-y-4">
            <PlanSummary plan={selectedPlan} price={selectedPrice} installmentCount={installmentCount} />
            <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
              <h2 className="text-lg font-bold">Proteções do fluxo</h2>
              <ol className="mt-4 space-y-3 text-sm text-muted-foreground">
                <li>1. O backend usa o preço cadastrado, nunca o valor enviado pelo navegador.</li>
                <li>2. A chave de idempotência evita cobranças duplicadas.</li>
                <li>3. Parcelas são sincronizadas e exibidas individualmente.</li>
                <li>4. Somente o webhook confirmado libera o acesso.</li>
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
    <div className="flex items-center gap-2" aria-label={`Etapa ${step} de 3`}>
      {[1, 2, 3].map((item) => (
        <span key={item} className={`grid h-8 w-8 place-items-center rounded-full text-xs font-bold ${step >= item ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
          {step > item ? <Check className="h-4 w-4" /> : item}
        </span>
      ))}
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
      Os pagamentos são processados pelo Asaas. Nenhum dado clínico é enviado ao gateway.
    </div>
  );
}

function PlanSummary({ plan, price, installmentCount }: { plan: Plan; price: PlanPrice; installmentCount: number }) {
  const count = price.billing_model === "INSTALLMENT" ? installmentCount : 1;
  return (
    <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">Plano selecionado</span>
      <h2 className="mt-4 text-2xl font-bold">{plan.name}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{plan.description}</p>
      <div className="mt-5">
        <strong className="text-3xl font-extrabold">{currency(price.total_amount, price.currency)}</strong>
        <span className="ml-1 text-xs text-muted-foreground">/{price.billing_interval === "MONTHLY" ? "mês" : "ano"}</span>
      </div>
      {count > 1 && (
        <p className="mt-2 text-sm font-semibold text-primary">
          {count}x de aproximadamente {currency(String(Number(price.total_amount) / count), price.currency)}
        </p>
      )}
      {Number(price.discount_percentage) > 0 && (
        <p className="mt-2 text-sm font-semibold text-success">Economia de {price.discount_percentage}%</p>
      )}
      <ul className="mt-5 space-y-2 text-sm text-muted-foreground">
        {Object.entries(plan.features)
          .filter(([, enabled]) => enabled)
          .slice(0, 7)
          .map(([key]) => (
            <li key={key} className="flex items-center gap-2">
              <Check className="h-4 w-4 text-primary" /> {featureLabels[key] || key}
            </li>
          ))}
      </ul>
    </div>
  );
}
