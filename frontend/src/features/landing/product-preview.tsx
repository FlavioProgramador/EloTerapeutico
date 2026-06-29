"use client";

import { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { productTabs, type ProductTabId } from "./content";
import { Reveal } from "./motion";

export function ProductPreview() {
  const [activeTab, setActiveTab] = useState<ProductTabId>("overview");
  const active = productTabs.find((item) => item.id === activeTab) ?? productTabs[0];

  return (
    <section id="produto" className="scroll-mt-24 border-y border-border bg-card/35 py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <Reveal className="mx-auto max-w-3xl text-center">
          <span className="landing-eyebrow">Produto em contexto</span>
          <h2 className="mt-5 text-balance text-3xl font-extrabold tracking-tight text-foreground sm:text-5xl">
            Veja como os módulos trabalham juntos
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-muted-foreground">
            Uma demonstração visual baseada nas áreas reais do projeto. Os dados exibidos são ilustrativos.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-8 lg:grid-cols-[0.72fr_1.28fr] lg:items-center">
          <Reveal>
            <div role="tablist" aria-label="Módulos da plataforma" className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
              {productTabs.map((tab) => (
                <button
                  key={tab.id}
                  id={`tab-${tab.id}`}
                  role="tab"
                  type="button"
                  aria-selected={activeTab === tab.id}
                  aria-controls={`panel-${tab.id}`}
                  onClick={() => setActiveTab(tab.id)}
                  className={activeTab === tab.id ? "rounded-2xl border border-accent/50 bg-secondary p-4 text-left text-foreground shadow-lg" : "rounded-2xl border border-border bg-background/30 p-4 text-left text-muted-foreground hover:bg-secondary/50"}
                >
                  <span className="text-sm font-extrabold">{tab.label}</span>
                  <span className="mt-1 block text-xs leading-5 opacity-80">{tab.eyebrow}</span>
                </button>
              ))}
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="landing-product-frame">
              <div className="border-b border-border px-5 py-4 text-right text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                Dados demonstrativos
              </div>
              <div id={`panel-${active.id}`} role="tabpanel" aria-labelledby={`tab-${active.id}`} className="p-5 sm:p-7">
                <p className="text-xs font-bold uppercase tracking-widest text-accent">{active.eyebrow}</p>
                <h3 className="mt-3 text-2xl font-extrabold text-foreground">{active.title}</h3>
                <p className="mt-4 max-w-2xl leading-7 text-muted-foreground">{active.description}</p>
                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  {active.bullets.map((bullet) => (
                    <div key={bullet} className="rounded-2xl border border-border bg-background/45 p-4">
                      <CheckCircle2 className="h-4 w-4 text-accent" />
                      <p className="mt-4 text-sm font-bold leading-6 text-foreground">{bullet}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
