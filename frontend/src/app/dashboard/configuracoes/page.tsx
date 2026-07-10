import type { Metadata } from "next";
import { Settings } from "lucide-react";

export const metadata: Metadata = {
  title: "Configurações | Elo Terapêutico",
};

export default function SettingsPage() {
  return (
    <main className="flex min-h-[500px] flex-col items-center justify-center p-8 text-center text-muted-foreground">
      <Settings className="mb-4 h-12 w-12 text-border" />
      <h1 className="text-2xl font-bold text-foreground">Configurações</h1>
      <p className="mt-2 text-sm">Opções de conta e sistema serão disponibilizadas aqui em breve.</p>
    </main>
  );
}
