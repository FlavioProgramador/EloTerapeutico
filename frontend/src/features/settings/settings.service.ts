import { api } from "@/lib/api";
import type {
  AuthSessionItem,
  PracticeSettings,
  SettingsProfile,
  WorkingHour,
} from "./types";

export const settingsService = {
  async profile() {
    const { data } = await api.get<SettingsProfile>("auth/me/");
    return data;
  },
  async updateProfile(payload: Partial<SettingsProfile>) {
    const { data } = await api.patch<SettingsProfile>("auth/me/", payload);
    return data;
  },
  async practice() {
    const { data } = await api.get<PracticeSettings>("auth/settings/");
    return data;
  },
  async updatePractice(payload: Partial<PracticeSettings>) {
    const { data } = await api.patch<PracticeSettings>("auth/settings/", payload);
    return data;
  },
  async workingHours() {
    const { data } = await api.get<WorkingHour[] | { results: WorkingHour[] }>(
      "auth/working-hours/",
    );
    return Array.isArray(data) ? data : data.results;
  },
  async saveWorkingHour(input: Omit<WorkingHour, "id" | "weekday_display"> & { id?: number }) {
    const payload = {
      weekday: input.weekday,
      start_time: input.start_time,
      end_time: input.end_time,
      is_active: input.is_active,
    };
    if (input.id) {
      const { data } = await api.patch<WorkingHour>(
        `auth/working-hours/${input.id}/`,
        payload,
      );
      return data;
    }
    const { data } = await api.post<WorkingHour>("auth/working-hours/", payload);
    return data;
  },
  async sessions() {
    const { data } = await api.get<AuthSessionItem[]>("auth/sessions/");
    return data;
  },
  async revokeSession(publicId: string) {
    await api.post(`auth/sessions/${publicId}/revoke/`, {});
  },
  async changePassword(payload: {
    current_password: string;
    new_password: string;
    new_password_confirm: string;
  }) {
    const { data } = await api.post<{ message: string }>(
      "auth/password/change/",
      payload,
    );
    return data;
  },
};
