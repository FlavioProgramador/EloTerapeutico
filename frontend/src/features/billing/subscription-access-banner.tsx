"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { AlertTriangle, Clock3 } from "lucide-react";

import { api } from "@/lib/api";

interface EntitlementResponse {
  allowed: boolean;
  code: string;
  message: string;
  redirect_to: string;
  trial_days_remaining: number | null;
  subscription: {
    status: string;
    trial_ends_at: string | null;
  } | null;
}

function trialMessage(
  daysRemaining: number | null,
  trialEndsAt?: string | null,
) {
  if (daysRemaining === null) return "Seu teste gratuito está ativo.";
  if (daysRemaining > 1)
    return `Teste gratuito: ${daysRemaining} dias restantes.`;
  if (daysRemaining === 1) return "Seu teste gratuito termina amanhã.";

  if (trialEndsAt) {
    const time = new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(trialEndsAt));
    return `Seu teste gratuito termina hoje às ${time}.`;
  }
  return "Seu teste gratuito termina hoje.";
}

export function SubscriptionAccessBanner() {
  const router = useRouter();
  const pathname = usePathname();
  const [entitlement, setEntitlement] = useState<EntitlementResponse | null>(
    null,
  );

  useEffect(() => {
    let mounted = true;

    async function loadEntitlement() {
      try {
        const response = await api.get<EntitlementResponse>(
          "billing/entitlement/",
        );
        if (!mounted) return;

        setEntitlement(response.data);
        if (
          !response.data.allowed &&
          !pathname.startsWith("/dashboard/assinatura")
        ) {
          router.replace(response.data.redirect_to || "/planos");
        }
      } catch {
        // O interceptor global trata 401 e 402. Não renderize conteúdo privado
        // até que o redirecionamento seja concluído.
      }
    }

    loadEntitlement();
    return () => {
      mounted = false;
    };
  }, [router, pathname]);

  if (!entitlement?.allowed) return null;

  if (entitlement.code === "TRIAL_ACTIVE") {
    return (
      <div
        role="status"
        className="mx-6 mt-4 flex items-center justify-between gap-3 rounded-lg border border-primary/20 bg-primary/5 px-4 py-2.5 text-sm text-foreground md:mx-8"
      >
        <span className="flex items-center gap-2">
          <Clock3 className="h-4 w-4 text-primary" aria-hidden="true" />
          {trialMessage(
            entitlement.trial_days_remaining,
            entitlement.subscription?.trial_ends_at,
          )}
        </span>
        <button
          type="button"
          onClick={() => router.push("/planos")}
          className="shrink-0 font-semibold text-primary hover:underline"
        >
          Ver planos
        </button>
      </div>
    );
  }

  if (entitlement.code === "PAYMENT_GRACE_PERIOD") {
    return (
      <div
        role="alert"
        className="mx-6 mt-4 flex items-center justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-sm text-foreground md:mx-8"
      >
        <span className="flex items-center gap-2">
          <AlertTriangle
            className="h-4 w-4 text-amber-600"
            aria-hidden="true"
          />
          Há um pagamento em atraso. Regularize antes do fim do período de
          tolerância.
        </span>
        <button
          type="button"
          onClick={() => router.push("/billing")}
          className="shrink-0 font-semibold text-amber-700 hover:underline dark:text-amber-400"
        >
          Ver cobrança
        </button>
      </div>
    );
  }

  return null;
}
