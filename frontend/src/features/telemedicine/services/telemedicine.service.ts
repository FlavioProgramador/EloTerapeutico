import { api } from "@/lib/api";

import type {
  TelemedicineCredentials,
  TelemedicineDashboardRoom,
  TelemedicinePublicContext,
} from "../types";

const PUBLIC_BASE = "/api/backend/scheduling/telemedicine/public";

async function publicPost<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${PUBLIC_BASE}/${path}/`, {
    method: "POST",
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = (await response.json().catch(() => ({}))) as {
    detail?: unknown;
  };
  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "O atendimento online está temporariamente indisponível.",
    );
  }
  return data as T;
}

export const telemedicinePublicService = {
  exchange: (token: string) =>
    publicPost<TelemedicinePublicContext>("exchange", { token }),
  consent: (
    token: string,
    payload: { accepted: boolean; responsible_guardian_name?: string },
  ) => publicPost<{ accepted: true; document_version: string; accepted_at: string }>(
    "consent",
    { token, ...payload },
  ),
  join: (token: string) =>
    publicPost<TelemedicineCredentials>("join", { token }),
  leave: (token: string, identity: string) =>
    publicPost<void>("leave", { token, identity }),
};

export const telemedicineProfessionalService = {
  join: async (roomId: number) =>
    (
      await api.post<TelemedicineCredentials>(
        `scheduling/telemedicine/${roomId}/join-professional/`,
        {},
      )
    ).data,
  createInvitation: async (roomId: number) =>
    (
      await api.post<{ invitation_url: string; expires_at: string }>(
        `scheduling/telemedicine/${roomId}/create-invitation/`,
        {},
      )
    ).data,
  revokeInvitation: async (roomId: number) =>
    (
      await api.post<{ revoked: boolean }>(
        `scheduling/telemedicine/${roomId}/revoke-invitation/`,
        {},
      )
    ).data,
  finish: async (roomId: number) =>
    (
      await api.post<TelemedicineDashboardRoom>(
        `scheduling/telemedicine/${roomId}/finish/`,
        {},
      )
    ).data,
};
