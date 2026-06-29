"use client";

import React, { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import {
  Bell,
  ChevronDown,
  LogOut,
  Moon,
  Search,
  Settings,
  Sun,
  User,
} from "lucide-react";

import { useAuth } from "@/contexts/auth";
import { cn } from "@/lib/utils";

interface HeaderProps {
  className?: string;
}

export function Header({ className }: HeaderProps) {
  const { user, logout } = useAuth();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => setMounted(true), []);

  const getRoleLabel = (role: string) => {
    const roles: Record<string, string> = {
      therapist: "Terapeuta",
      secretary: "Secretária",
      admin: "Administrador",
    };
    return roles[role] || role;
  };

  const isDark = resolvedTheme === "dark";

  return (
    <header
      className={cn(
        "sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background px-6 transition-colors duration-150",
        className,
      )}
    >
      <div className="relative hidden w-full max-w-md md:block">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/70" />
        <input
          type="text"
          placeholder="Buscar pacientes, consultas, prontuários..."
          className="h-9 w-full rounded-lg border border-border bg-card pl-10 pr-4 text-xs text-foreground outline-none transition placeholder:text-muted-foreground/60 focus:border-primary/60 focus:ring-2 focus:ring-primary/10"
        />
      </div>

      <div className="ml-auto flex items-center gap-2 sm:gap-3">
        <button
          type="button"
          onClick={() => setTheme(isDark ? "light" : "dark")}
          className="grid h-9 w-9 place-items-center rounded-lg text-muted-foreground transition hover:bg-secondary hover:text-foreground"
          title={isDark ? "Ativar tema claro" : "Ativar tema escuro"}
          aria-label={isDark ? "Ativar tema claro" : "Ativar tema escuro"}
        >
          {mounted &&
            (isDark ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            ))}
        </button>

        <button
          type="button"
          className="relative grid h-9 w-9 place-items-center rounded-lg text-muted-foreground transition hover:bg-secondary hover:text-foreground"
          title="Notificações"
          aria-label="Notificações"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-background" />
        </button>

        <div className="mx-1 h-6 w-px bg-border" />

        <div className="relative">
          <button
            type="button"
            onClick={() => setIsProfileOpen((current) => !current)}
            className="flex items-center gap-3 rounded-lg p-1.5 transition hover:bg-secondary"
            aria-expanded={isProfileOpen}
          >
            <div className="grid h-8.5 w-8.5 place-items-center rounded-full border border-primary/25 bg-primary/10 text-xs font-bold text-primary">
              {user?.full_name?.charAt(0).toUpperCase() || "J"}
            </div>

            <div className="hidden text-left sm:block">
              <p className="text-xs font-bold leading-none text-foreground">
                {user?.full_name || "Juliana Martins"}
              </p>
              <p className="mt-0.5 text-[10px] text-muted-foreground">
                {user ? getRoleLabel(user.role) : "Terapeuta"}
              </p>
            </div>
            <ChevronDown className="hidden h-3.5 w-3.5 text-muted-foreground sm:block" />
          </button>

          {isProfileOpen && (
            <>
              <button
                type="button"
                className="fixed inset-0 z-40 cursor-default"
                onClick={() => setIsProfileOpen(false)}
                aria-label="Fechar menu de perfil"
              />

              <div className="absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-popover shadow-xl shadow-black/10">
                <div className="border-b border-border px-4 py-3">
                  <p className="truncate text-xs font-bold text-popover-foreground">
                    {user?.full_name || "Juliana Martins"}
                  </p>
                  <p className="mt-0.5 truncate text-[10px] text-muted-foreground">
                    {user?.email || "juliana@teste.com"}
                  </p>
                </div>

                <div className="p-1.5">
                  <button
                    type="button"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-xs text-muted-foreground transition hover:bg-secondary hover:text-foreground"
                  >
                    <User className="h-4 w-4" />
                    Meu perfil
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsProfileOpen(false)}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-xs text-muted-foreground transition hover:bg-secondary hover:text-foreground"
                  >
                    <Settings className="h-4 w-4" />
                    Configurações
                  </button>
                </div>

                <div className="border-t border-border p-1.5">
                  <button
                    type="button"
                    onClick={() => {
                      setIsProfileOpen(false);
                      logout();
                    }}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-xs text-destructive transition hover:bg-destructive/10"
                  >
                    <LogOut className="h-4 w-4" />
                    Sair
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
