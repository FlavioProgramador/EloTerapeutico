import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { communicationsService } from "./communications.service";
import type {
  CreateCommunicationPayload,
  NotificationPreference,
  UpdateChannelConfigurationPayload,
} from "./types";

export function useCommunicationDashboard(period: string) {
  return useQuery({
    queryKey: ["communications-dashboard", period],
    queryFn: () => communicationsService.dashboard(period),
  });
}
export function useCommunications(
  filters?: Record<string, string | number | undefined>,
) {
  return useQuery({
    queryKey: ["communications", filters],
    queryFn: () => communicationsService.list(filters),
  });
}
export function useCommunication(id: string | null) {
  return useQuery({
    queryKey: ["communication", id],
    queryFn: () => communicationsService.detail(id!),
    enabled: Boolean(id),
  });
}
export function useCommunicationTemplates() {
  return useQuery({
    queryKey: ["communication-templates"],
    queryFn: () => communicationsService.templates(),
  });
}
export function useCommunicationAutomations() {
  return useQuery({
    queryKey: ["communication-automations"],
    queryFn: communicationsService.automations,
  });
}
export function useCommunicationChannels() {
  return useQuery({
    queryKey: ["communication-channels"],
    queryFn: communicationsService.channels,
  });
}
export function useCommunicationPatients() {
  return useQuery({
    queryKey: ["communication-patients"],
    queryFn: communicationsService.patients,
  });
}
export function useCreateCommunication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateCommunicationPayload) =>
      communicationsService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["communications"] });
      queryClient.invalidateQueries({ queryKey: ["communications-dashboard"] });
    },
  });
}
export function useCommunicationAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: string;
      action:
        | "cancel"
        | "retry"
        | "send"
        | "mark-manually-sent"
        | "open-manual";
    }) => communicationsService.action(id, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["communications"] });
      queryClient.invalidateQueries({ queryKey: ["communication"] });
      queryClient.invalidateQueries({ queryKey: ["communications-dashboard"] });
    },
  });
}
export function useToggleCommunicationAutomation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      communicationsService.toggleAutomation(id, active),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["communication-automations"],
      }),
  });
}

function useChannelMutation<TInput, TOutput>(
  mutationFn: (input: TInput) => Promise<TOutput>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["communication-channels"] }),
  });
}
export function useUpdateCommunicationChannel() {
  return useChannelMutation(
    ({
      channel,
      payload,
    }: {
      channel: string;
      payload: UpdateChannelConfigurationPayload;
    }) => communicationsService.updateChannel(channel, payload),
  );
}
export function useTestCommunicationChannelConnection() {
  return useChannelMutation((channel: string) =>
    communicationsService.testChannelConnection(channel),
  );
}
export function useSendCommunicationChannelTest() {
  return useChannelMutation(
    ({ channel, destination }: { channel: string; destination?: string }) =>
      communicationsService.sendChannelTest(channel, destination),
  );
}
export function useToggleCommunicationChannel() {
  return useChannelMutation(
    ({ channel, active }: { channel: string; active: boolean }) =>
      communicationsService.toggleChannel(channel, active),
  );
}
export function useRemoveCommunicationChannel() {
  return useChannelMutation((channel: string) =>
    communicationsService.removeChannel(channel),
  );
}

export function useNotifications(
  filters?: Record<string, string | number | boolean | undefined>,
  enabled = true,
) {
  return useQuery({
    queryKey: ["communication-notifications", filters],
    queryFn: () => communicationsService.notifications(filters),
    refetchInterval: enabled ? 60_000 : false,
    refetchOnWindowFocus: true,
    enabled,
  });
}
export function useUnreadNotificationsCount() {
  return useQuery({
    queryKey: ["communication-notifications-unread"],
    queryFn: communicationsService.unreadCount,
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
function useNotificationMutation<TInput, TOutput>(
  mutationFn: (input: TInput) => Promise<TOutput>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["communication-notifications"] });
      queryClient.invalidateQueries({ queryKey: ["communication-notifications-unread"] });
    },
  });
}
export function useMarkNotificationRead() {
  return useNotificationMutation(communicationsService.markNotificationRead);
}
export function useMarkNotificationUnread() {
  return useNotificationMutation(communicationsService.markNotificationUnread);
}
export function useArchiveNotification() {
  return useNotificationMutation(communicationsService.archiveNotification);
}
export function useReadAllNotifications() {
  return useNotificationMutation(() => communicationsService.readAllNotifications());
}
export function useArchiveReadNotifications() {
  return useNotificationMutation(() => communicationsService.archiveReadNotifications());
}
export function useNotificationCategories() {
  return useQuery({
    queryKey: ["communication-notification-categories"],
    queryFn: communicationsService.notificationCategories,
    staleTime: 60 * 60 * 1000,
  });
}
export function useNotificationPreferences() {
  return useQuery({
    queryKey: ["communication-notification-preferences"],
    queryFn: communicationsService.notificationPreferences,
  });
}
export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<NotificationPreference>) =>
      communicationsService.updateNotificationPreferences(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(["communication-notification-preferences"], data);
      queryClient.invalidateQueries({ queryKey: ["communication-notifications"] });
      queryClient.invalidateQueries({ queryKey: ["communication-notifications-unread"] });
    },
  });
}
