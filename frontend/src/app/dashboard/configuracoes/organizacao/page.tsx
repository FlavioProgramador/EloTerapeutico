"use client";

import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";

import { useOrganization } from "@/contexts/organization";
import { OrganizationSettingsLayout } from "@/features/organizations/components/settings-layout";
import { api } from "@/lib/api";

export default function OrganizationSettingsPage() {
  const {
    activeOrganization,
    activeMembership,
    refreshOrganizations,
  } = useOrganization();
  const [form, setForm] = useState({
    name: "",
    legal_name: "",
    organization_type: "individual",
    document: "",
    email: "",
    phone: "",
    timezone: "America/Sao_Paulo",
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!activeOrganization) return;
    setForm({
      name: activeOrganization.name,
      legal_name: activeOrganization.legal_name,
      organization_type: activeOrganization.organization_type,
      document: activeOrganization.document,
      email: activeOrganization.email,
      phone: activeOrganization.phone,
      timezone: activeOrganization.timezone,
    });
  }, [activeOrganization]);

  const canEdit = ["owner", "admin"].includes(activeMembership?.role || "");

  return (
    <OrganizationSettingsLayout
      title="Organização"
      description="Dados institucionais do consultório, clínica ou empresa ativa."
    >
      {!activeOrganization ? (
        <p className="text-sm text-muted-foreground">Nenhuma organização ativa.</p>
      ) : (
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!canEdit) return;
            setSaving(true);
            setMessage("");
            try {
              await api.patch(
                `organizations/${activeOrganization.id}/`,
                form,
              );
              await refreshOrganizations();
              setMessage("Dados da organização atualizados.");
            } catch {
              setMessage("Não foi possível atualizar a organização.");
            } finally {
              setSaving(false);
            }
          }}
        >
          {[
            ["name", "Nome"],
            ["legal_name", "Nome legal"],
            ["document", "CPF ou CNPJ"],
            ["email", "E-mail"],
            ["phone", "Telefone"],
            ["timezone", "Fuso horário"],
          ].map(([name, label]) => (
            <label key={name} className="space-y-1.5 text-xs font-medium">
              <span>{label}</span>
              <input
                value={form[name as keyof typeof form]}
                disabled={!canEdit}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    [name]: event.target.value,
                  }))
                }
                className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm disabled:opacity-60"
              />
            </label>
          ))}
          <label className="space-y-1.5 text-xs font-medium">
            <span>Tipo</span>
            <select
              value={form.organization_type}
              disabled={!canEdit}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  organization_type: event.target.value,
                }))
              }
              className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm disabled:opacity-60"
            >
              <option value="individual">Profissional individual</option>
              <option value="clinic">Clínica</option>
              <option value="company">Empresa</option>
            </select>
          </label>
          <div className="flex items-center gap-3 md:col-span-2">
            {canEdit ? (
              <button
                type="submit"
                disabled={saving || !form.name.trim()}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-60"
              >
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Salvar alterações
              </button>
            ) : (
              <p className="text-xs text-muted-foreground">
                Seu papel permite somente visualizar estes dados.
              </p>
            )}
            {message ? <p className="text-xs text-muted-foreground">{message}</p> : null}
          </div>
        </form>
      )}
    </OrganizationSettingsLayout>
  );
}
