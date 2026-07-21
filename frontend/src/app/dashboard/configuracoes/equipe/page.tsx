"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, MailPlus, Trash2 } from "lucide-react";

import { useOrganization } from "@/contexts/organization";
import { OrganizationSettingsLayout } from "@/features/organizations/components/settings-layout";
import {
  membershipRoleLabels,
  type MembershipRole,
  type OrganizationMembership,
} from "@/features/organizations/types";
import { api } from "@/lib/api";

interface Invitation {
  id: string;
  email: string;
  role: MembershipRole;
  status: string;
}

const roles: MembershipRole[] = [
  "admin",
  "therapist",
  "receptionist",
  "finance",
  "viewer",
];

export default function OrganizationTeamPage() {
  const { activeOrganization, activeMembership } = useOrganization();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<MembershipRole>("therapist");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const canManage = ["owner", "admin"].includes(activeMembership?.role || "");

  const members = useQuery({
    queryKey: ["organization-members", activeOrganization?.id],
    queryFn: async () =>
      (
        await api.get<OrganizationMembership[]>(
          `organizations/${activeOrganization?.id}/members/`,
        )
      ).data,
    enabled: Boolean(activeOrganization && canManage),
  });

  const invitations = useQuery({
    queryKey: ["organization-invitations", activeOrganization?.id],
    queryFn: async () =>
      (
        await api.get<Invitation[]>(
          `organizations/${activeOrganization?.id}/invitations/`,
        )
      ).data,
    enabled: Boolean(activeOrganization && canManage),
  });

  const refresh = async () => {
    await Promise.all([members.refetch(), invitations.refetch()]);
  };

  return (
    <OrganizationSettingsLayout
      title="Equipe"
      description="Convide profissionais e controle papéis dentro da organização ativa."
    >
      {!canManage ? (
        <p className="text-sm text-muted-foreground">
          Apenas proprietários e administradores podem gerenciar a equipe.
        </p>
      ) : (
        <div className="space-y-8">
          <form
            className="grid gap-3 rounded-xl border border-border bg-background p-4 md:grid-cols-[1fr_180px_auto]"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!activeOrganization || !email.trim()) return;
              setSaving(true);
              setMessage("");
              try {
                await api.post(
                  `organizations/${activeOrganization.id}/invitations/`,
                  { email: email.trim(), role },
                );
                setEmail("");
                setMessage("Convite criado e colocado na fila de envio.");
                await refresh();
              } catch {
                setMessage("Não foi possível criar o convite.");
              } finally {
                setSaving(false);
              }
            }}
          >
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="profissional@exemplo.com"
              className="h-10 rounded-lg border border-border bg-card px-3 text-sm"
            />
            <select
              value={role}
              onChange={(event) => setRole(event.target.value as MembershipRole)}
              className="h-10 rounded-lg border border-border bg-card px-3 text-sm"
            >
              {roles.map((item) => (
                <option key={item} value={item}>
                  {membershipRoleLabels[item]}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={saving}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground disabled:opacity-60"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <MailPlus className="h-4 w-4" />
              )}
              Convidar
            </button>
            {message ? (
              <p className="text-xs text-muted-foreground md:col-span-3">
                {message}
              </p>
            ) : null}
          </form>

          <div>
            <h2 className="mb-3 text-sm font-semibold">Membros</h2>
            <div className="overflow-hidden rounded-xl border border-border">
              {(members.data ?? []).map((member) => (
                <div
                  key={member.id}
                  className="grid items-center gap-3 border-b border-border p-4 last:border-b-0 md:grid-cols-[1fr_180px_44px]"
                >
                  <div>
                    <p className="text-sm font-medium">{member.user_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {member.user_email}
                    </p>
                  </div>
                  <select
                    value={member.role}
                    disabled={
                      member.role === "owner" ||
                      member.id === activeMembership?.id
                    }
                    onChange={async (event) => {
                      if (!activeOrganization) return;
                      await api.patch(
                        `organizations/${activeOrganization.id}/members/${member.id}/`,
                        { role: event.target.value },
                      );
                      await refresh();
                    }}
                    className="h-9 rounded-lg border border-border bg-background px-2 text-xs disabled:opacity-60"
                  >
                    {member.role === "owner" ? (
                      <option value="owner">Proprietário</option>
                    ) : null}
                    {roles.map((item) => (
                      <option key={item} value={item}>
                        {membershipRoleLabels[item]}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    disabled={
                      member.role === "owner" ||
                      member.id === activeMembership?.id
                    }
                    onClick={async () => {
                      if (!activeOrganization) return;
                      await api.delete(
                        `organizations/${activeOrganization.id}/members/${member.id}/`,
                      );
                      await refresh();
                    }}
                    className="grid h-9 w-9 place-items-center rounded-lg text-destructive hover:bg-destructive/10 disabled:opacity-30"
                    aria-label={`Remover ${member.user_name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-sm font-semibold">Convites</h2>
            <div className="overflow-hidden rounded-xl border border-border">
              {(invitations.data ?? []).length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">
                  Nenhum convite pendente.
                </p>
              ) : (
                invitations.data?.map((invitation) => (
                  <div
                    key={invitation.id}
                    className="flex items-center justify-between border-b border-border p-4 last:border-b-0"
                  >
                    <div>
                      <p className="text-sm font-medium">{invitation.email}</p>
                      <p className="text-xs text-muted-foreground">
                        {membershipRoleLabels[invitation.role]} · {invitation.status}
                      </p>
                    </div>
                    {invitation.status === "pending" ? (
                      <button
                        type="button"
                        onClick={async () => {
                          if (!activeOrganization) return;
                          await api.post(
                            `organizations/${activeOrganization.id}/invitations/${invitation.id}/revoke/`,
                            {},
                          );
                          await refresh();
                        }}
                        className="rounded-lg border border-border px-3 py-2 text-xs"
                      >
                        Revogar
                      </button>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </OrganizationSettingsLayout>
  );
}
