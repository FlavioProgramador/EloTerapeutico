import type { Metadata } from "next";

import { SettingsPageContent } from "@/features/settings/settings-page";

export const metadata: Metadata = {
  title: "Configurações | Elo Terapêutico",
};

export default function SettingsPage() {
  return <SettingsPageContent />;
}
