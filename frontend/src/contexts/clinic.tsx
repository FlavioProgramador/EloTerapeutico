"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/contexts/auth";
import { api } from "@/lib/api";

export interface ClinicSummary {
  public_id: string;
  name: string;
  email: string;
  phone: string;
  timezone: string;
  logo: string | null;
  status: "active" | "suspended" | "archived";
  created_at: string;
  updated_at: string;
}

export interface ClinicMembership {
  public_id: string;
  clinic: ClinicSummary;
  role:
    | "owner"
    | "admin"
    | "therapist"
    | "secretary"
    | "financial"
    | "support";
  role_display: string;
  status: "invited" | "active" | "suspended" | "revoked";
  extra_permissions: string[];
  joined_at: string | null;
  is_current: boolean;
}

interface ClinicContextPayload {
  active_membership: ClinicMembership | null;
  memberships: ClinicMembership[];
  requires_setup: boolean;
}

interface ClinicContextValue extends ClinicContextPayload {
  isLoading: boolean;
  error: string | null;
  refreshClinics: () => Promise<void>;
  switchClinic: (clinicId: string) => Promise<void>;
}

const EMPTY_CONTEXT: ClinicContextPayload = {
  active_membership: null,
  memberships: [],
  requires_setup: false,
};

const ClinicContext = createContext<ClinicContextValue | undefined>(undefined);

export function ClinicProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [payload, setPayload] = useState<ClinicContextPayload>(EMPTY_CONTEXT);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshClinics = useCallback(async () => {
    if (!isAuthenticated) {
      setPayload(EMPTY_CONTEXT);
      setError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<ClinicContextPayload>("auth/clinics/");
      setPayload(response.data);
    } catch {
      setPayload(EMPTY_CONTEXT);
      setError("Não foi possível carregar o contexto da clínica.");
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (authLoading) return;
    void refreshClinics();
  }, [authLoading, refreshClinics]);

  const switchClinic = useCallback(
    async (clinicId: string) => {
      setError(null);
      const response = await api.post<{
        active_membership: ClinicMembership;
      }>("auth/clinics/switch/", { clinic_id: clinicId });
      const activeMembership = response.data.active_membership;

      setPayload((current) => ({
        ...current,
        active_membership: activeMembership,
        requires_setup: false,
        memberships: current.memberships.map((membership) => ({
          ...membership,
          is_current: membership.clinic.public_id === clinicId,
        })),
      }));

      queryClient.clear();
      router.refresh();
    },
    [queryClient, router],
  );

  const value = useMemo<ClinicContextValue>(
    () => ({
      ...payload,
      isLoading: authLoading || isLoading,
      error,
      refreshClinics,
      switchClinic,
    }),
    [authLoading, error, isLoading, payload, refreshClinics, switchClinic],
  );

  return (
    <ClinicContext.Provider value={value}>{children}</ClinicContext.Provider>
  );
}

export function useClinic(): ClinicContextValue {
  const context = useContext(ClinicContext);
  if (!context) {
    throw new Error("useClinic deve ser usado dentro de ClinicProvider");
  }
  return context;
}
