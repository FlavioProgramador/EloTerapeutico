"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Save } from "lucide-react";

import { useOrganization } from "@/contexts/organization";
import { OrganizationSettingsLayout } from "@/features/organizations/components/settings-layout";
import { api } from "@/lib/api";

interface ProfessionalProfile {
  display_name: string;
  professional_title: string;
  council_type: string;
  council_number: string;
  council_region: string;
  specialties: string[];
  bio: string;
  phone: string;
  public_email: string;
  default_appointment_duration: number;
  default_session_value: string | number;
  accepts_online: boolean;
  accepts_in_person: boolean;
  is_public: boolean;
}

const emptyProfile: ProfessionalProfile = {
  display_name: "",
  professional_title: "",
  council_type: "",
  council_number: "",
  council_region: "",
  specialties: [],
  bio: "",
  phone: "",
  public_email: "",
  default_appointment_duration: 50,
  default_session_value: 0,
  accepts_online: true,
  accepts_in_person: true,
  is_public: false,
};

export default function ProfessionalProfilePage() {
  const { activeOrganization } = useOrganization();
  const [form, setForm] = useState(emptyProfile);
  const [specialties, setSpecialties] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const profile = useQuery({
    queryKey: ["professional-profile", activeOrganization?.id],
    queryFn: async () =>
      (
        await api.get<ProfessionalProfile>(
          `organizations/${activeOrganization?.id}/professional-profile/`,
        )
      ).data,
    enabled: Boolean(activeOrganization),
  });

  useEffect(() => {
    if (!profile.data) return;
    setForm(profile.data);
    setSpecialties(profile.data.specialties.join(", "));
  }, [profile.data]);

  const textFields: Array<[keyof ProfessionalProfile, string]> = [
    ["display_name", "Nome profissional"],
    ["professional_title", "Título profissional"],
    ["council_type", "Conselho"],
    ["council_number", "Número do conselho"],
    ["council_region", "UF ou região"],
    ["public_email", "E-mail público"],
    ["phone", "Telefone profissional"],
  ];

  return (
    <OrganizationSettingsLayout
      title="Perfil profissional"
      description="Informações profissionais específicas da organização ativa."
    >
      {profile.isLoading ? (
        <Loader2 className="h-5 w-5 animate-spin text-primary" />
      ) : (
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!activeOrganization) return;
            setSaving(true);
            setMessage("");
            try {
              await api.patch(
                `organizations/${activeOrganization.id}/professional-profile/`,
                {
                  ...form,
                  specialties: specialties
                    .split(",")
                    .map((item) => item.trim())
                    .filter(Boolean),
                },
              );
              setMessage("Perfil profissional atualizado.");
              await profile.refetch();
            } catch {
              setMessage("Não foi possível atualizar o perfil.");
            } finally {
              setSaving(false);
            }
          }}
        >
          {textFields.map(([name, label]) => (
            <label key={name} className="space-y-1.5 text-xs font-medium">
              <span>{label}</span>
              <input
                value={String(form[name] ?? "")}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    [name]: event.target.value,
                  }))
                }
                className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
              />
            </label>
          ))}
          <label className="space-y-1.5 text-xs font-medium md:col-span-2">
            <span>Especialidades separadas por vírgula</span>
            <input
              value={specialties}
              onChange={(event) => setSpecialties(event.target.value)}
              className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
            />
          </label>
          <label className="space-y-1.5 text-xs font-medium md:col-span-2">
            <span>Apresentação</span>
            <textarea
              rows={5}
              value={form.bio}
              onChange={(event) =>
                setForm((current) => ({ ...current, bio: event.target.value }))
              }
              className="w-full rounded-lg border border-border bg-background p-3 text-sm"
            />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border p-3 text-sm">
            Atendimento presencial
            <input
              type="checkbox"
              checked={form.accepts_in_person}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  accepts_in_person: event.target.checked,
                }))
              }
              className="h-4 w-4 accent-primary"
            />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border p-3 text-sm">
            Atendimento online
            <input
              type="checkbox"
              checked={form.accepts_online}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  accepts_online: event.target.checked,
                }))
              }
              className="h-4 w-4 accent-primary"
            />
          </label>
          <div className="flex items-center gap-3 md:col-span-2">
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
              Salvar perfil
            </button>
            {message ? <p className="text-xs text-muted-foreground">{message}</p> : null}
          </div>
        </form>
      )}
    </OrganizationSettingsLayout>
  );
}
