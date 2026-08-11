"use client";

import { useEffect, useState, useId } from "react";
import { Loader2, Save } from "lucide-react";

import { useOrganization } from "@/contexts/organization";
import { OrganizationSettingsLayout } from "@/features/organizations/components/settings-layout";
import { api } from "@/lib/api";

export default function OrganizationSettingsPage() {
  const baseId = useId();
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

  const textFields = [
    ["name", "Nome"],
    ["legal_name", "Nome legal"],
    ["document", "CPF ou CNPJ"],
    ["email", "E-mail"],
    ["phone", "Telefone"],
    ["timezone", "Fuso horário"],
  ] as const;

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
          {textFields.map(([name, label]) => {
            const inputId = `${baseId}-${name}`;
            return (
              <div key={name} className="flex flex-col gap-1.5">
                <label htmlFor={inputId} className="text-xs font-semibold text-foreground">
                  {label}
                </label>
                <input
                  id={inputId}
                  value={form[name as keyof typeof form]}
                  disabled={!canEdit}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      [name]: event.target.value,
                    }))
                  }
                  className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-60"
                />
              </div>
            );
          })}
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${baseId}-organization_type`} className="text-xs font-semibold text-foreground">
              Tipo
            </label>
            <select
              id={`${baseId}-organization_type`}
              value={form.organization_type}
              disabled={!canEdit}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  organization_type: event.target.value,
                }))
              }
              className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-60"
            >
              <option value="individual">Profissional individual</option>
              <option value="clinic">Clínica</option>
              <option value="company">Empresa</option>
            </select>
          </div>
          <div className="flex items-center gap-3 md:col-span-2">
            {canEdit ? (
              <button
                type="submit"
                disabled={saving || !form.name.trim()}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-60"
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
