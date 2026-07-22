"use client";

import { useState } from "react";
import { Headphones, ShieldCheck, VideoOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { TelemedicinePublicContext } from "../types";

interface TelemedicineConsentProps {
  context: TelemedicinePublicContext;
  submitting: boolean;
  onAccept: (responsibleGuardianName: string) => Promise<void>;
}

export function TelemedicineConsent({
  context,
  submitting,
  onAccept,
}: TelemedicineConsentProps) {
  const [accepted, setAccepted] = useState(false);
  const [guardianName, setGuardianName] = useState("");

  return (
    <section className="space-y-5" aria-labelledby="telemedicine-consent-title">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Consentimento · {context.consent_version}
        </p>
        <h2 id="telemedicine-consent-title" className="mt-2 text-xl font-bold">
          Antes de entrar no atendimento
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Leia as orientações com atenção. Você pode recusar a modalidade online
          e conversar com o profissional sobre uma alternativa.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Guidance icon={<ShieldCheck className="size-4" />} text="Use um ambiente reservado e uma rede confiável." />
        <Guidance icon={<Headphones className="size-4" />} text="Use fones quando possível para preservar o sigilo." />
        <Guidance icon={<VideoOff className="size-4" />} text="O Elo Terapêutico não grava áudio ou vídeo." />
      </div>

      <div className="max-h-56 overflow-y-auto rounded-xl border border-border bg-secondary/20 p-4 text-sm leading-6 text-muted-foreground">
        {context.consent_text}
      </div>

      <label className="space-y-1.5 text-sm font-medium">
        <span>Nome do responsável legal, quando aplicável</span>
        <input
          value={guardianName}
          onChange={(event) => setGuardianName(event.target.value)}
          maxLength={180}
          autoComplete="name"
          className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
          placeholder="Deixe em branco quando não se aplicar"
        />
      </label>

      <label className="flex items-start gap-3 rounded-xl border border-border p-4 text-sm">
        <input
          type="checkbox"
          checked={accepted}
          onChange={(event) => setAccepted(event.target.checked)}
          className="mt-0.5 size-4 accent-primary"
        />
        <span>
          Li as informações, compreendi as condições do atendimento online e
          concordo em prosseguir.
        </span>
      </label>

      <div className="rounded-xl border border-amber-500/25 bg-amber-500/10 p-4 text-xs leading-5 text-muted-foreground">
        Esta sala não substitui serviços de emergência. Em uma situação urgente,
        procure os serviços públicos de atendimento da sua região.
      </div>

      <Button
        className="w-full"
        size="lg"
        disabled={!accepted || submitting}
        onClick={() => onAccept(guardianName.trim())}
      >
        {submitting ? "Registrando consentimento..." : "Aceitar e testar dispositivos"}
      </Button>
    </section>
  );
}

function Guidance({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-border p-3 text-xs text-muted-foreground">
      <span className="mt-0.5 text-primary">{icon}</span>
      <span>{text}</span>
    </div>
  );
}
