"use client";

import { Building2, ChevronDown, Loader2 } from "lucide-react";
import { useState } from "react";

import { useOrganization } from "@/contexts/organization";

export function OrganizationSwitcher() {
  const {
    activeOrganization,
    organizations,
    isLoading,
    isSwitching,
    switchOrganization,
  } = useOrganization();
  const [error, setError] = useState("");

  if (isLoading) {
    return (
      <div className="hidden h-9 items-center gap-2 rounded-lg border border-border px-3 text-xs text-muted-foreground md:flex">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Carregando organização
      </div>
    );
  }

  if (!activeOrganization) return null;

  if (organizations.length <= 1) {
    return (
      <div className="hidden max-w-56 items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 md:flex">
        <Building2 className="h-4 w-4 shrink-0 text-primary" />
        <span className="truncate text-xs font-medium text-foreground">
          {activeOrganization.name}
        </span>
      </div>
    );
  }

  return (
    <div className="relative hidden md:block">
      <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-primary" />
      <select
        value={activeOrganization.id}
        disabled={isSwitching}
        aria-label="Organização ativa"
        onChange={async (event) => {
          setError("");
          try {
            await switchOrganization(event.target.value);
          } catch {
            setError("Não foi possível trocar de organização.");
          }
        }}
        className="h-9 max-w-64 appearance-none rounded-lg border border-border bg-card pl-9 pr-9 text-xs font-medium text-foreground outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/10 disabled:opacity-60"
      >
        {organizations.map((organization) => (
          <option
            key={organization.id}
            value={organization.id}
            disabled={organization.status !== "active"}
          >
            {organization.name}
          </option>
        ))}
      </select>
      {isSwitching ? (
        <Loader2 className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 animate-spin text-muted-foreground" />
      ) : (
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
      )}
      {error ? (
        <p className="absolute left-0 top-10 whitespace-nowrap text-[10px] text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}
