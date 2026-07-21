"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Phone,
  ShieldCheck,
  User,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  registerSchema,
  type RegisterFormData,
} from "@/features/auth/schemas/auth.schemas";
import { authService } from "@/features/auth/services/auth.service";
import { listPlans } from "@/features/billing/api";
import type { Plan, PlanPrice } from "@/features/billing/types";
import { Brand } from "@/features/landing/brand";
import { safeInternalPath } from "@/lib/auth-flow";
import { getPublicErrorMessage } from "@/lib/errors/public-error";

type AccessMode = "TRIAL" | "PAID";
type BillingCycle = "MONTHLY" | "YEARLY";
type PaymentMode = "RECURRING" | "ONE_TIME" | "INSTALLMENT";

interface RegistrationSelection {
  plan: string;
  price: string;
  accessMode: AccessMode;
  billingCycle?: BillingCycle;
  paymentMode?: PaymentMode;
}

function selectionFromParams(params: URLSearchParams): RegistrationSelection {
  const billingCycle = (
    params.get("billing_cycle") ||
    params.get("interval") ||
    ""
  ).toUpperCase();
  const paymentMode = (params.get("payment_mode") || "").toUpperCase();

  return {
    plan: params.get("plan") || params.get("plan_slug") || "",
    price:
      params.get("price") ||
      params.get("plan_price_slug") ||
      params.get("plan_price_id") ||
      "",
    accessMode: params.get("mode")?.toUpperCase() === "PAID" ? "PAID" : "TRIAL",
    billingCycle: billingCycle
      ? (billingCycle as BillingCycle)
      : undefined,
    paymentMode: paymentMode ? (paymentMode as PaymentMode) : undefined,
  };
}

function currency(value: string, currencyCode = "BRL") {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currencyCode,
  }).format(Number(value));
}

function billingIntervalLabel(value: PlanPrice["billing_interval"]): string {
  return value === "YEARLY" ? "Anual" : "Mensal";
}

function billingModelLabel(value: PlanPrice["billing_model"]): string {
  if (value === "INSTALLMENT") return "Parcelado";
  if (value === "ONE_TIME") return "Pagamento único";
  return "Recorrente";
}

function findPrice(
  plans: Plan[],
  selection: RegistrationSelection,
): { plan?: Plan; price?: PlanPrice } {
  const selectedPlan =
    plans.find((plan) => plan.slug === selection.plan) ||
    plans.find((plan) =>
      plan.prices.some(
        (price) =>
          String(price.id) === selection.price ||
          price.slug === selection.price,
      ),
    );
  if (!selectedPlan) return {};

  const selectedPrice =
    selectedPlan.prices.find(
      (price) =>
        String(price.id) === selection.price || price.slug === selection.price,
    ) ||
    selectedPlan.prices.find((price) => {
      const intervalMatches =
        !selection.billingCycle ||
        price.billing_interval === selection.billingCycle;
      const modeMatches =
        !selection.paymentMode || price.billing_model === selection.paymentMode;
      return intervalMatches && modeMatches && price.available;
    }) ||
    selectedPlan.prices.find((price) => price.available);

  return { plan: selectedPlan, price: selectedPrice };
}

function PlanSummary({
  selected,
  plansLoading,
  accessMode,
}: {
  selected: { plan?: Plan; price?: PlanPrice };
  plansLoading: boolean;
  accessMode: AccessMode;
}) {
  return (
    <div className="absolute bottom-8 right-8 z-10 w-[min(26rem,calc(100%-4rem))] rounded-3xl border border-primary/20 bg-white/90 p-6 shadow-2xl shadow-primary/15 backdrop-blur-md xl:bottom-10 xl:right-10 xl:p-7">
      <div className="mb-5 flex items-center gap-3">
        <span className="grid h-11 w-11 place-items-center rounded-full border border-primary/20 bg-primary-soft text-primary">
          <ShieldCheck className="h-6 w-6" aria-hidden="true" />
        </span>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-primary">
            Resumo da contratação
          </p>
          <h2 className="mt-1 text-lg font-bold text-foreground">
            {selected.plan?.name || "Elo Terapêutico"}
          </h2>
        </div>
      </div>

      {plansLoading ? (
        <div className="rounded-2xl border border-primary/10 bg-primary-soft/70 p-5 text-sm text-muted-foreground">
          Carregando informações do plano...
        </div>
      ) : selected.plan && selected.price ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-2xl border border-primary/10 bg-white/75 p-3">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Ciclo
              </span>
              <strong className="mt-1 block text-sm text-foreground">
                {billingIntervalLabel(selected.price.billing_interval)}
              </strong>
            </div>
            <div className="rounded-2xl border border-primary/10 bg-white/75 p-3">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Modalidade
              </span>
              <strong className="mt-1 block text-sm text-foreground">
                {billingModelLabel(selected.price.billing_model)}
              </strong>
            </div>
          </div>

          <div className="rounded-2xl border border-primary/20 bg-primary-soft p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-primary">
              Valor total
            </p>
            <p className="mt-1 text-3xl font-extrabold text-primary">
              {currency(
                selected.price.total_amount,
                selected.price.currency,
              )}
            </p>
            {selected.price.billing_model === "INSTALLMENT" && (
              <p className="mt-1 text-xs text-primary/75">
                Até {selected.price.max_installments} parcelas, conforme o checkout.
              </p>
            )}
          </div>

          {accessMode === "TRIAL" && (
            <div className="flex items-center gap-3 rounded-2xl border border-primary/20 bg-white/80 p-3 text-sm text-foreground">
              <CheckCircle2
                className="h-5 w-5 shrink-0 text-primary"
                aria-hidden="true"
              />
              <span className="font-medium">Período de avaliação incluído.</span>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-2xl border border-primary/10 bg-white/75 p-5 text-sm text-muted-foreground">
          Sua conta será criada e você poderá comparar os planos disponíveis em
          seguida.
        </div>
      )}

      <Link
        href="/planos"
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl p-2 text-sm font-bold text-primary transition-colors hover:bg-primary-soft hover:text-primary-hover"
      >
        Alterar ou escolher plano <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [plansLoading, setPlansLoading] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const selection = useMemo(
    () => selectionFromParams(new URLSearchParams(searchParams.toString())),
    [searchParams],
  );
  const selected = useMemo(
    () => findPrice(plans, selection),
    [plans, selection],
  );

  useEffect(() => {
    let active = true;
    void listPlans()
      .then((result) => {
        if (active) setPlans(result);
      })
      .catch(() => {
        if (active) setPlans([]);
      })
      .finally(() => {
        if (active) setPlansLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      role: "therapist",
      terms_accepted: false,
      privacy_accepted: false,
    },
  });

  const loginParams = new URLSearchParams();
  if (selection.plan) loginParams.set("plan", selection.plan);
  if (selection.price) loginParams.set("price", selection.price);
  const loginHref = `/login${loginParams.size ? `?${loginParams.toString()}` : ""}`;

  const onSubmit = async (data: RegisterFormData) => {
    try {
      const response = await authService.register({
        email: data.email,
        full_name: data.full_name,
        phone: data.phone || "",
        password: data.password,
        password_confirm: data.confirm_password,
        role: data.role,
        crp: data.crp || "",
        specialty: data.specialty || "",
        terms_accepted: data.terms_accepted,
        privacy_accepted: data.privacy_accepted,
        plan: selection.plan || undefined,
        plan_price_slug: selection.price || undefined,
        billing_cycle: selection.billingCycle,
        payment_mode: selection.paymentMode,
        access_mode: selection.accessMode,
      });

      toast.success("Conta criada com sucesso", {
        description:
          selection.accessMode === "TRIAL"
            ? "Seu acesso de avaliação foi iniciado."
            : "Continue para concluir a assinatura selecionada.",
      });

      router.replace(
        safeInternalPath(
          response.next,
          selection.plan ? "/onboarding" : "/planos",
        ),
      );
    } catch (error: unknown) {
      toast.error("Não foi possível criar sua conta", {
        description: getPublicErrorMessage(
          error,
          "Revise os dados informados e tente novamente.",
        ),
      });
    }
  };

  return (
    <main className="flex min-h-screen overflow-hidden bg-background font-sans text-foreground">
      <section className="relative z-10 flex w-full flex-col justify-center overflow-y-auto border-r border-primary/10 bg-background px-5 py-10 sm:px-10 lg:w-[45%] lg:px-14 xl:w-[40%] xl:px-16">
        <div
          className="pointer-events-none absolute -left-28 top-1/3 h-80 w-80 rounded-full bg-primary/8 blur-3xl"
          aria-hidden="true"
        />
        <div className="relative mx-auto w-full max-w-2xl py-8 lg:py-12">
          <Brand />
          <div className="mt-7">
            <span className="inline-flex rounded-full border border-primary/20 bg-primary-soft px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-primary">
              Crie sua conta
            </span>
            <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Comece com segurança e sem surpresas.
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
              A conta é criada primeiro. O acesso às ferramentas depende de uma
              assinatura ativa ou período de avaliação válido.
            </p>
          </div>

          <form
            className="mt-8 grid gap-5 rounded-2xl border border-primary/10 bg-card p-5 shadow-sm shadow-primary/5 sm:p-6"
            onSubmit={handleSubmit(onSubmit)}
            noValidate
          >
            <Input
              id="register-full-name"
              label="Nome completo"
              type="text"
              autoComplete="name"
              error={errors.full_name?.message}
              leftIcon={
                <User className="h-5 w-5 text-primary" aria-hidden="true" />
              }
              {...register("full_name")}
            />

            <div className="grid gap-5 sm:grid-cols-2">
              <Input
                id="register-email"
                label="E-mail"
                type="email"
                autoComplete="email"
                error={errors.email?.message}
                leftIcon={
                  <Mail className="h-5 w-5 text-primary" aria-hidden="true" />
                }
                {...register("email")}
              />
              <Input
                id="register-phone"
                label="Telefone"
                type="tel"
                autoComplete="tel"
                error={errors.phone?.message}
                leftIcon={
                  <Phone className="h-5 w-5 text-primary" aria-hidden="true" />
                }
                {...register("phone")}
              />
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <Input
                id="register-crp"
                label="Registro profissional"
                type="text"
                autoComplete="off"
                error={errors.crp?.message}
                placeholder="Opcional"
                {...register("crp")}
              />
              <Input
                id="register-specialty"
                label="Especialidade"
                type="text"
                autoComplete="organization-title"
                error={errors.specialty?.message}
                placeholder="Opcional"
                {...register("specialty")}
              />
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <Input
                id="register-password"
                label="Senha"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                error={errors.password?.message}
                leftIcon={
                  <Lock className="h-5 w-5 text-primary" aria-hidden="true" />
                }
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="text-muted-foreground hover:text-primary"
                    aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <Eye className="h-5 w-5" aria-hidden="true" />
                    )}
                  </button>
                }
                {...register("password")}
              />
              <Input
                id="register-confirm-password"
                label="Confirmar senha"
                type={showConfirmPassword ? "text" : "password"}
                autoComplete="new-password"
                error={errors.confirm_password?.message}
                leftIcon={
                  <Lock className="h-5 w-5 text-primary" aria-hidden="true" />
                }
                rightIcon={
                  <button
                    type="button"
                    onClick={() =>
                      setShowConfirmPassword((current) => !current)
                    }
                    className="text-muted-foreground hover:text-primary"
                    aria-label={
                      showConfirmPassword ? "Ocultar senha" : "Mostrar senha"
                    }
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <Eye className="h-5 w-5" aria-hidden="true" />
                    )}
                  </button>
                }
                {...register("confirm_password")}
              />
            </div>

            <div className="space-y-3 rounded-xl border border-primary/10 bg-primary-soft/45 p-4">
              <label className="flex items-start gap-3 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-input accent-primary"
                  aria-invalid={Boolean(errors.terms_accepted)}
                  {...register("terms_accepted")}
                />
                <span>
                  Li e aceito os{" "}
                  <Link
                    href="/termos-de-uso"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-semibold text-primary hover:underline"
                  >
                    Termos de Uso
                  </Link>
                  .
                </span>
              </label>
              {errors.terms_accepted && (
                <p className="text-xs text-danger" role="alert">
                  {errors.terms_accepted.message}
                </p>
              )}

              <label className="flex items-start gap-3 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-input accent-primary"
                  aria-invalid={Boolean(errors.privacy_accepted)}
                  {...register("privacy_accepted")}
                />
                <span>
                  Li e aceito a{" "}
                  <Link
                    href="/politica-de-privacidade"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-semibold text-primary hover:underline"
                  >
                    Política de Privacidade
                  </Link>
                  .
                </span>
              </label>
              {errors.privacy_accepted && (
                <p className="text-xs text-danger" role="alert">
                  {errors.privacy_accepted.message}
                </p>
              )}
            </div>

            <Button
              id="register-submit"
              type="submit"
              className="w-full font-bold shadow-lg shadow-primary/20 sm:w-auto"
              isLoading={isSubmitting}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Criar conta
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            Já possui uma conta?{" "}
            <Link
              href={loginHref}
              className="font-semibold text-primary hover:text-primary-hover hover:underline"
            >
              Entrar
            </Link>
          </p>
        </div>
      </section>

      <aside className="relative hidden overflow-hidden bg-primary-soft lg:block lg:w-[55%] xl:w-[60%]">
        <Image
          src="/register_illustration.svg"
          alt="Ilustração de um ambiente terapêutico acolhedor"
          fill
          priority
          sizes="(min-width: 1280px) 60vw, 55vw"
          className="object-cover object-left"
        />
        <div
          className="absolute inset-0 bg-gradient-to-t from-primary/24 via-primary/5 to-transparent"
          aria-hidden="true"
        />
        <PlanSummary
          selected={selected}
          plansLoading={plansLoading}
          accessMode={selection.accessMode}
        />
      </aside>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <main className="grid min-h-screen place-items-center bg-background p-6">
          <p className="text-sm text-muted-foreground">
            Carregando cadastro...
          </p>
        </main>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
