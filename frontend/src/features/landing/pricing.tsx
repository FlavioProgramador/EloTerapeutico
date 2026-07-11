"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getCookie } from "cookies-next";
import { ArrowRight, Check, Loader2 } from "lucide-react";

import { listPlans } from "@/features/billing/api";
import type { Plan } from "@/features/billing/types";
import { Reveal } from "./motion";

const featureLabels: Record<keyof Plan["features"], string> = {
  agenda: "Agenda integrada",
  patients: "Cadastro de pacientes",
  clinical_records: "Prontuário clínico",
  financial: "Financeiro",
  documents: "Documentos",
  forms: "Formulários",
  reports: "Relatórios",
  ai: "Recursos de IA",
};

const fallbackPlans = [
  {
    name: "Essencial",
    slug: "essencial",
    description: "Plano inicial para organizar a rotina clínica.",
    features: ["Agenda e pacientes", "Prontuário eletrônico", "Configuração simples"],
  },
  {
    name: "Profissional",
    slug: "profissional",
    description: "Plano recomendado para terapeutas que precisam de mais controle.",
    features: ["Módulos avançados", "Mais limites de uso", "Gestão profissional"],
  },
  {
    name: "Premium",
    slug: "premium",
    description: "Plano completo para operar com recursos ampliados.",
    features: ["Relatórios", "Documentos e formulários", "Recursos premium"],
  },
];

function currency(value: string, currencyCode = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: currencyCode }).format(Number(value));
}

function planFeatures(plan: Plan) {
  const enabled = Object.entries(plan.features)
    .filter(([, active]) => active)
    .map(([key]) => featureLabels[key as keyof Plan["features"]]);

  if (!enabled.includes(featureLabels.patients)) enabled.unshift(featureLabels.patients);

  const limits = [
    plan.max_patients ? `Até ${plan.max_patients} pacientes` : "Pacientes ilimitados",
    plan.max_storage_mb ? `${plan.max_storage_mb} MB de armazenamento` : "Armazenamento conforme plano",
  ];

  return [...enabled, ...limits].slice(0, 6);
}

function checkoutHref(slug: string, isAuthenticated: boolean) {
  const checkout = `/checkout?plan=${encodeURIComponent(slug)}`;
  if (isAuthenticated) return checkout;
  return `/register?plan=${encodeURIComponent(slug)}&mode=paid&next=${encodeURIComponent(checkout)}`;
}

function trialHref(slug: string) {
  return `/register?plan=${encodeURIComponent(slug)}&mode=trial&next=${encodeURIComponent("/dashboard")}`;
}

export function Pricing() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasApiError, setHasApiError] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(Boolean(getCookie("auth_token")));
    let mounted = true;
    async function load() {
      try {
        const data = await listPlans();
        if (mounted) {
          setPlans(data);
          setHasApiError(false);
        }
      } catch {
        if (mounted) setHasApiError(true);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  const orderedPlans = useMemo(() => {
    return [...plans].sort((a, b) => {
      const order = ["essencial", "profissional", "premium"];
      return order.indexOf(a.slug) - order.indexOf(b.slug);
    });
  }, [plans]);

  return (
    <section id="precos" className="pricing-section">
      <div className="pricing-section__inner">
        <Reveal className="pricing-section__heading">
          <span className="landing-eyebrow">Planos</span>
          <h2>Escolha o plano certo para sua prática.</h2>
          <p>
            Comece com 7 dias grátis ou assine diretamente. Os pagamentos são processados pelo Asaas, sem armazenar cartão, CVV ou dados sensíveis no Elo Terapêutico.
          </p>
        </Reveal>

        {loading ? (
          <div className="pricing-section__loading">
            <Loader2 aria-hidden="true" /> Carregando planos...
          </div>
        ) : hasApiError || orderedPlans.length === 0 ? (
          <div className="pricing-section__grid">
            {fallbackPlans.map((plan, i) => (
              <Reveal key={plan.slug} className={`pricing-card ${plan.slug === "profissional" ? "pricing-card--highlighted" : ""}`} delay={i * 0.06}>
                {plan.slug === "profissional" && <span className="pricing-card__badge">Recomendado</span>}
                <div className="pricing-card__header">
                  <span className="pricing-card__name">{plan.name}</span>
                  <div className="pricing-card__price">
                    <strong>Indisponível</strong>
                    <small>tente novamente</small>
                  </div>
                  <p className="pricing-card__desc">{plan.description}</p>
                </div>
                <ul className="pricing-card__features">
                  {plan.features.map((feature) => (
                    <li key={feature}>
                      <Check aria-hidden="true" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link href="/planos" className={`pricing-card__cta ${plan.slug === "profissional" ? "pricing-card__cta--primary" : ""}`}>
                  Ver planos
                  <ArrowRight aria-hidden="true" />
                </Link>
              </Reveal>
            ))}
          </div>
        ) : (
          <div className="pricing-section__grid">
            {orderedPlans.map((plan, i) => {
              const highlighted = plan.slug === "profissional";
              const defaultPrice = plan.prices[0];
              const amount = plan.price ?? defaultPrice?.total_amount ?? "0.00";
              const currencyCode = plan.currency ?? defaultPrice?.currency ?? "BRL";
              const interval = plan.billing_cycle ?? defaultPrice?.billing_interval ?? "MONTHLY";
              return (
                <Reveal key={plan.slug} className={`pricing-card ${highlighted ? "pricing-card--highlighted" : ""}`} delay={i * 0.06}>
                  {highlighted && <span className="pricing-card__badge">Recomendado</span>}
                  <div className="pricing-card__header">
                    <span className="pricing-card__name">{plan.name}</span>
                    <div className="pricing-card__price">
                      <strong>{currency(amount, currencyCode)}</strong>
                      <small>/{interval === "MONTHLY" ? "mês" : "ano"}</small>
                    </div>
                    <p className="pricing-card__desc">{plan.description}</p>
                  </div>
                  <ul className="pricing-card__features">
                    {planFeatures(plan).map((feature) => (
                      <li key={feature}>
                        <Check aria-hidden="true" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  {isAuthenticated ? (
                    <Link href={checkoutHref(plan.slug, true)} className={`pricing-card__cta ${highlighted ? "pricing-card__cta--primary" : ""}`}>
                      Escolher plano
                      <ArrowRight aria-hidden="true" />
                    </Link>
                  ) : (
                    <div className="grid gap-2">
                      <Link href={trialHref(plan.slug)} className="pricing-card__cta pricing-card__cta--primary">
                        Começar teste grátis
                        <ArrowRight aria-hidden="true" />
                      </Link>
                      <Link href={checkoutHref(plan.slug, false)} className="pricing-card__cta">
                        Assinar agora
                        <ArrowRight aria-hidden="true" />
                      </Link>
                    </div>
                  )}
                </Reveal>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
