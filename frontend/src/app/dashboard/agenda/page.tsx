"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Plus,
  Clock,
  User,
  CheckCircle,
  XCircle,
  AlertCircle,
  CalendarDays,
  DollarSign,
  FileText,
  AlertTriangle,
  Eye,
} from "lucide-react";
import { toast } from "sonner";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { cn } from "@/lib/utils";

import { usePatients } from "@/features/patients/hooks/use-patients";
import {
  useAppointments,
  useAppointment,
  useCreateAppointment,
  useUpdateAppointmentStatus,
  useAvailableSlots,
} from "@/features/agenda/hooks/use-agenda";
import type { TimeSlot } from "@/features/agenda/services/agenda.service";

const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];

const DAYS_OF_WEEK = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

const agendaFormSchema = z.object({
  patientId: z.string().min(1, "Selecione o paciente."),
  date: z.string().min(1, "Data é obrigatória."),
  duration: z.number(),
  useTimeSlots: z.boolean(),
  selectedSlot: z.string().optional(),
  manualStart: z.string().optional(),
  manualEnd: z.string().optional(),
  sessionValue: z.string().min(1, "Valor da sessão é obrigatório."),
  isRecurring: z.boolean(),
  recurrenceRule: z.string(),
  notes: z.string().optional(),
});
type AgendaFormData = z.infer<typeof agendaFormSchema>;

export default function AgendaPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());

  // Detalhe de consulta
  const [selectedAppointmentId, setSelectedAppointmentId] = useState<number | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // Modais de ações
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancellationReason, setCancellationReason] = useState("");

  // React Query para buscar pacientes
  const { data: patientsData } = usePatients({ status: "active" });
  const activePatients = patientsData?.results || [];

  // Filtra o mês inteiro
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const startOfMonth = new Date(year, month, 1).toISOString();
  const endOfMonth = new Date(year, month + 1, 0, 23, 59, 59).toISOString();

  // Busca agendamentos do período
  const {
    data: appointments = [],
    isLoading: loadingAppointments,
    refetch: refetchAppointments,
  } = useAppointments({
    start_time_gte: startOfMonth,
    start_time_lte: endOfMonth,
  });

  // Busca detalhes de um agendamento específico
  const { data: selectedAppointmentDetails, isLoading: loadingDetail } = useAppointment(
    selectedAppointmentId || undefined
  );

  // Mutações
  const createAppointmentMutation = useCreateAppointment();
  const updateStatusMutation = useUpdateAppointmentStatus();

  // Form com React Hook Form + Zod
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AgendaFormData>({
    resolver: zodResolver(agendaFormSchema),
    defaultValues: {
      patientId: "",
      date: new Date().toISOString().split("T")[0],
      duration: 50,
      useTimeSlots: true,
      selectedSlot: "",
      manualStart: "09:00",
      manualEnd: "09:50",
      sessionValue: "180.00",
      isRecurring: false,
      recurrenceRule: "WEEKLY",
      notes: "",
    },
  });

  const watchDate = watch("date");
  const watchDuration = watch("duration");
  const watchUseTimeSlots = watch("useTimeSlots");
  const watchIsRecurring = watch("isRecurring");

  // Query de horários disponíveis
  const { data: availableSlots = [], isLoading: loadingSlots } = useAvailableSlots(
    watchDate,
    watchDuration,
    isNewModalOpen && watchUseTimeSlots
  );

  // Auto-seleciona primeiro slot retornado
  useEffect(() => {
    if (availableSlots.length > 0) {
      setValue("selectedSlot", JSON.stringify(availableSlots[0]));
    } else {
      setValue("selectedSlot", "");
    }
  }, [availableSlots, setValue]);

  // Busca agendamentos do mês quando muda currentDate
  useEffect(() => {
    refetchAppointments();
  }, [currentDate, refetchAppointments]);

  // Navegar meses
  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const setToday = () => {
    const todayDate = new Date();
    setCurrentDate(todayDate);
    setSelectedDate(todayDate);
  };

  // Abre os detalhes
  const openAppointmentDetails = (apptId: number) => {
    setSelectedAppointmentId(apptId);
    setIsDetailModalOpen(true);
  };

  // Atualização rápida de status
  const updateStatus = async (apptId: number, statusStr: string, reason?: string) => {
    updateStatusMutation.mutate(
      { id: apptId, status: statusStr, cancellationReason: reason },
      {
        onSuccess: () => {
          refetchAppointments();
          setIsCancelModalOpen(false);
          setCancellationReason("");
          setIsDetailModalOpen(false);
          setSelectedAppointmentId(null);
        },
      }
    );
  };

  // Criação da consulta
  const onSubmit = async (data: AgendaFormData) => {
    let startTimeStr = "";
    let endTimeStr = "";

    if (data.useTimeSlots) {
      if (!data.selectedSlot) {
        toast.error("Selecione um horário", { description: "Nenhum horário livre disponível." });
        return;
      }
      const slotObj: TimeSlot = JSON.parse(data.selectedSlot);
      startTimeStr = slotObj.start_datetime;
      endTimeStr = slotObj.end_datetime;
    } else {
      startTimeStr = `${data.date}T${data.manualStart}:00`;
      endTimeStr = `${data.date}T${data.manualEnd}:00`;
    }

    const payload = {
      patient: Number(data.patientId),
      start_time: startTimeStr,
      end_time: endTimeStr,
      notes: data.notes || "",
      session_value: data.sessionValue,
      is_recurring: data.isRecurring,
      recurrence_rule: data.isRecurring ? data.recurrenceRule : null,
    };

    createAppointmentMutation.mutate(payload, {
      onSuccess: () => {
        setIsNewModalOpen(false);
        reset();
        refetchAppointments();
      },
    });
  };

  // Constrói dias do calendário do mês atual
  const buildCalendarDays = () => {
    const calendarYear = currentDate.getFullYear();
    const calendarMonth = currentDate.getMonth();

    const firstDayIndex = new Date(calendarYear, calendarMonth, 1).getDay();
    const totalDays = new Date(calendarYear, calendarMonth + 1, 0).getDate();
    const prevMonthDays = new Date(calendarYear, calendarMonth, 0).getDate();

    const cells = [];

    // Mês anterior
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      const date = new Date(calendarYear, calendarMonth - 1, prevMonthDays - i);
      cells.push({
        date,
        isCurrentMonth: false,
        isToday: isSameDate(date, new Date()),
      });
    }

    // Mês atual
    for (let i = 1; i <= totalDays; i++) {
      const date = new Date(calendarYear, calendarMonth, i);
      cells.push({
        date,
        isCurrentMonth: true,
        isToday: isSameDate(date, new Date()),
      });
    }

    // Próximo mês
    const remainingCells = 42 - cells.length;
    for (let i = 1; i <= remainingCells; i++) {
      const date = new Date(calendarYear, calendarMonth + 1, i);
      cells.push({
        date,
        isCurrentMonth: false,
        isToday: isSameDate(date, new Date()),
      });
    }

    return cells;
  };

  const isSameDate = (d1: Date, d2: Date) => {
    return (
      d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate()
    );
  };

  const getAppointmentsForDate = (date: Date) => {
    return appointments.filter((appt) => {
      const apptDate = new Date(appt.start_time);
      return isSameDate(apptDate, date);
    });
  };

  const selectedDayAppointments = getAppointmentsForDate(selectedDate).sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
      case "completed":
        return "bg-slate-500/10 text-slate-500 border-slate-500/20";
      case "missed":
        return "bg-rose-500/10 text-rose-500 border-rose-500/20";
      case "cancelled":
        return "bg-secondary text-muted-foreground border-border";
      case "rescheduled":
        return "bg-primary/10 text-primary border-primary/20";
      default:
        return "bg-primary/10 text-primary border-primary/20";
    }
  };

  const calendarDays = buildCalendarDays();

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Agenda Clínica
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Controle de horários de sessões, confirmações financeiras e recorrências
          </p>
        </div>
        <Button
          onClick={() => {
            reset({
              patientId: "",
              date: selectedDate.toISOString().split("T")[0],
              duration: 50,
              useTimeSlots: true,
              selectedSlot: "",
              manualStart: "09:00",
              manualEnd: "09:50",
              sessionValue: "180.00",
              isRecurring: false,
              recurrenceRule: "WEEKLY",
              notes: "",
            });
            setIsNewModalOpen(true);
          }}
          leftIcon={<Plus className="h-4 w-4" />}
          className="text-white font-semibold self-start sm:self-auto"
        >
          Novo Agendamento
        </Button>
      </div>

      {/* Grid Principal */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Lado Esquerdo: Calendário Mensal */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="border-border/80 bg-card shadow-xs p-5">
            {/* Header Calendário */}
            <div className="flex items-center justify-between pb-4 border-b border-border/40">
              <div className="flex items-center gap-2">
                <CalendarIcon className="h-4.5 w-4.5 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">
                  {MONTHS[currentDate.getMonth()]} de {currentDate.getFullYear()}
                </h3>
              </div>
              <div className="flex items-center gap-1.5">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={setToday}
                  className="text-xs h-8"
                >
                  Hoje
                </Button>
                <div className="flex items-center border border-border/60 rounded-md bg-secondary">
                  <button
                    onClick={prevMonth}
                    className="p-1.5 hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition rounded-l-md cursor-pointer"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <div className="h-4.5 w-[1px] bg-border/60" />
                  <button
                    onClick={nextMonth}
                    className="p-1.5 hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition rounded-r-md cursor-pointer"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Grid do Calendário */}
            <div className="mt-4">
              <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">
                {DAYS_OF_WEEK.map((d) => (
                  <div key={d} className="py-1">{d}</div>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-1">
                {loadingAppointments ? (
                  <div className="col-span-7 py-32 text-center flex flex-col items-center gap-2">
                    <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs text-muted-foreground animate-pulse">Carregando consultas...</span>
                  </div>
                ) : (
                  calendarDays.map((cell, index) => {
                    const dayAppts = getAppointmentsForDate(cell.date);
                    const isSelected = isSameDate(cell.date, selectedDate);
                    
                    return (
                      <div
                        key={index}
                        onClick={() => setSelectedDate(cell.date)}
                        className={cn(
                          "min-h-[84px] border p-1.5 rounded-md flex flex-col justify-between transition-colors cursor-pointer select-none relative",
                          cell.isCurrentMonth
                            ? "bg-card border-border/60 hover:border-primary/50 text-foreground"
                            : "bg-secondary/5 border-border/10 text-muted-foreground/30 hover:border-border/30",
                          isSelected && "ring-1 ring-primary bg-primary/5 border-transparent",
                          cell.isToday && "border-primary"
                        )}
                      >
                        {/* Número do Dia */}
                        <div className={cn(
                          "text-[10px] font-bold self-end h-5 w-5 flex items-center justify-center",
                          cell.isToday ? "text-primary bg-primary/10 rounded-full" : "text-muted-foreground"
                        )}>
                          {cell.date.getDate()}
                        </div>

                        {/* Eventos / Badges */}
                        <div className="mt-1 space-y-0.5 overflow-hidden flex-1 flex flex-col justify-end">
                          {dayAppts.slice(0, 2).map((appt) => (
                            <div
                              key={appt.id}
                              className={cn(
                                "text-[8px] px-1 py-0.5 rounded-sm border font-medium truncate leading-none",
                                getStatusColor(appt.status)
                              )}
                            >
                              {new Date(appt.start_time).toLocaleTimeString("pt-BR", {
                                hour: "2-digit",
                                minute: "2-digit"
                              })} - {appt.patient_name?.split(" ")[0]}
                            </div>
                          ))}
                          {dayAppts.length > 2 && (
                            <div className="text-[7px] text-center font-bold text-primary bg-primary/10 px-1 py-0.5 rounded-sm border border-primary/20">
                              + {dayAppts.length - 2} mais
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* Lado Direito: Agenda Diária */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="border-border/80 bg-card shadow-xs p-5 h-full flex flex-col justify-between">
            <div className="space-y-4">
              <div className="border-b border-border/40 pb-3">
                <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <CalendarDays className="h-4 w-4 text-primary" />
                  Agenda do Dia
                </h4>
                <p className="text-sm font-bold text-foreground mt-1">
                  {selectedDate.toLocaleDateString("pt-BR", {
                    weekday: "long",
                    day: "numeric",
                    month: "short"
                  })}
                </p>
              </div>

              {/* Lista de Sessões */}
              <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
                {selectedDayAppointments.length === 0 ? (
                  <div className="py-12 text-center text-muted-foreground space-y-2">
                    <Clock className="h-6 w-6 text-muted-foreground/30 mx-auto" />
                    <p className="text-[10px]">Nenhuma consulta agendada.</p>
                  </div>
                ) : (
                  selectedDayAppointments.map((appt) => {
                    const startStr = new Date(appt.start_time).toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit"
                    });
                    const endStr = new Date(appt.end_time).toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit"
                    });

                    return (
                      <div
                        key={appt.id}
                        className="p-3 bg-secondary/20 border border-border/50 hover:border-primary/30 rounded-md transition-colors relative overflow-hidden group"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div className="space-y-0.5">
                            <span className="text-[10px] font-bold text-primary block">
                              {startStr} - {endStr}
                            </span>
                            <span className="text-xs font-semibold text-foreground block truncate max-w-[110px]">
                              {appt.patient_name}
                            </span>
                            <span className="text-[9px] text-muted-foreground block">
                              {appt.therapist_name?.split(" ")[0] || ""}
                            </span>
                          </div>
                          
                          <span className={cn(
                            "inline-flex px-1.5 py-0.5 rounded-sm text-[8px] font-bold border capitalize shrink-0",
                            getStatusColor(appt.status)
                          )}>
                            {appt.status_display}
                          </span>
                        </div>

                        {/* Botão de Ações */}
                        <div className="flex gap-1.5 justify-end mt-2.5 border-t border-border/40 pt-2 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => openAppointmentDetails(appt.id)}
                            className="h-6 w-6 text-muted-foreground hover:text-foreground cursor-pointer"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                          {appt.status === "scheduled" && (
                            <>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => updateStatus(appt.id, "confirmed")}
                                className="h-6 w-6 text-emerald-500 hover:bg-emerald-500/10 cursor-pointer"
                                title="Confirmar"
                              >
                                <CheckCircle className="h-3.5 w-3.5" />
                              </Button>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => {
                                  setSelectedAppointmentId(appt.id);
                                  setIsCancelModalOpen(true);
                                }}
                                className="h-6 w-6 text-rose-500 hover:bg-rose-500/10 cursor-pointer"
                                title="Cancelar"
                              >
                                <XCircle className="h-3.5 w-3.5" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                reset({
                  patientId: "",
                  date: selectedDate.toISOString().split("T")[0],
                  duration: 50,
                  useTimeSlots: true,
                  selectedSlot: "",
                  manualStart: "09:00",
                  manualEnd: "09:50",
                  sessionValue: "180.00",
                  isRecurring: false,
                  recurrenceRule: "WEEKLY",
                  notes: "",
                });
                setIsNewModalOpen(true);
              }}
              className="border-dashed border-border hover:bg-secondary w-full mt-4 text-xs h-9 flex items-center justify-center gap-1.5"
            >
              <Plus className="h-3.5 w-3.5" />
              Agendar no dia {selectedDate.getDate()}
            </Button>
          </Card>
        </div>
      </div>

      {/* MODAL: NOVO AGENDAMENTO */}
      <Modal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        title="Agendar Nova Consulta"
        description="Agende uma consulta individual ou configure uma recorrência de sessões."
        className="max-w-xl"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {/* Paciente */}
          <div className="flex flex-col gap-1">
            <label htmlFor="new-appt-patient" className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
              <User className="h-3.5 w-3.5 text-primary" /> Paciente *
            </label>
            <select
              id="new-appt-patient"
              {...register("patientId")}
              className="w-full h-10 bg-secondary border border-border rounded-md px-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
            >
              <option value="">Selecione o paciente ativo...</option>
              {activePatients.map((p) => (
                <option key={p.id} value={p.id}>{p.full_name}</option>
              ))}
            </select>
            {errors.patientId && (
              <p className="text-[10px] text-destructive mt-0.5">{errors.patientId.message}</p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Input
                id="new-appt-date"
                label="Data da Consulta *"
                type="date"
                error={errors.date?.message}
                {...register("date")}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="new-appt-duration" className="text-xs font-semibold text-muted-foreground">Duração</label>
              <select
                id="new-appt-duration"
                {...register("duration", { valueAsNumber: true })}
                className="w-full h-10 bg-secondary border border-border rounded-md px-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
              >
                <option value="30">30 minutos</option>
                <option value="45">45 minutos</option>
                <option value="50">50 minutos (Recomendado)</option>
                <option value="60">60 minutos</option>
                <option value="90">90 minutos</option>
              </select>
            </div>
          </div>

          {/* Seleção de horários livres */}
          <div className="p-4 rounded-md border border-primary/20 bg-primary/5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-primary flex items-center gap-1.5">
                <Clock className="h-4 w-4" /> Verificar Horários Livres
              </span>
              <label className="relative inline-flex items-center cursor-pointer select-none">
                <input
                  type="checkbox"
                  {...register("useTimeSlots")}
                  className="sr-only peer"
                />
                <div className="w-8 h-4.5 bg-border/60 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-3.5 after:w-3.5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            {watchUseTimeSlots ? (
              <div className="space-y-2">
                {loadingSlots ? (
                  <div className="text-center py-2 flex items-center justify-center gap-1.5">
                    <div className="h-4.5 w-4.5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs text-muted-foreground animate-pulse">Buscando slots do terapeuta...</span>
                  </div>
                ) : availableSlots.length === 0 ? (
                  <div className="text-[10px] text-muted-foreground p-2.5 bg-card rounded-md text-center flex items-center gap-1.5 justify-center border border-border/40">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                    Nenhum slot disponível configurado para este dia da semana.
                  </div>
                ) : (
                  <select
                    {...register("selectedSlot")}
                    className="w-full h-10 bg-card border border-border rounded-md px-3 text-xs focus:outline-none focus:border-primary text-foreground cursor-pointer"
                  >
                    {availableSlots.map((slot, index) => (
                      <option key={index} value={JSON.stringify(slot)}>
                        {slot.start} - {slot.end}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  id="new-appt-start"
                  label="Início Manual"
                  type="time"
                  {...register("manualStart")}
                />
                <Input
                  id="new-appt-end"
                  label="Término Manual"
                  type="time"
                  {...register("manualEnd")}
                />
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              id="new-appt-value"
              label="Valor da Sessão (R$)"
              type="text"
              required
              leftIcon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
              {...register("sessionValue")}
            />

            <div className="flex items-center justify-end pb-3 pt-3">
              <label className="flex items-center gap-2 text-xs font-semibold text-muted-foreground select-none cursor-pointer">
                <input
                  type="checkbox"
                  {...register("isRecurring")}
                  className="rounded-xs bg-secondary border-border focus:ring-primary text-primary"
                />
                <span>Consulta Recorrente?</span>
              </label>
            </div>
          </div>

          {/* Regra de recorrência */}
          {watchIsRecurring && (
            <div className="flex flex-col gap-1 p-3.5 rounded-md border border-primary/20 bg-primary/5">
              <label htmlFor="new-appt-recurrence" className="text-xs font-semibold text-muted-foreground">Frequência da Recorrência</label>
              <select
                id="new-appt-recurrence"
                {...register("recurrenceRule")}
                className="w-full h-10 bg-card border border-border rounded-md px-3 text-sm focus:outline-none focus:border-primary text-foreground cursor-pointer"
              >
                <option value="WEEKLY">Semanal (Gera 4 sessões consecutivas)</option>
                <option value="BIWEEKLY">Quinzenal (Gera 4 sessões consecutivas)</option>
                <option value="MONTHLY">Mensal (Gera 4 sessões consecutivas)</option>
              </select>
            </div>
          )}

          <Textarea
            id="new-appt-notes"
            label="Observações do Agendamento (opcional)"
            placeholder="Anotações ou avisos sobre esta sessão..."
            {...register("notes")}
          />

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsNewModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={createAppointmentMutation.isPending}
              className="text-white font-semibold"
            >
              Confirmar Agendamento
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL: DETALHES DE CONSULTA */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedAppointmentId(null);
        }}
        title="Detalhes do Agendamento"
        description="Ficha detalhada do horário agendado e status da sessão."
        className="max-w-md"
      >
        {loadingDetail ? (
          <div className="py-8 text-center flex flex-col items-center gap-3">
            <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-muted-foreground">Carregando detalhes...</span>
          </div>
        ) : selectedAppointmentDetails ? (
          <div className="space-y-4">
            <div className="space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-sm text-foreground">{selectedAppointmentDetails.patient_name}</h4>
                  <p className="text-[10px] text-muted-foreground">Dr(a). {selectedAppointmentDetails.therapist_name}</p>
                </div>
                <span className={cn(
                  "inline-flex px-2 py-0.5 rounded-sm text-[10px] font-bold border capitalize",
                  getStatusColor(selectedAppointmentDetails.status)
                )}>
                  {selectedAppointmentDetails.status_display}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 border-t border-b border-border/40 py-3 text-xs">
                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">Horário</p>
                  <div className="font-semibold flex items-center gap-1 text-foreground">
                    <Clock className="h-3.5 w-3.5 text-primary shrink-0" />
                    <span>
                      {new Date(selectedAppointmentDetails.start_time).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit"
                      })} - {new Date(selectedAppointmentDetails.end_time).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit"
                      })}
                    </span>
                  </div>
                </div>

                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">Duração</p>
                  <p className="font-semibold text-foreground">{selectedAppointmentDetails.duration_display}</p>
                </div>

                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">Valor da Sessão</p>
                  <p className="font-semibold text-primary">
                    R$ {parseFloat(selectedAppointmentDetails.session_value).toFixed(2)}
                  </p>
                </div>

                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">Recorrente</p>
                  <p className="font-semibold text-foreground">{selectedAppointmentDetails.is_recurring ? `Sim (${selectedAppointmentDetails.recurrence_rule})` : "Não"}</p>
                </div>
              </div>

              {selectedAppointmentDetails.notes && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase flex items-center gap-1">
                    <FileText className="h-3.5 w-3.5" /> Observações
                  </p>
                  <p className="text-xs text-foreground bg-secondary p-2.5 rounded-md border border-border">
                    {selectedAppointmentDetails.notes}
                  </p>
                </div>
              )}

              {selectedAppointmentDetails.status === "cancelled" && selectedAppointmentDetails.cancellation_reason && (
                <div className="space-y-1 p-3 rounded-md bg-rose-500/5 border border-rose-500/10">
                  <p className="text-[10px] font-bold text-rose-600 dark:text-rose-400 uppercase flex items-center gap-1">
                    <AlertCircle className="h-3.5 w-3.5" /> Motivo do Cancelamento
                  </p>
                  <p className="text-xs text-rose-700 dark:text-rose-300 font-medium">
                    {selectedAppointmentDetails.cancellation_reason}
                  </p>
                </div>
              )}
            </div>

            {/* Ações */}
            <div className="flex gap-2 pt-4 border-t border-border/40 justify-end">
              {selectedAppointmentDetails.status === "scheduled" && (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => updateStatus(selectedAppointmentDetails.id, "confirmed")}
                    className="text-xs text-emerald-600 dark:text-emerald-500 border-emerald-500/20 hover:bg-emerald-500/5 font-semibold cursor-pointer"
                  >
                    Confirmar Presença
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => updateStatus(selectedAppointmentDetails.id, "missed")}
                    className="text-xs text-rose-600 dark:text-rose-500 border-rose-500/20 hover:bg-rose-500/5 font-semibold cursor-pointer"
                  >
                    Faltou
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setIsCancelModalOpen(true)}
                    className="text-xs text-muted-foreground border-border hover:bg-secondary font-semibold cursor-pointer"
                  >
                    Cancelar Sessão
                  </Button>
                </>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setIsDetailModalOpen(false);
                  setSelectedAppointmentId(null);
                }}
                className="text-xs h-9"
              >
                Fechar
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* MODAL: DIGITAR MOTIVO DE CANCELAMENTO */}
      <Modal
        isOpen={isCancelModalOpen}
        onClose={() => {
          setIsCancelModalOpen(false);
          setCancellationReason("");
        }}
        title="Cancelar Consulta"
        description="Justifique o motivo do cancelamento da consulta clínica. Esta ação é irreversível."
        className="max-w-md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (selectedAppointmentId) {
              updateStatus(selectedAppointmentId, "cancelled", cancellationReason);
            }
          }}
          className="space-y-4"
        >
          <Textarea
            label="Motivo do Cancelamento *"
            placeholder="Ex: Paciente solicitou desmarcação por imprevisto..."
            value={cancellationReason}
            onChange={(e) => setCancellationReason(e.target.value)}
            required
            className="min-h-[100px]"
          />

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsCancelModalOpen(false);
                setCancellationReason("");
              }}
            >
              Descartar
            </Button>
            <Button
              type="submit"
              className="bg-rose-600 hover:bg-rose-700 text-white font-semibold"
            >
              Confirmar Cancelamento
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
