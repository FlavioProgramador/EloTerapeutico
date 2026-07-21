"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Activity } from "lucide-react";

import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { useAuth } from "@/contexts/auth";
import { useOrganization } from "@/contexts/organization";
import { SubscriptionAccessBanner } from "@/features/billing/subscription-access-banner";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const {
    activeOrganization,
    isLoading: organizationLoading,
  } = useOrganization();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (
      !authLoading &&
      !organizationLoading &&
      isAuthenticated &&
      (!activeOrganization || activeOrganization.onboarding_status !== "completed")
    ) {
      router.replace("/onboarding");
    }
  }, [
    activeOrganization,
    authLoading,
    isAuthenticated,
    organizationLoading,
    router,
  ]);

  if (authLoading || organizationLoading) {
    return (
      <div className="flex min-h-screen w-full flex-col items-center justify-center gap-4 bg-background font-sans text-foreground">
        <div className="relative flex items-center justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
            <Activity className="h-6 w-6 animate-pulse text-primary-foreground" />
          </div>
        </div>
        <div className="z-10 flex flex-col items-center gap-1">
          <h2 className="text-sm font-semibold tracking-tight text-foreground">
            Carregando painel...
          </h2>
          <p className="text-xs text-muted-foreground">
            Validando sua organização e seu acesso
          </p>
        </div>
      </div>
    );
  }

  if (
    !isAuthenticated ||
    !activeOrganization ||
    activeOrganization.onboarding_status !== "completed"
  ) {
    return null;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="relative flex flex-1 flex-col overflow-hidden">
        <Header />
        <SubscriptionAccessBanner />
        <main className="z-10 flex-1 overflow-y-auto p-6 md:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${activeOrganization.id}:${pathname}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="h-full w-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
