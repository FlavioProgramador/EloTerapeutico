"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CalendarDays, Clock3, Loader2, ShieldCheck, Video } from "lucide-react";

import { telemedicinePublicService } from "../services/telemedicine.service";
import type {
  TelemedicineCredentials,
  TelemedicineDeviceChoices,
  TelemedicinePublicContext,
} from "../types";
import { TelemedicineConsent } from "./telemedicine-consent";
import {
  TelemedicineEndedState,
  TelemedicineErrorState,
} from "./telemedicine-error-state";
import { TelemedicinePreJoin } from "./telemedicine-prejoin";
import { TelemedicineSession } from "./telemedicine-session";

type Step = "loading" | "consent" | "prejoin" | "session" | "ended" | "error";

export function PatientTelemedicineFlow() {
  const tokenRef = useRef("");
  const [step, setStep] = useState<Step>("loading");
  const [context, setContext] = useState<TelemedicinePublicContext>();
  const [credentials, setCredentials] = useState<TelemedicineCredentials>();
  const [choices, setChoices] = useState<TelemedicineDeviceChoices>();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fail = useCallback((message: string) => {
    setCredentials(undefined);
    setChoices(undefined);
    setError(message);
    setStep("error");
  }, []);

  useEffect(() => {
    let active = true;
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const rawToken = fragment.get("token")?.trim() || "";
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${window.location.search}`,
    );

    if (!rawToken) {
      fail("O convite é inválido ou não está mais disponível.");
      return () => {
        active = false;
      };
    }

    tokenRef.current = rawToken;
    telemedicinePublicService
      .exchange(rawToken)
      .then((data) => {
        if (!active) return;
        setContext(data);
        setStep(data.consent_accepted ? "prejoin" : "consent");
      })
      .catch((reason: unknown) => {
        if (!active) return;
        fail(
          reason instanceof Error
            ? reason.message
            : "O acesso é inválido ou expirou.",
        );
      });

    return () => {
      active = false;
      tokenRef.current = "";
    };
  }, [fail]);

  const handleConsent = useCallback(async (guardianName: string) => {
    setSubmitting(true);
    try {
      await telemedicinePublicService.consent(tokenRef.current, {
        accepted: true,
        responsible_guardian_name: guardianName,
      });
      setContext((current) =>
        current ? { ...current, consent_accepted: true } : current,
      );
      setStep("prejoin");
    } catch (reason: unknown) {
      fail(reason instanceof Error ? reason.message : "Não foi possível registrar o consentimento.");
    } finally {
      setSubmitting(false);
    }
  }, [fail]);

  const handleJoin = useCallback(async (deviceChoices: TelemedicineDeviceChoices) => {
    setSubmitting(true);
    try {
      const issued = await telemedicinePublicService.join(tokenRef.current);
      setChoices(deviceChoices);
      setCredentials(issued);
      setStep("session");
    } catch (reason: unknown) {
      fail(reason instanceof Error ? reason.message : "Não foi possível entrar no atendimento.");
    } finally {
      setSubmitting(false);
    }
  }, [fail]);

  const handleDisconnected = useCallback(() => {
    const currentCredentials = credentials;
    const rawToken = tokenRef.current;
    if (currentCredentials && rawToken) {
      void telemedicinePublicService
        .leave(rawToken, currentCredentials.identity)
        .catch(() => undefined);
    }
    setCredentials(undefined);
    setChoices(undefined);
    tokenRef.current = "";
    setStep("ended");
  }, [credentials]);

  return (
    <main className="grid min-h-screen place-items-center bg-background p-4 sm:p-6">
      <section className="w-full max-w-5xl rounded-2xl border border-border bg-card p-5 shadow-xl sm:p-7">
        <header className="mb-6 flex flex-wrap items-center gap-3 border-b border-border pb-5">
          <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
            <Video className="size-5" />
          </span>
          <div>
            <h1 className="text-xl font-bold">Sala de atendimento online</h1>
            <p className="text-sm text-muted-foreground">
              Acesso individual, temporário e protegido
            </p>
          </div>
          <span className="ml-auto inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-700">
            <ShieldCheck className="size-3.5" />
            Sem gravação
          </span>
        </header>

        {context && step !== "session" ? <AppointmentSummary context={context} /> : null}

        {step === "loading" ? (
          <div className="grid min-h-72 place-items-center text-center">
            <div>
              <Loader2 className="mx-auto size-7 animate-spin text-primary" />
              <p className="mt-3 text-sm text-muted-foreground">Validando acesso...</p>
            </div>
          </div>
        ) : null}
        {step === "consent" && context ? (
          <TelemedicineConsent
            context={context}
            submitting={submitting}
            onAccept={handleConsent}
          />
        ) : null}
        {step === "prejoin" ? (
          <TelemedicinePreJoin
            role="patient"
            joining={submitting}
            onJoin={handleJoin}
            onError={fail}
          />
        ) : null}
        {step === "session" && credentials && choices ? (
          <TelemedicineSession
            credentials={credentials}
            choices={choices}
            onDisconnected={handleDisconnected}
            onError={fail}
          />
        ) : null}
        {step === "ended" ? <TelemedicineEndedState /> : null}
        {step === "error" ? <TelemedicineErrorState message={error} /> : null}
      </section>
    </main>
  );
}

function AppointmentSummary({ context }: { context: TelemedicinePublicContext }) {
  const start = new Date(context.appointment_start);
  const end = new Date(context.appointment_end);
  return (
    <div className="mb-6 grid gap-3 rounded-xl border border-border bg-secondary/20 p-4 sm:grid-cols-3">
      <div>
        <span className="text-xs text-muted-foreground">Profissional</span>
        <strong className="mt-1 block text-sm">{context.therapist_name}</strong>
        <span className="text-xs text-muted-foreground">{context.organization_name}</span>
      </div>
      <div className="flex items-start gap-2">
        <CalendarDays className="mt-0.5 size-4 text-primary" />
        <div>
          <span className="text-xs text-muted-foreground">Data</span>
          <strong className="mt-1 block text-sm">{start.toLocaleDateString("pt-BR")}</strong>
        </div>
      </div>
      <div className="flex items-start gap-2">
        <Clock3 className="mt-0.5 size-4 text-primary" />
        <div>
          <span className="text-xs text-muted-foreground">Horário</span>
          <strong className="mt-1 block text-sm">
            {start.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
            {" – "}
            {end.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
          </strong>
        </div>
      </div>
    </div>
  );
}
