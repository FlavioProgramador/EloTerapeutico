"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Archive,
  ArrowLeft,
  Bell,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  Loader2,
  MailOpen,
  RotateCcw,
  Search,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import {
  useArchiveNotification,
  useArchiveReadNotifications,
  useMarkNotificationRead,
  useMarkNotificationUnread,
  useNotificationCategories,
  useNotifications,
  useReadAllNotifications,
} from "./use-communications";
import type { NotificationCategory } from "./types";

type Tab = "all" | "unread" | "archived";

const priorityLabels = {
  low: "Baixa",
  normal: "Normal",
  high: "Alta",
  critical: "Crítica",
};

export function NotificationsPage() {
  const [tab, setTab] = useState<Tab>("all");
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<NotificationCategory | "">("");
  const [priority, setPriority] = useState("");
  const [search, setSearch] = useState("");
  const filters = useMemo(
    () => ({
      page,
      page_size: 20,
      is_read: tab === "unread" ? "false" : undefined,
      archived: tab === "archived" ? "true" : undefined,
      category: category || undefined,
      priority: priority || undefined,
      search: search || undefined,
    }),
    [category, page, priority, search, tab],
  );
  const notifications = useNotifications(filters);
  const categories = useNotificationCategories();
  const markRead = useMarkNotificationRead();
  const markUnread = useMarkNotificationUnread();
  const archive = useArchiveNotification();
  const readAll = useReadAllNotifications();
  const archiveRead = useArchiveReadNotifications();
  const totalPages = Math.max(
    1,
    Math.ceil((notifications.data?.count ?? 0) / 20),
  );

  function changeTab(next: Tab) {
    setTab(next);
    setPage(1);
  }

  return (
    <main className="min-h-full bg-background p-4 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Link
              href="/dashboard/comunicacoes"
              className="inline-flex items-center gap-1 text-xs font-semibold text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Comunicações
            </Link>
            <h1 className="mt-3 text-2xl font-bold text-foreground">
              Central de notificações
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Acompanhe eventos administrativos sem expor conteúdo clínico sensível.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => readAll.mutate(undefined)}
              disabled={readAll.isPending}
            >
              {readAll.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <CheckCheck className="mr-2 h-4 w-4" />
              )}
              Marcar todas como lidas
            </Button>
            <Button
              variant="outline"
              onClick={() => archiveRead.mutate(undefined)}
              disabled={archiveRead.isPending}
            >
              <Archive className="mr-2 h-4 w-4" /> Arquivar lidas
            </Button>
          </div>
        </div>

        <section className="rounded-xl border border-border bg-card p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap gap-2" role="tablist" aria-label="Estado das notificações">
              {([
                ["all", "Todas"],
                ["unread", "Não lidas"],
                ["archived", "Arquivadas"],
              ] as const).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  role="tab"
                  aria-selected={tab === value}
                  onClick={() => changeTab(value)}
                  className={cn(
                    "rounded-lg px-3 py-2 text-xs font-semibold transition",
                    tab === value
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-muted-foreground hover:text-foreground",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="grid gap-2 sm:grid-cols-[minmax(12rem,1fr)_10rem_9rem]">
              <label className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                  placeholder="Buscar notificações"
                  aria-label="Buscar notificações"
                  className="h-10 w-full rounded-lg border border-border bg-background pl-9 pr-3 text-xs outline-none focus:border-primary"
                />
              </label>
              <select
                value={category}
                onChange={(event) => {
                  setCategory(event.target.value as NotificationCategory | "");
                  setPage(1);
                }}
                aria-label="Filtrar por categoria"
                className="h-10 rounded-lg border border-border bg-background px-3 text-xs"
              >
                <option value="">Todas as categorias</option>
                {categories.data?.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
              <select
                value={priority}
                onChange={(event) => {
                  setPriority(event.target.value);
                  setPage(1);
                }}
                aria-label="Filtrar por prioridade"
                className="h-10 rounded-lg border border-border bg-background px-3 text-xs"
              >
                <option value="">Prioridade</option>
                {Object.entries(priorityLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <section className="overflow-hidden rounded-xl border border-border bg-card">
          {notifications.isLoading && (
            <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Carregando notificações...
            </div>
          )}
          {notifications.isError && (
            <div className="grid min-h-64 place-items-center gap-3 p-8 text-center">
              <p className="text-sm text-destructive">Não foi possível carregar as notificações.</p>
              <Button variant="outline" onClick={() => notifications.refetch()}>
                <RotateCcw className="mr-2 h-4 w-4" /> Tentar novamente
              </Button>
            </div>
          )}
          {!notifications.isLoading && notifications.data?.results.length === 0 && (
            <div className="grid min-h-64 place-items-center">
              <EmptyState
                icon={<Bell className="h-6 w-6" />}
                title="Nenhuma notificação"
                description="Não há notificações para os filtros selecionados."
              />
            </div>
          )}
          {notifications.data?.results.map((notification) => (
            <article
              key={notification.public_id}
              className={cn(
                "flex items-start gap-4 border-b border-border px-5 py-4 last:border-0",
                !notification.is_read && !notification.archived_at && "bg-primary/5",
              )}
            >
              <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
                <Bell className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <strong className="text-sm text-foreground">{notification.title}</strong>
                  {!notification.is_read && !notification.archived_at && (
                    <span className="h-2 w-2 rounded-full bg-primary" aria-label="Não lida" />
                  )}
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground">
                    {notification.category_display}
                  </span>
                  <span className="rounded-full border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
                    {notification.priority_display}
                  </span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {notification.message}
                </p>
                <time className="mt-2 block text-[10px] text-muted-foreground">
                  {new Date(notification.created_at).toLocaleString("pt-BR")}
                </time>
                <div className="mt-3 flex flex-wrap gap-2">
                  {notification.internal_url && (
                    <Link
                      href={notification.internal_url}
                      onClick={() => {
                        if (!notification.is_read) markRead.mutate(notification.public_id);
                      }}
                      className="rounded-lg bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground"
                    >
                      {notification.action_label || "Abrir"}
                    </Link>
                  )}
                  {!notification.archived_at && (
                    <button
                      type="button"
                      onClick={() =>
                        notification.is_read
                          ? markUnread.mutate(notification.public_id)
                          : markRead.mutate(notification.public_id)
                      }
                      className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-[11px] font-semibold text-muted-foreground hover:text-foreground"
                    >
                      <MailOpen className="h-3.5 w-3.5" />
                      {notification.is_read ? "Marcar não lida" : "Marcar lida"}
                    </button>
                  )}
                  {!notification.archived_at && (
                    <button
                      type="button"
                      onClick={() => archive.mutate(notification.public_id)}
                      className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-[11px] font-semibold text-muted-foreground hover:text-foreground"
                    >
                      <Archive className="h-3.5 w-3.5" /> Arquivar
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </section>

        {notifications.data && notifications.data.count > 20 && (
          <nav className="flex items-center justify-between" aria-label="Paginação das notificações">
            <span className="text-xs text-muted-foreground">
              Página {page} de {totalPages}
            </span>
            <div className="flex gap-2">
              <Button variant="outline" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button variant="outline" disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </nav>
        )}
      </div>
    </main>
  );
}
