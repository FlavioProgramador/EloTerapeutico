"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Save } from "lucide-react";

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
      description="Agenda, lembretes, portal e identificação dos documentos."
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
              await api.patch(
                `organizations/${activeOrganization.id}/settings/`,
                { ...form, allow_telemedicine: false },
              );
              setMessage("Configurações de atendimento atualizadas.");
              await settings.refetch();
            } catch {
              setMessage("Não foi possível atualizar as configurações.");
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
          <div className="rounded-xl border border-dashed border-border p-4 text-sm md:col-span-2">
            <p className="font-medium">Telemedicina</p>
            <p className="mt-1 text-xs text-muted-foreground">
              A configuração ficará disponível quando o provedor de vídeo estiver integrado. Nenhuma sala é anunciada como funcional antes disso.
            </p>
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
