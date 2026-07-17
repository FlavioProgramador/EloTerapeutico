import type { Metadata } from "next";

import { NotificationsPage } from "@/features/communications/notifications-page";

export const metadata: Metadata = {
  title: "Notificações | Elo Terapêutico",
};

export default function NotificacoesPage() {
  return <NotificationsPage />;
}
