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
      <div className="min-h-screen w-full flex flex-col items-center justify-center bg-slate-950 text-white gap-4">
        {/* Efeito de luz difusa de fundo */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-primary/20 blur-[100px] pointer-events-none" />
        
        <div className="relative flex items-center justify-center">
          <div className="h-16 w-16 rounded-2xl bg-primary flex items-center justify-center shadow-lg shadow-primary/30 animate-pulse">
            <Activity className="h-8 w-8 text-white animate-bounce" />
          </div>
          <div className="absolute inset-0 rounded-2xl border-2 border-primary/40 scale-120 animate-ping opacity-25" />
        </div>
        <div className="flex flex-col items-center gap-1.5 z-10">
          <h2 className="text-xl font-bold tracking-wider text-slate-100">Carregando Painel</h2>
          <p className="text-sm text-muted-foreground animate-pulse">Sincronizando dados clínicos seguros...</p>
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
        {/* Elemento decorativo de fundo */}
        <div className="absolute top-[10%] right-[5%] w-96 h-96 rounded-full bg-primary/5 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[10%] left-[5%] w-96 h-96 rounded-full bg-violet-600/5 blur-[120px] pointer-events-none" />

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
