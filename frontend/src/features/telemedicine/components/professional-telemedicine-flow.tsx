"use client";

import { useCallback, useState } from "react";
import { ShieldCheck, Video } from "lucide-react";

import { telemedicineProfessionalService } from "../services/telemedicine.service";
import type {
  TelemedicineCredentials,
  TelemedicineDeviceChoices,
} from "../types";
import {
  TelemedicineEndedState,
  TelemedicineErrorState,
} from "./telemedicine-error-state";
import { TelemedicinePreJoin } from "./telemedicine-prejoin";
import { TelemedicineSession } from "./telemedicine-session";

interface ProfessionalTelemedicineFlowProps {
  roomId: number;
}

export function ProfessionalTelemedicineFlow({
  roomId,
}: ProfessionalTelemedicineFlowProps) {
  const [step, setStep] = useState<"prejoin" | "session" | "ended" | "error">(
    "prejoin",
  );
  const [joining, setJoining] = useState(false);
  const [credentials, setCredentials] = useState<TelemedicineCredentials>();
  const [choices, setChoices] = useState<TelemedicineDeviceChoices>();
  const [error, setError] = useState("");

  const fail = useCallback((message: string) => {
    setCredentials(undefined);
    setChoices(undefined);
    setError(message);
    setStep("error");
  }, []);

  const join = useCallback(
    async (deviceChoices: TelemedicineDeviceChoices) => {
      setJoining(true);
      try {
        const issued = await telemedicineProfessionalService.join(roomId);
        setChoices(deviceChoices);
        setCredentials(issued);
        setStep("session");
      } catch (reason: unknown) {
        fail(
          reason instanceof Error
            ? reason.message
            : "Não foi possível iniciar o atendimento.",
        );
      } finally {
        setJoining(false);
      }
    },
    [fail, roomId],
  );

  const disconnect = useCallback(() => {
    setCredentials(undefined);
    setChoices(undefined);
    setStep("ended");
  }, []);

  const finish = useCallback(async () => {
    await telemedicineProfessionalService.finish(roomId);
  }, [roomId]);

  return (
    <main className="min-h-screen bg-background p-4 sm:p-6">
      <section className="mx-auto w-full max-w-6xl rounded-2xl border border-border bg-card p-5 shadow-xl sm:p-7">
        <header className="mb-6 flex flex-wrap items-center gap-3 border-b border-border pb-5">
          <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
            <Video className="size-5" />
          </span>
          <div>
            <h1 className="text-xl font-bold">Atendimento online</h1>
            <p className="text-sm text-muted-foreground">
              Sala #{roomId} · acesso profissional autenticado
            </p>
          </div>
          <span className="ml-auto inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-700">
            <ShieldCheck className="size-3.5" />
            E2EE obrigatória
          </span>
        </header>

        {step === "prejoin" ? (
          <TelemedicinePreJoin
            role="professional"
            joining={joining}
            onJoin={join}
            onError={fail}
          />
        ) : null}
        {step === "session" && credentials && choices ? (
          <TelemedicineSession
            credentials={credentials}
            choices={choices}
            onDisconnected={disconnect}
            onError={fail}
            onFinish={finish}
          />
        ) : null}
        {step === "ended" ? <TelemedicineEndedState /> : null}
        {step === "error" ? <TelemedicineErrorState message={error} /> : null}
      </section>
    </main>
  );
}
