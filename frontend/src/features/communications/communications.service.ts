import { api } from "@/lib/api";
import type {
  ChannelTestResponse,
  Communication,
  CommunicationAutomation,
  CommunicationChannelConfig,
  CommunicationDashboard,
  CommunicationDetail,
  CommunicationTemplate,
  CreateCommunicationPayload,
  InAppNotification,
  Paginated,
  PatientOption,
  UpdateChannelConfigurationPayload,
} from "./types";

function params(input?: Record<string, string | number | undefined | null>) {
  return Object.fromEntries(
    Object.entries(input ?? {}).filter(
      ([, value]) => value !== undefined && value !== null && value !== "",
    ),
  );
}

export const communicationsService = {
  async dashboard(period = "30") {
    const end = new Date();
    const start = new Date(end);
    start.setDate(start.getDate() - Number(period));
    const { data } = await api.get<CommunicationDashboard>(
      "communications/dashboard/",
      {
        params: {
          start_date: start.toISOString(),
          end_date: end.toISOString(),
        },
      },
    );
    return data;
  },
  async list(filters?: Record<string, string | number | undefined>) {
    const { data } = await api.get<Paginated<Communication>>(
      "communications/",
      { params: params(filters) },
    );
    return data;
  },
  async detail(id: string) {
    const { data } = await api.get<CommunicationDetail>(
      `communications/${id}/`,
    );
    return data;
  },
  async create(payload: CreateCommunicationPayload) {
    const { data } = await api.post<CommunicationDetail>(
      "communications/",
      payload,
      { headers: { "Idempotency-Key": crypto.randomUUID() } },
    );
    return data;
  },
  async action(
    id: string,
    action: "cancel" | "retry" | "send" | "mark-manually-sent" | "open-manual",
  ) {
    const { data } = await api.post(
      action === "open-manual"
        ? `communications/${id}/open-manual/`
        : `communications/${id}/${action}/`,
    );
    return data;
  },
  async templates(filters?: Record<string, string | undefined>) {
    const { data } = await api.get<
      Paginated<CommunicationTemplate> | CommunicationTemplate[]
    >("communications/templates/", { params: params(filters) });
    return Array.isArray(data) ? data : data.results;
  },
  async automations() {
    const { data } = await api.get<
      Paginated<CommunicationAutomation> | CommunicationAutomation[]
    >("communications/automations/");
    return Array.isArray(data) ? data : data.results;
  },
  async toggleAutomation(id: number, active: boolean) {
    const { data } = await api.post<CommunicationAutomation>(
      `communications/automations/${id}/${active ? "activate" : "deactivate"}/`,
    );
    return data;
  },
  async channels() {
    const { data } = await api.get<
      Paginated<CommunicationChannelConfig> | CommunicationChannelConfig[]
    >("communications/channels/");
    return Array.isArray(data) ? data : data.results;
  },
  async updateChannel(
    channel: string,
    payload: UpdateChannelConfigurationPayload,
  ) {
    const { data } = await api.patch<CommunicationChannelConfig>(
      `communications/channels/${channel}/`,
      payload,
    );
    return data;
  },
  async testChannelConnection(channel: string) {
    const { data } = await api.post<CommunicationChannelConfig>(
      `communications/channels/${channel}/test-connection/`,
      {},
    );
    return data;
  },
  async sendChannelTest(channel: string, destination?: string) {
    const { data } = await api.post<ChannelTestResponse>(
      `communications/channels/${channel}/test/`,
      { destination: destination || undefined },
    );
    return data;
  },
  async toggleChannel(channel: string, active: boolean) {
    const { data } = await api.post<CommunicationChannelConfig>(
      `communications/channels/${channel}/${active ? "activate" : "deactivate"}/`,
      {},
    );
    return data;
  },
  async removeChannel(channel: string) {
    const { data } = await api.post<CommunicationChannelConfig>(
      `communications/channels/${channel}/remove/`,
      { confirm: true },
    );
    return data;
  },
  async patients() {
    const { data } = await api.get<Paginated<PatientOption> | PatientOption[]>(
      "patients/",
      { params: { page_size: 100, status: "active" } },
    );
    return Array.isArray(data) ? data : data.results;
  },
  async notifications() {
    const { data } = await api.get<
      Paginated<InAppNotification> | InAppNotification[]
    >("communications/notifications/", { params: { page_size: 10 } });
    return Array.isArray(data) ? data : data.results;
  },
  async unreadCount() {
    const { data } = await api.get<{ count: number }>(
      "communications/notifications/unread-count/",
    );
    return data.count;
  },
  async markNotificationRead(id: number) {
    const { data } = await api.post<InAppNotification>(
      `communications/notifications/${id}/read/`,
    );
    return data;
  },
  async readAllNotifications() {
    const { data } = await api.post<{ updated: number }>(
      "communications/notifications/read-all/",
    );
    return data;
  },
};
