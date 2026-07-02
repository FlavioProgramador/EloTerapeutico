"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  CalendarDays,
  CalendarRange,
  LockKeyhole,
  Package,
  Plus,
  Repeat2,
  Video,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { AgendaCalendarPanel, type AgendaView } from "./agenda-calendar-panel";
import { AppointmentModal } from "./appointment-modal";
import { PackagesPanel } from "./packages-panel";
import { RecurrencesPanel } from "./recurrences-panel";
import { ScheduleBlockModal } from "./schedule-block-modal";
import { TelemedicinePanel } from "./telemedicine-panel";
import { toDateInput } from "../lib/calendar.mjs";

export type AgendaTab = "agenda" | "recurrences" | "packages" | "telemedicine";

const tabs = [
  { id: "agenda" as const, label: "Agenda", href: "/dashboard/agenda", icon: CalendarDays },
  {
    id: "recurrences" as const,
    label: "Recorrências",
    href: "/dashboard/agenda/recurrences",
    icon: Repeat2,
  },
  {
    id: "packages" as const,
    label: "Pacotes",
    href: "/dashboard/agenda/packages",
    icon: Package,
  },
  {
    id: "telemedicine" as const,
    label: "Telemedicina",
    href: "/dashboard/agenda/telemedicine",
    icon: Video,
  },
];

export function AgendaWorkspace({ initialTab = "agenda" }: { initialTab?: AgendaTab }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const tab = useMemo<AgendaTab>(() => {
    if (pathname.endsWith("/recurrences")) return "recurrences";
    if (pathname.endsWith("/packages")) return "packages";
    if (pathname.endsWith("/telemedicine")) return "telemedicine";
    return initialTab;
  }, [initialTab, pathname]);

  const dateParam = searchParams.get("date");
  const viewParam = searchParams.get("view") as AgendaView | null;
  const [selectedDate, setSelectedDate] = useState(() => {
    const parsed = dateParam ? new Date(`${dateParam}T12:00:00`) : new Date();
    return Number.isNaN(parsed.getTime()) ? new Date() : parsed;
  });
  const [view, setView] = useState<AgendaView>(() =>
    viewParam === "day" || viewParam === "week" || viewParam === "month"
      ? viewParam
      : "month",
  );
  const [appointmentOpen, setAppointmentOpen] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [newAppointmentTime, setNewAppointmentTime] = useState("09:00");

  useEffect(() => {
    const saved = window.localStorage.getItem("elo-agenda-view") as AgendaView | null;
    if (!viewParam && (saved === "day" || saved === "week" || saved === "month")) {
      setView(saved);
    }
  }, [viewParam]);

  function updateQuery(date: Date, nextView: AgendaView) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("date", toDateInput(date));
    params.set("view", nextView);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }

  function changeDate(date: Date) {
    setSelectedDate(date);
    updateQuery(date, view);
  }

  function changeView(nextView: AgendaView) {
    setView(nextView);
    window.localStorage.setItem("elo-agenda-view", nextView);
    updateQuery(selectedDate, nextView);
  }

  function openAppointment(date = selectedDate, time = "09:00") {
    setSelectedDate(date);
    setNewAppointmentTime(time);
    setAppointmentOpen(true);
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Agenda</h1>
            <CalendarRange className="size-5 text-muted-foreground" aria-hidden="true" />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Gerencie consultas e horários</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            leftIcon={<LockKeyhole className="size-4" />}
            onClick={() => setBlockOpen(true)}
          >
            Bloquear horário
          </Button>
          <Button leftIcon={<Plus className="size-4" />} onClick={() => openAppointment()}>
            Nova consulta
          </Button>
        </div>
      </header>

      <nav className="flex gap-1 overflow-x-auto border-b border-border" aria-label="Seções da agenda">
        {tabs.map(({ id, label, href, icon: Icon }) => (
          <Link
            key={id}
            href={href}
            aria-current={tab === id ? "page" : undefined}
            className={cn(
              "relative inline-flex shrink-0 items-center gap-2 px-4 py-3 text-sm font-medium text-muted-foreground transition hover:text-foreground",
              tab === id && "text-primary",
            )}
          >
            <Icon className="size-4" />
            {label}
            {tab === id && (
              <span className="absolute inset-x-0 bottom-0 h-0.5 rounded-full bg-primary" />
            )}
          </Link>
        ))}
      </nav>

      {tab === "agenda" && (
        <AgendaCalendarPanel
          selectedDate={selectedDate}
          view={view}
          onDateChange={changeDate}
          onViewChange={changeView}
          onNewAppointment={openAppointment}
        />
      )}
      {tab === "recurrences" && <RecurrencesPanel />}
      {tab === "packages" && <PackagesPanel />}
      {tab === "telemedicine" && <TelemedicinePanel />}

      <AppointmentModal
        open={appointmentOpen}
        defaultDate={selectedDate}
        defaultTime={newAppointmentTime}
        onClose={() => setAppointmentOpen(false)}
      />
      <ScheduleBlockModal
        open={blockOpen}
        defaultDate={selectedDate}
        onClose={() => setBlockOpen(false)}
      />
    </div>
  );
}
