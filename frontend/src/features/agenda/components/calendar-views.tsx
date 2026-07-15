"use client";

import { Clock3, LockKeyhole, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  addDays,
  buildMonthDays,
  isSameDay,
  startOfWeek,
} from "../lib/calendar.mjs";
import type { AgendaAppointment, ScheduleBlock } from "../types";
import { StatusBadge } from "./agenda-ui";

const weekdays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

function eventTone(status: string) {
  if (status === "confirmed")
    return "border-primary/30 bg-primary/10 text-primary";
  if (status === "completed")
    return "border-success/30 bg-success/10 text-success";
  if (status === "missed" || status === "cancelled")
    return "border-destructive/30 bg-destructive/10 text-destructive";
  return "border-warning/30 bg-warning/10 text-warning";
}

export function MonthView({
  currentDate,
  appointments,
  blocks,
  onSelectDate,
  onSelectAppointment,
}: {
  currentDate: Date;
  appointments: AgendaAppointment[];
  blocks: ScheduleBlock[];
  onSelectDate: (date: Date) => void;
  onSelectAppointment: (appointment: AgendaAppointment) => void;
}) {
  const days = buildMonthDays(currentDate);
  return (
    <div className="min-w-[880px]">
      <div className="grid grid-cols-7 border-b border-border bg-secondary/20 text-center text-xs font-semibold text-muted-foreground">
        {weekdays.map((weekday) => (
          <div key={weekday} className="px-2 py-3">
            {weekday}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {days.map((date) => {
          const items = appointments.filter((item) =>
            isSameDay(item.start_time, date),
          );
          const dayBlocks = blocks.filter((item) =>
            isSameDay(item.start_time, date),
          );
          const currentMonth = date.getMonth() === currentDate.getMonth();
          return (
            <button
              type="button"
              key={date.toISOString()}
              onClick={() => onSelectDate(date)}
              className={cn(
                "min-h-32 border-b border-r border-border p-2 text-left transition hover:bg-secondary/20",
                !currentMonth && "bg-secondary/10 text-muted-foreground/60",
              )}
            >
              <span
                className={cn(
                  "mb-2 grid size-7 place-items-center rounded-full text-xs font-semibold",
                  isSameDay(date, new Date()) &&
                    "bg-primary text-primary-foreground",
                )}
              >
                {date.getDate()}
              </span>
              <div className="space-y-1">
                {items.slice(0, 3).map((item) => (
                  <span
                    key={item.id}
                    role="button"
                    tabIndex={0}
                    onClick={(event) => {
                      event.stopPropagation();
                      onSelectAppointment(item);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") onSelectAppointment(item);
                    }}
                    className={cn(
                      "block truncate rounded border px-1.5 py-1 text-[10px] font-semibold",
                      eventTone(item.status),
                    )}
                  >
                    {new Date(item.start_time).toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}{" "}
                    {item.patient_name}
                  </span>
                ))}
                {dayBlocks.slice(0, 1).map((item) => (
                  <span
                    key={`block-${item.id}`}
                    className="flex items-center gap-1 truncate rounded border border-border bg-secondary px-1.5 py-1 text-[10px] text-muted-foreground"
                  >
                    <LockKeyhole className="size-3" /> Bloqueado
                  </span>
                ))}
                {items.length > 3 && (
                  <span className="block text-[10px] font-semibold text-primary">
                    +{items.length - 3} consultas
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function WeekView({
  currentDate,
  appointments,
  blocks,
  onNewAppointment,
  onSelectAppointment,
}: {
  currentDate: Date;
  appointments: AgendaAppointment[];
  blocks: ScheduleBlock[];
  onNewAppointment: (date: Date, time: string) => void;
  onSelectAppointment: (appointment: AgendaAppointment) => void;
}) {
  const start = startOfWeek(currentDate);
  const days = Array.from({ length: 7 }, (_, index) => addDays(start, index));
  const hours = Array.from({ length: 14 }, (_, index) => index + 7);
  return (
    <div className="min-w-[980px]">
      <div className="grid grid-cols-[72px_repeat(7,minmax(130px,1fr))] border-b border-border bg-secondary/20">
        <div className="p-3 text-xs font-semibold text-muted-foreground">
          Horário
        </div>
        {days.map((date) => (
          <div
            key={date.toISOString()}
            className={cn(
              "border-l border-border p-3 text-center",
              isSameDay(date, new Date()) && "bg-primary/10",
            )}
          >
            <span className="block text-xs text-muted-foreground">
              {weekdays[date.getDay()]}
            </span>
            <strong className="text-sm">{date.getDate()}</strong>
          </div>
        ))}
      </div>
      {hours.map((hour) => (
        <div
          key={hour}
          className="grid min-h-20 grid-cols-[72px_repeat(7,minmax(130px,1fr))] border-b border-border"
        >
          <div className="p-3 text-xs text-muted-foreground">
            {String(hour).padStart(2, "0")}:00
          </div>
          {days.map((date) => {
            const items = appointments.filter((item) => {
              const value = new Date(item.start_time);
              return isSameDay(value, date) && value.getHours() === hour;
            });
            const blocked = blocks.some((item) => {
              const startValue = new Date(item.start_time);
              const endValue = new Date(item.end_time);
              return (
                isSameDay(startValue, date) &&
                startValue.getHours() <= hour &&
                endValue.getHours() > hour
              );
            });
            return (
              <button
                type="button"
                key={`${date.toISOString()}-${hour}`}
                onClick={() =>
                  onNewAppointment(date, `${String(hour).padStart(2, "0")}:00`)
                }
                className={cn(
                  "group relative border-l border-border p-1 text-left hover:bg-primary/5",
                  blocked && "bg-secondary/40",
                )}
              >
                {blocked && (
                  <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    <LockKeyhole className="size-3" /> Indisponível
                  </span>
                )}
                {items.map((item) => (
                  <span
                    key={item.id}
                    role="button"
                    tabIndex={0}
                    onClick={(event) => {
                      event.stopPropagation();
                      onSelectAppointment(item);
                    }}
                    className={cn(
                      "mb-1 block rounded border p-1.5 text-[10px] font-semibold",
                      eventTone(item.status),
                    )}
                  >
                    {new Date(item.start_time).toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}{" "}
                    · {item.patient_name}
                  </span>
                ))}
                {!blocked && !items.length && (
                  <Plus className="absolute right-2 top-2 size-3.5 text-primary opacity-0 transition group-hover:opacity-100" />
                )}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}

export function DayView({
  currentDate,
  appointments,
  blocks,
  onNewAppointment,
  onSelectAppointment,
}: {
  currentDate: Date;
  appointments: AgendaAppointment[];
  blocks: ScheduleBlock[];
  onNewAppointment: (date: Date, time: string) => void;
  onSelectAppointment: (appointment: AgendaAppointment) => void;
}) {
  const hours = Array.from({ length: 15 }, (_, index) => index + 7);
  const dayItems = appointments
    .filter((item) => isSameDay(item.start_time, currentDate))
    .sort(
      (left, right) => +new Date(left.start_time) - +new Date(right.start_time),
    );
  return (
    <div className="min-w-[680px]">
      <div className="grid grid-cols-[110px_1fr] border-b border-border bg-secondary/20">
        <div className="p-4 text-xs font-semibold text-muted-foreground">
          Horário
        </div>
        <div className="border-l border-border p-4 text-center">
          <span className="block text-xs capitalize text-muted-foreground">
            {currentDate.toLocaleDateString("pt-BR", { weekday: "long" })}
          </span>
          <strong>{currentDate.toLocaleDateString("pt-BR")}</strong>
        </div>
      </div>
      {hours.map((hour) => {
        const items = dayItems.filter(
          (item) => new Date(item.start_time).getHours() === hour,
        );
        const blocked = blocks.some((item) => {
          const start = new Date(item.start_time);
          const end = new Date(item.end_time);
          return (
            isSameDay(start, currentDate) &&
            start.getHours() <= hour &&
            end.getHours() > hour
          );
        });
        return (
          <button
            type="button"
            key={hour}
            onClick={() =>
              onNewAppointment(
                currentDate,
                `${String(hour).padStart(2, "0")}:00`,
              )
            }
            className="grid min-h-16 w-full grid-cols-[110px_1fr] border-b border-border text-left hover:bg-primary/5"
          >
            <span className="p-4 text-xs text-muted-foreground">
              {String(hour).padStart(2, "0")}:00
            </span>
            <span
              className={cn(
                "border-l border-border p-2",
                blocked && "bg-secondary/40",
              )}
            >
              {blocked && (
                <span className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                  <LockKeyhole className="size-3.5" /> Horário bloqueado
                </span>
              )}
              {items.map((item) => (
                <span
                  key={item.id}
                  role="button"
                  tabIndex={0}
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectAppointment(item);
                  }}
                  className={cn(
                    "mb-1 flex items-center justify-between rounded-lg border p-3",
                    eventTone(item.status),
                  )}
                >
                  <span>
                    <strong className="block text-sm">
                      {item.patient_name}
                    </strong>
                    <span className="mt-1 flex items-center gap-1 text-xs">
                      <Clock3 className="size-3" />
                      {new Date(item.start_time).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}{" "}
                      · {item.duration_display} · {item.modality_display}
                    </span>
                  </span>
                  <StatusBadge status={item.status} />
                </span>
              ))}
            </span>
          </button>
        );
      })}
    </div>
  );
}
