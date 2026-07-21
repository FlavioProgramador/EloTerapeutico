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
    <main className="grid min-h-screen bg-background font-sans text-foreground lg:grid-cols-[minmax(0,1fr)_minmax(22rem,0.72fr)]">
      <section className="flex items-center px-5 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto w-full max-w-2xl">
          <Brand />
          <div className="mt-8">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">
              Crie sua conta
            </p>
            <h1 className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Comece com segurança e sem surpresas.
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
              A conta é criada primeiro. O acesso às ferramentas depende de uma
              assinatura ativa ou período de avaliação válido.
            </p>
          </div>

          <form
            className="mt-8 grid gap-5"
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
                <User className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
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
                  <Mail
                    className="h-5 w-5 text-muted-foreground"
                    aria-hidden="true"
                  />
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
                  <Phone
                    className="h-5 w-5 text-muted-foreground"
                    aria-hidden="true"
                  />
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
                  <Lock
                    className="h-5 w-5 text-muted-foreground"
                    aria-hidden="true"
                  />
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
                  <Lock
                    className="h-5 w-5 text-muted-foreground"
                    aria-hidden="true"
                  />
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

            <div className="space-y-3 rounded-xl border border-border bg-card p-4">
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
              className="w-full font-bold sm:w-auto"
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
              className="font-semibold text-primary hover:underline"
            >
              Entrar
            </Link>
          </p>
        </div>
      </section>

      <aside className="flex items-center border-l border-sidebar-border bg-sidebar p-6 text-sidebar-foreground sm:p-10">
        <div className="mx-auto w-full max-w-md space-y-6">
          <div className="rounded-xl border border-sidebar-border bg-sidebar-surface/80 p-6">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg border border-sidebar-active/25 bg-sidebar-active/10 text-sidebar-active">
                <ShieldCheck className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-sidebar-muted">
                  Seleção atual
                </p>
                <h2 className="text-base font-bold text-sidebar-foreground">
                  {selected.plan?.name || "Avaliação do Elo Terapêutico"}
                </h2>
              </div>
            </div>

            <div className="mt-5 border-t border-sidebar-border pt-5">
              {plansLoading ? (
                <p className="text-sm text-sidebar-muted">Carregando plano...</p>
              ) : selected.price ? (
                <>
                  <p className="text-2xl font-bold text-sidebar-active">
                    {currency(selected.price.amount, selected.price.currency)}
                  </p>
                  <p className="mt-1 text-xs text-sidebar-muted">
                    {selected.price.billing_interval_display} •{" "}
                    {selected.price.billing_model_display}
                  </p>
                </>
              ) : (
                <p className="text-sm text-sidebar-muted">
                  Você poderá escolher ou revisar o plano após criar a conta.
                </p>
              )}
            </div>
          </div>

          <ul className="space-y-3 text-sm text-sidebar-muted">
            {[
              "Tokens de acesso protegidos em cookies HttpOnly.",
              "Dados clínicos não participam do fluxo de cobrança.",
              "A assinatura só é ativada após confirmação segura do pagamento.",
            ].map((item) => (
              <li key={item} className="flex items-start gap-3">
                <CheckCircle2
                  className="mt-0.5 h-4 w-4 shrink-0 text-sidebar-active"
                  aria-hidden="true"
                />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
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
