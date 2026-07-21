"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/contexts/auth";
import { api } from "@/lib/api";
import {
  getStoredOrganizationId,
  storeOrganizationId,
} from "@/features/organizations/storage";
import type {
  Organization,
  OrganizationContextPayload,
  OrganizationMembership,
} from "@/features/organizations/types";

const ORGANIZATION_CONTEXT_QUERY_KEY = ["organization-context"] as const;

interface OrganizationContextValue {
  activeOrganization: Organization | null;
  activeMembership: OrganizationMembership | null;
  organizations: Organization[];
  isLoading: boolean;
  isSwitching: boolean;
  switchOrganization: (organizationId: string) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
}

const OrganizationContext = createContext<OrganizationContextValue | null>(null);

async function loadOrganizationContext(): Promise<OrganizationContextPayload> {
  try {
    const { data } = await api.get<OrganizationContextPayload>(
      "organizations/context/",
    );
    return data;
  } catch (error) {
    if (!getStoredOrganizationId()) throw error;
    storeOrganizationId(null);
    const { data } = await api.get<OrganizationContextPayload>(
      "organizations/context/",
    );
    return data;
  }
}

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ORGANIZATION_CONTEXT_QUERY_KEY,
    queryFn: loadOrganizationContext,
    enabled: isAuthenticated,
    staleTime: 60_000,
    retry: false,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      storeOrganizationId(null);
      queryClient.removeQueries({ queryKey: ORGANIZATION_CONTEXT_QUERY_KEY });
      return;
    }
    const activeId = query.data?.active_organization?.id;
    if (activeId) storeOrganizationId(activeId);
  }, [isAuthenticated, query.data?.active_organization?.id, queryClient]);

  const switchOrganization = useCallback(
    async (organizationId: string) => {
      const target = query.data?.organizations.find(
        (organization) => organization.id === organizationId,
      );
      if (!target || target.status !== "active") {
        throw new Error("ORGANIZATION_NOT_AVAILABLE");
      }

      await queryClient.cancelQueries();
      await api.post(`organizations/${organizationId}/activate/`, {});
      storeOrganizationId(organizationId);
      queryClient.removeQueries({
        predicate: (candidate) =>
          candidate.queryKey[0] !== "auth-me" &&
          candidate.queryKey[0] !== ORGANIZATION_CONTEXT_QUERY_KEY[0],
      });
      await query.refetch();
    },
    [query, queryClient],
  );

  const refreshOrganizations = useCallback(async () => {
    await query.refetch();
  }, [query]);

  const value = useMemo<OrganizationContextValue>(
    () => ({
      activeOrganization: query.data?.active_organization ?? null,
      activeMembership: query.data?.active_membership ?? null,
      organizations: query.data?.organizations ?? [],
      isLoading: query.isLoading,
      isSwitching: query.isFetching && Boolean(query.data),
      switchOrganization,
      refreshOrganizations,
    }),
    [query.data, query.isFetching, query.isLoading, refreshOrganizations, switchOrganization],
  );

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization(): OrganizationContextValue {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error("useOrganization deve ser usado dentro de OrganizationProvider");
  }
  return context;
}
