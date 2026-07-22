"use client";

import { PreJoin } from "@livekit/components-react";
import { ShieldCheck } from "lucide-react";

import type { TelemedicineDeviceChoices, TelemedicineRole } from "../types";

interface TelemedicinePreJoinProps {
  role: TelemedicineRole;
  joining: boolean;
  onJoin: (choices: TelemedicineDeviceChoices) => Promise<void>;
  onError: (message: string) => void;
}

export function TelemedicinePreJoin({
  role,
  joining,
  onJoin,
  onError,
}: TelemedicinePreJoinProps) {
  return (
    <section className="space-y-4" aria-labelledby="telemedicine-prejoin-title">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Teste de câmera e microfone
        </p>
        <h2 id="telemedicine-prejoin-title" className="mt-2 text-xl font-bold">
          Confira seus dispositivos
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Você pode entrar sem câmera. O microfone é recomendado para o
          atendimento.
        </p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-border bg-card p-3">
        <PreJoin
          persistUserChoices={false}
          joinLabel={joining ? "Preparando sala..." : "Entrar no atendimento"}
          micLabel="Microfone"
          camLabel="Câmera"
          userLabel="Nome de exibição"
          defaults={{
            username: role === "patient" ? "Paciente" : "Profissional",
            audioEnabled: true,
            videoEnabled: true,
          }}
          onError={(error) =>
            onError(
              error?.message ||
                "Não foi possível acessar câmera ou microfone. Revise as permissões do navegador.",
            )
          }
          onSubmit={(values) =>
            onJoin({
              username:
                values.username ||
                (role === "patient" ? "Paciente" : "Profissional"),
              audioEnabled: Boolean(values.audioEnabled),
              videoEnabled: Boolean(values.videoEnabled),
              audioDeviceId: values.audioDeviceId || "",
              videoDeviceId: values.videoDeviceId || "",
            })
          }
        />
      </div>

      <div className="flex items-start gap-2 rounded-xl border border-primary/20 bg-primary/5 p-4 text-xs text-muted-foreground">
        <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
        A mídia será protegida com criptografia ponta a ponta antes da conexão.
        Suas escolhas não são salvas no navegador.
      </div>
    </section>
  );
}
