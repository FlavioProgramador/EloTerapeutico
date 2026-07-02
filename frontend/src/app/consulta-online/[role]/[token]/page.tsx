"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CalendarDays, Clock3, ShieldCheck, Video } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface RoomAccess {
  appointment_start: string;
  appointment_end: string;
  patient_name: string;
  therapist_name: string;
  status: string;
  role: "patient" | "professional";
  expires_at: string;
}

export default function OnlineConsultationPage() {
  const params = useParams<{ role: string; token: string }>();
  const [data, setData] = useState<RoomAccess>();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    api
      .get<RoomAccess>(
        `agenda/telemedicine-access/${params.role}/${params.token}/`,
      )
      .then((response) => {
        if (active) setData(response.data);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        const message =
          reason &&
          typeof reason === "object" &&
          "response" in reason &&
          typeof (reason as { response?: { data?: { detail?: unknown } } }).response
            ?.data?.detail === "string"
            ? String(
                (reason as { response?: { data?: { detail?: string } } }).response
                  ?.data?.detail,
              )
            : "A sala não está disponível.";
        setError(message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [params.role, params.token]);

  return (
    <main className="grid min-h-screen place-items-center bg-background p-6">
      <section className="w-full max-w-xl rounded-2xl border border-border bg-card p-6 shadow-xl">
        <div className="flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
            <Video className="size-5" />
          </span>
          <div>
            <h1 className="text-xl font-bold">Sala de atendimento online</h1>
            <p className="text-sm text-muted-foreground">
              Acesso protegido e temporário
            </p>
          </div>
        </div>

        {loading && (
          <p className="py-12 text-center text-sm text-muted-foreground">
            Validando acesso...
          </p>
        )}
        {error && (
          <div className="my-6 rounded-xl border border-destructive/25 bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        )}
        {data && (
          <div className="mt-6 space-y-5">
            <div className="rounded-xl border border-border bg-secondary/20 p-4">
              <strong className="block text-lg">{data.patient_name}</strong>
              <span className="text-sm text-muted-foreground">
                Profissional: {data.therapist_name}
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Info
                icon={<CalendarDays className="size-4" />}
                label="Data"
                value={new Date(data.appointment_start).toLocaleDateString(
                  "pt-BR",
                )}
              />
              <Info
                icon={<Clock3 className="size-4" />}
                label="Horário"
                value={`${new Date(data.appointment_start).toLocaleTimeString(
                  "pt-BR",
                  { hour: "2-digit", minute: "2-digit" },
                )}–${new Date(data.appointment_end).toLocaleTimeString("pt-BR", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}`}
              />
            </div>
            <div className="flex items-start gap-2 rounded-xl border border-primary/20 bg-primary/5 p-4 text-xs text-muted-foreground">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
              O link é individual, revogável e expira após o atendimento. Não
              compartilhe com terceiros.
            </div>
            <Button
              className="w-full"
              size="lg"
              leftIcon={<Video className="size-5" />}
              disabled={
                data.status === "cancelled" || data.status === "expired"
              }
            >
              Entrar na consulta
            </Button>
          </div>
        )}
      </section>
    </main>
  );
}

function Info({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-border p-4">
      <span className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
        {icon}
        {label}
      </span>
      <strong className="mt-2 block text-sm">{value}</strong>
    </div>
  );
}
