"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/navigation/sidebar";
import { Header } from "@/components/navigation/header";
import { useAuth } from "@/contexts/auth";
import { Activity } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex flex-col items-center justify-center bg-background text-foreground gap-4 font-sans">
        <div className="relative flex items-center justify-center">
          <div className="h-12 w-12 rounded-lg bg-primary flex items-center justify-center">
            <Activity className="h-6 w-6 text-primary-foreground animate-pulse" />
          </div>
        </div>
        <div className="flex flex-col items-center gap-1 z-10">
          <h2 className="text-sm font-semibold tracking-tight text-foreground">Carregando painel...</h2>
          <p className="text-xs text-muted-foreground">Sincronizando seus dados clínicos protegidos</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Evita exibir flashes de layout não autorizado enquanto o redirecionamento ocorre
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Sidebar Persistente */}
      <Sidebar />

      {/* Área de Conteúdo Principal */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Header Superior */}
        <Header />

        {/* Conteúdo Dinâmico */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 z-10">
          {children}
        </main>
      </div>
    </div>
  );
}
