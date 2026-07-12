"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, Clock3, CreditCard, Loader2, RefreshCw } from "lucide-react";

import { getMySubscription } from "./api";
import type { Subscription } from "./types";

type AccessState = "pending" | "past-due" | "expired";

const copy = {
  pending: {
    eyebrow: "Pagamento pendente",
    title: "Aguardando confirmação do pagamento",
    description: "A cobrança foi criada, mas o acesso só será liberado após a confirmação segura recebida pelo webhook do gateway.",
    icon: Clock3,
    primary: { href: "/dashboard/assinatura/faturas", label: "Acompanhar faturas" },
  },
  "past-due": {
    eyebrow: "Regularização necessária",
    title: "Existe uma cobrança vencida",
    description: "Entre na área de faturas para atualizar a cobrança ou escolher uma nova forma de pagamento. Seus dados permanecem preservados.",
    icon: AlertTriangle,
    primary: { href: "/dashboard/assinatura/faturas", label: "Regularizar cobrança" },
  },
  expired: {
    eyebrow: "Acesso expirado",
    title: "Escolha um plano para continuar",
    description: "O teste ou período contratado terminou. Sua conta e seus dados continuam salvos, mas as ferramentas internas estão bloqueadas.",
    icon: RefreshCw,
    primary: { href: "/planos", label: "Ver planos" },
  },
} satisfies Record<AccessState, {
  eyebrow: string;
  title: string;
  description: string;
  icon: typeof Clock3;
  primary: { href: string; label: string };
}>;

function formatDate(value?: string | null) {
  if (!value) return null;
  return new Intl.DateTimeFormat("pt-BR").format(new Date(value));
}

export function AccessStatePage({ state }: { state: AccessState }) {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const content = copy[state];
  const Icon = content.icon;

  useEffect(() => {
    void getMySubscription().then(setSubscription).catch(() => setSubscription(null)).finally(() => setLoading(false));
  }, []);

  return (
    <main className="grid min-h-screen place-items-center bg-[#F7FAF8] px-5 py-12 text-[#1A2E26]">
      <section className="w-full max-w-2xl rounded-[32px] border border-[#1A2E26]/10 bg-white p-7 text-center shadow-sm sm:p-10">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-[#FFF7ED] text-[#F97316]"><Icon className="h-8 w-8" /></div>
        <p className="mt-6 text-xs font-extrabold uppercase tracking-[0.22em] text-[#F97316]">{content.eyebrow}</p>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">{content.title}</h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-gray-600">{content.description}</p>

        <div className="mt-7 rounded-2xl border border-gray-100 bg-gray-50 p-5 text-left text-sm">
          {loading ? (
            <div className="flex items-center gap-2 text-gray-500"><Loader2 className="h-4 w-4 animate-spin" /> Consultando assinatura...</div>
          ) : subscription ? (
            <dl className="grid gap-3 sm:grid-cols-2">
              <div><dt className="text-gray-500">Plano</dt><dd className="font-bold text-gray-900">{subscription.plan.name}</dd></div>
              <div><dt className="text-gray-500">Status</dt><dd className="font-bold text-gray-900">{subscription.status}</dd></div>
              {subscription.trial_ends_at && <div><dt className="text-gray-500">Fim do teste</dt><dd className="font-bold text-gray-900">{formatDate(subscription.trial_ends_at)}</dd></div>}
              {subscription.current_period_end && <div><dt className="text-gray-500">Fim do período</dt><dd className="font-bold text-gray-900">{formatDate(subscription.current_period_end)}</dd></div>}
            </dl>
          ) : (
            <p className="text-gray-600">Nenhuma assinatura operacional foi localizada. Escolha um plano para regularizar a conta.</p>
          )}
        </div>

        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Link href={content.primary.href} className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#F97316] px-5 py-3 text-sm font-bold text-white hover:bg-[#EA580C]"><CreditCard className="h-4 w-4" /> {content.primary.label}</Link>
          <Link href="/dashboard/assinatura" className="rounded-xl border border-gray-200 px-5 py-3 text-sm font-bold text-gray-700 hover:bg-gray-50">Gerenciar assinatura</Link>
          <Link href="/" className="rounded-xl border border-gray-200 px-5 py-3 text-sm font-bold text-gray-700 hover:bg-gray-50">Página inicial</Link>
        </div>
      </section>
    </main>
  );
}
