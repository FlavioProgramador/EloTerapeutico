"use client";

import { AlertCircle, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

import { CheckoutCustomerStep } from "./checkout/checkout-customer-step";
import { CheckoutPlanSummary } from "./checkout/checkout-plan-summary";
import { CheckoutReviewStep } from "./checkout/checkout-review-step";
import {
  CheckoutProtections,
  CheckoutStepIndicator,
} from "./checkout/checkout-shared";
import { CheckoutSuccessStep } from "./checkout/checkout-success-step";
import { useCheckoutWizard } from "./hooks/use-checkout-wizard";

export function CheckoutWizard() {
  const controller = useCheckoutWizard();

  if (
    controller.authLoading ||
    (!controller.isAuthenticated && !controller.authLoading) ||
    controller.plansQuery.isLoading
  ) {
    return <CheckoutLoadingState />;
  }

  if (
    controller.plansQuery.isError ||
    !controller.selectedPlan ||
    !controller.selectedPrice
  ) {
    return (
      <CheckoutUnavailableState
        loadFailed={controller.plansQuery.isError}
        onRetry={() => controller.plansQuery.refetch()}
      />
    );
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8 text-foreground md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <Link
          href="/planos"
          className="inline-flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Voltar para planos
        </Link>

        <section className="grid gap-6 lg:grid-cols-[1.12fr_0.88fr]">
          <div className="rounded-3xl border border-border bg-card p-6 shadow-sm md:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <span className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
                  Checkout seguro Asaas
                </span>
                <h1 className="mt-4 text-3xl font-bold tracking-tight md:text-4xl">
                  Finalize sua assinatura
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  O plano será liberado somente após a confirmação do pagamento
                  pelo backend.
                </p>
              </div>
              <CheckoutStepIndicator step={controller.step} />
            </div>

            {controller.error && (
              <div className="mt-6 rounded-2xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm font-semibold text-danger">
                {controller.error}
              </div>
            )}

            {controller.step === 1 && (
              <CheckoutCustomerStep controller={controller} />
            )}
            {controller.step === 2 && (
              <CheckoutReviewStep controller={controller} />
            )}
            {controller.step === 3 && (
              <CheckoutSuccessStep controller={controller} />
            )}
          </div>

          <aside className="space-y-4">
            <CheckoutPlanSummary
              plan={controller.selectedPlan}
              price={controller.selectedPrice}
              installmentCount={controller.installmentCount}
            />
            <CheckoutProtections />
          </aside>
        </section>
      </div>
    </main>
  );
}

function CheckoutLoadingState() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
        <Loader2 className="h-4 w-4 animate-spin" /> Preparando checkout seguro...
      </div>
    </main>
  );
}

function CheckoutUnavailableState({
  loadFailed,
  onRetry,
}: {
  loadFailed: boolean;
  onRetry: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="max-w-md rounded-3xl border border-border bg-card p-8 text-center shadow-sm">
        <AlertCircle className="mx-auto h-8 w-8 text-danger" />
        <h1 className="mt-4 text-xl font-bold">
          {loadFailed
            ? "Não foi possível carregar os planos"
            : "Opção de contratação indisponível"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {loadFailed
            ? "Tente novamente em instantes."
            : "Cadastre um preço ativo para este plano no painel administrativo."}
        </p>
        {loadFailed ? (
          <button
            type="button"
            onClick={onRetry}
            className="mt-5 inline-flex rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground"
          >
            Tentar novamente
          </button>
        ) : (
          <Link
            href="/planos"
            className="mt-5 inline-flex rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground"
          >
            Ver planos
          </Link>
        )}
      </div>
    </main>
  );
}
