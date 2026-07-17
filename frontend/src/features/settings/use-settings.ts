import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { settingsService } from "./settings.service";
import type { PracticeSettings, SettingsProfile, WorkingHour } from "./types";

export const settingsKeys = {
  profile: ["settings", "profile"] as const,
  practice: ["settings", "practice"] as const,
  workingHours: ["settings", "working-hours"] as const,
  sessions: ["settings", "sessions"] as const,
};

export function useSettingsProfile() {
  return useQuery({ queryKey: settingsKeys.profile, queryFn: settingsService.profile });
}
export function usePracticeSettings() {
  return useQuery({ queryKey: settingsKeys.practice, queryFn: settingsService.practice });
}
export function useWorkingHours() {
  return useQuery({ queryKey: settingsKeys.workingHours, queryFn: settingsService.workingHours });
}
export function useAuthSessions() {
  return useQuery({ queryKey: settingsKeys.sessions, queryFn: settingsService.sessions });
}
export function useUpdateSettingsProfile() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<SettingsProfile>) => settingsService.updateProfile(payload),
    onSuccess: (data) => client.setQueryData(settingsKeys.profile, data),
  });
}
export function useUpdatePracticeSettings() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<PracticeSettings>) => settingsService.updatePractice(payload),
    onSuccess: (data) => client.setQueryData(settingsKeys.practice, data),
  });
}
export function useSaveWorkingHours() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (items: Array<Omit<WorkingHour, "weekday_display">>) =>
      Promise.all(items.map((item) => settingsService.saveWorkingHour(item))),
    onSuccess: () => client.invalidateQueries({ queryKey: settingsKeys.workingHours }),
  });
}
export function useRevokeSession() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: settingsService.revokeSession,
    onSuccess: () => client.invalidateQueries({ queryKey: settingsKeys.sessions }),
  });
}
