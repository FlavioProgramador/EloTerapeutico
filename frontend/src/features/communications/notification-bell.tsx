"use client";

import Link from "next/link";
import { useState } from "react";
import { Bell, CheckCheck, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  useMarkNotificationRead,
  useNotifications,
  useReadAllNotifications,
  useUnreadNotificationsCount,
} from "./use-communications";

function formatNotificationDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const notifications = useNotifications({ page_size: 8 }, open);
  const unread = useUnreadNotificationsCount();
  const markRead = useMarkNotificationRead();
  const readAll = useReadAllNotifications();
  const count = unread.data ?? 0;
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="relative grid h-9 w-9 place-items-center rounded-lg text-muted-foreground transition hover:bg-secondary hover:text-foreground"
        title="Notificações"
        aria-label={`Notificações${count ? `, ${count} não lidas` : ""}`}
        aria-expanded={open}
      >
        <Bell className="h-4 w-4" />
        {count > 0 && (
          <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-primary px-1 text-center text-[9px] font-bold leading-4 text-primary-foreground ring-2 ring-background">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>
      {open && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 cursor-default"
            onClick={() => setOpen(false)}
            aria-label="Fechar notificações"
          />
          <div className="absolute right-0 z-50 mt-2 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-xl border border-border bg-popover shadow-xl shadow-black/10">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <p className="text-sm font-bold text-popover-foreground">
                  Notificações
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {count} não lida{count === 1 ? "" : "s"}
                </p>
              </div>
              <button
                type="button"
                disabled={!count || readAll.isPending}
                onClick={() => readAll.mutate(undefined)}
                className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[10px] font-semibold text-primary transition hover:bg-primary/10 disabled:opacity-50"
              >
                {readAll.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <CheckCheck className="h-3.5 w-3.5" />
                )}
                Marcar todas
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto p-1.5">
              {notifications.isLoading && (
                <div className="flex items-center justify-center gap-2 p-8 text-xs text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Carregando...
                </div>
              )}
              {notifications.isError && (
                <p className="p-6 text-center text-xs text-destructive">
                  Não foi possível carregar as notificações.
                </p>
              )}
              {!notifications.isLoading && notifications.data?.results.length === 0 && (
                <p className="p-8 text-center text-xs text-muted-foreground">
                  Nenhuma notificação registrada.
                </p>
              )}
              {notifications.data?.results.map((notification) => {
                const content = (
                  <span className="block min-w-0">
                    <span className="flex items-center gap-2">
                      <span className="truncate text-xs font-bold text-popover-foreground">
                        {notification.title}
                      </span>
                      {!notification.is_read && (
                        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                      )}
                    </span>
                    <span className="mt-1 line-clamp-2 block text-[11px] leading-relaxed text-muted-foreground">
                      {notification.message}
                    </span>
                    <span className="mt-1.5 block text-[9px] text-muted-foreground/80">
                      {formatNotificationDate(notification.created_at)}
                    </span>
                  </span>
                );
                const className = cn(
                  "block w-full rounded-lg px-3 py-3 text-left transition hover:bg-secondary",
                  !notification.is_read && "bg-primary/5",
                );
                if (notification.internal_url)
                  return (
                    <Link
                      key={notification.public_id}
                      href={notification.internal_url}
                      onClick={() => {
                        if (!notification.is_read)
                          markRead.mutate(notification.public_id);
                        setOpen(false);
                      }}
                      className={className}
                    >
                      {content}
                    </Link>
                  );
                return (
                  <button
                    key={notification.public_id}
                    type="button"
                    onClick={() =>
                      !notification.is_read && markRead.mutate(notification.public_id)
                    }
                    className={className}
                  >
                    {content}
                  </button>
                );
              })}
            </div>
            <Link
              href="/dashboard/notificacoes"
              onClick={() => setOpen(false)}
              className="block border-t border-border px-4 py-3 text-center text-xs font-semibold text-primary hover:bg-secondary"
            >
              Ver todas as notificações
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
