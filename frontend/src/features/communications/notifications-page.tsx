"use client";

import Link from "next/link";
import { ArrowLeft, Bell, CheckCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import { useMarkNotificationRead, useNotifications, useReadAllNotifications } from "./use-communications";

export function NotificationsPage() {
  const notifications = useNotifications(true);
  const markRead = useMarkNotificationRead();
  const readAll = useReadAllNotifications();
  return <main className="min-h-full bg-background p-4 sm:p-6 lg:p-8"><div className="mx-auto max-w-5xl">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><Link href="/dashboard/comunicacoes" className="inline-flex items-center gap-1 text-xs font-semibold text-muted-foreground hover:text-foreground"><ArrowLeft className="h-3.5 w-3.5" /> Comunicações</Link><h1 className="mt-3 text-2xl font-bold text-foreground">Notificações</h1><p className="mt-1 text-sm text-muted-foreground">Acompanhe confirmações, solicitações, falhas e eventos administrativos.</p></div><Button variant="outline" onClick={() => readAll.mutate()} disabled={readAll.isPending}>{readAll.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCheck className="mr-2 h-4 w-4" />}Marcar todas como lidas</Button></div>
    <section className="mt-6 overflow-hidden rounded-xl border border-border bg-card">
      {notifications.isLoading && <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Carregando notificações...</div>}
      {notifications.isError && <p className="p-8 text-center text-sm text-destructive">Não foi possível carregar as notificações.</p>}
      {!notifications.isLoading && notifications.data?.length === 0 && <div className="grid min-h-64 place-items-center"><EmptyState icon={<Bell className="h-6 w-6" />} title="Nenhuma notificação" description="Os eventos importantes do sistema aparecerão aqui." /></div>}
      {notifications.data?.map((notification) => <button key={notification.id} type="button" onClick={() => !notification.is_read && markRead.mutate(notification.id)} className={cn("flex w-full items-start gap-4 border-b border-border px-5 py-4 text-left transition last:border-0 hover:bg-secondary/60", !notification.is_read && "bg-primary/5")}><span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary/10 text-primary"><Bell className="h-4 w-4" /></span><span className="min-w-0 flex-1"><span className="flex items-center gap-2"><strong className="truncate text-sm text-foreground">{notification.title}</strong>{!notification.is_read && <span className="h-2 w-2 rounded-full bg-primary" />}</span><span className="mt-1 block text-xs leading-relaxed text-muted-foreground">{notification.message}</span><span className="mt-2 block text-[10px] text-muted-foreground">{new Date(notification.created_at).toLocaleString("pt-BR")}</span></span></button>)}
    </section>
  </div></main>;
}
