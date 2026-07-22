"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Save, ShieldCheck, Video } from "lucide-react";

import { useOrganization } from "@/contexts/organization";
import { OrganizationSettingsLayout } from "@/features/organizations/components/settings-layout";
import { api } from "@/lib/api";

interface AttendanceSettings {
  default_timezone: string;
  default_currency: string;
  default_appointment_duration: number;
  minimum_booking_notice_minutes: number;
  maximum_booking_days: number;
  cancellation_notice_hours: number;
  allow_online_booking: boolean;
  allow_patient_portal: boolean;
  allow_telemedicine: boolean;
  telemedicine_available: boolean;
  telemedicine_unavailable_reason: string;
  send_appointment_reminders: boolean;
  reminder_hours_before: number;
  business_name_on_documents: string;
  document_header: string;
  document_footer: string;
}

const defaults: AttendanceSettings = {
  default_timezone: "America/Sao_Paulo",
  default_currency: "BRL",
  default_appointment_duration: 50,
  minimum_booking_notice_minutes: 0,
  maximum_booking_days: 90,
  cancellation_notice_hours: 24,
  allow_online_booking: false,
  allow_patient_portal: false,
  allow_telemedicine: false,
  telemedicine_available: false,
  telemedicine_unavailable_reason: "",
  send_appointment_reminders: true,
  reminder_hours_before: 24,
  business_name_on_documents: "",
  document_header: "",
  document_footer: "",
};

export default function AttendanceSettingsPage() {
  const { activeOrganization, activeMembership } = useOrganization();
  const [form, setForm] = useState(defaults);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const canEdit = ["owner", "admin"].includes(activeMembership?.role || "");

  const settings = useQuery({
    queryKey: ["organization-settings", activeOrganization?.id],
    queryFn: async () =>
      (
        await api.get<AttendanceSettings>(
          `organizations/${activeOrganization?.id}/settings/`,
        )
      ).data,
    enabled: Boolean(activeOrganization),
  });

  useEffect(() => {
    if (settings.data) setForm(settings.data);
  }, [settings.data]);

  const numbers: Array<[keyof AttendanceSettings, string]> = [
    ["default_appointment_duration", "Duração padrão da sessão (minutos)"],
    ["minimum_booking_notice_minutes", "Antecedência mínima (minutos)"],
    ["maximum_booking_days", "Janela máxima de agendamento (dias)"],
    ["cancellation_notice_hours", "Prazo para cancelamento (horas)"],
    ["reminder_hours_before", "Lembrete antes da consulta (horas)"],
  ];
  const toggles: Array<[keyof AttendanceSettings, string]> = [
    ["allow_online_booking", "Permitir agendamento online"],
    ["allow_patient_portal", "Habilitar portal do paciente"],
    ["send_appointment_reminders", "Enviar lembretes de consulta"],
  ];

  return (
    <OrganizationSettingsLayout
      title="Atendimento"
      description="Agenda, telemedicina, lembretes, portal e identificação dos documentos."
    >
      {settings.isLoading ? (
        <Loader2 className="h-5 w-5 animate-spin text-primary" />
      ) : (
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!activeOrganization || !canEdit) return;
            setSaving(true);
            setMessage("");
            try {
              const {
                telemedicine_available: _available,
                telemedicine_unavailable_reason: _reason,
                ...payload
              } = form;
              await api.patch(
                `organizations/${activeOrganization.id}/settings/`,
                payload,
              );
              setMessage("Configurações de atendimento atualizadas.");
              await settings.refetch();
            } catch (reason: unknown) {
              const detail =
                reason &&
                typeof reason === "object" &&
                "response" in reason &&
                typeof (reason as { response?: { data?: { allow_telemedicine?: unknown } } })
                  .response?.data?.allow_telemedicine === "string"
                  ? String(
                      (reason as { response?: { data?: { allow_telemedicine?: string } } })
                        .response?.data?.allow_telemedicine,
                    )
                  : "Não foi possível atualizar as configurações.";
              setMessage(detail);
            } finally {
              setSaving(false);
            }
          }}
        >
          {numbers.map(([name, label]) => (
            <label key={name} className="space-y-1.5 text-xs font-medium">
              <span>{label}</span>
              <input
                type="number"
                min={0}
                disabled={!canEdit}
                value={Number(form[name])}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    [name]: Number(event.target.value),
                  }))
                }
                className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm disabled:opacity-60"
              />
            </label>
          ))}
          {toggles.map(([name, label]) => (
            <label
              key={name}
              className="flex items-center justify-between rounded-lg border border-border p-3 text-sm"
            >
              {label}
              <input
                type="checkbox"
                disabled={!canEdit}
                checked={Boolean(form[name])}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    [name]: event.target.checked,
                  }))
                }
                className="h-4 w-4 accent-primary disabled:opacity-60"
              />
            </label>
          ))}

          <div className="rounded-xl border border-border p-4 md:col-span-2">
            <div className="flex items-start gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                <Video className="size-5" />
              </span>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium">Telemedicina</p>
                  {form.telemedicine_available ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-1 text-[11px] font-semibold text-emerald-700">
                      <ShieldCheck className="size-3" /> Disponível
                    </span>
                  ) : (
                    <span className="rounded-full bg-secondary px-2 py-1 text-[11px] font-semibold text-muted-foreground">
                      Indisponível
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Áudio e vídeo com acesso temporário, consentimento e criptografia ponta a ponta. As chamadas não são gravadas.
                </p>
                {!form.telemedicine_available && form.telemedicine_unavailable_reason ? (
                  <p className="mt-2 text-xs text-amber-700">
                    {form.telemedicine_unavailable_reason}
                  </p>
                ) : null}
              </div>
              <input
                type="checkbox"
                aria-label="Habilitar telemedicina"
                disabled={!canEdit || !form.telemedicine_available}
                checked={form.allow_telemedicine}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    allow_telemedicine: event.target.checked,
                  }))
                }
                className="mt-2 size-4 accent-primary disabled:opacity-50"
              />
            </div>
          </div>

          <label className="space-y-1.5 text-xs font-medium md:col-span-2">
            <span>Nome exibido nos documentos</span>
            <input
              disabled={!canEdit}
              value={form.business_name_on_documents}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  business_name_on_documents: event.target.value,
                }))
              }
              className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm disabled:opacity-60"
            />
          </label>
          <div className="flex items-center gap-3 md:col-span-2">
            {canEdit ? (
              <button
                type="submit"
                disabled={saving}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-60"
              >
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Salvar atendimento
              </button>
            ) : (
              <p className="text-xs text-muted-foreground">
                Seu papel permite somente visualizar estas configurações.
              </p>
            )}
            {message ? <p className="text-xs text-muted-foreground">{message}</p> : null}
          </div>
        </form>
      )}
    </OrganizationSettingsLayout>
  );
}
