"use client";

import React, { useEffect, useState } from "react";
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
  Trash2,
  CalendarDays,
  DollarSign,
  FileText,
  AlertTriangle,
  RefreshCw,
  Eye,
} from "lucide-react";
import { useToast } from "@/contexts/toast";
import { useAuth } from "@/contexts/auth";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";

interface Patient {
  id: number;
  full_name: string;
  phone: string;
  email: string;
  status: string;
}

interface Appointment {
  id: number;
  patient_name: string;
  therapist_name: string;
  start_time: string;
  end_time: string;
  duration_display: string;
  status: "scheduled" | "confirmed" | "missed" | "cancelled" | "rescheduled";
  status_display: string;
  session_value: string;
  is_recurring: boolean;
}

interface AppointmentDetail extends Appointment {
  notes: string;
  cancellation_reason: string;
  recurrence_rule?: string;
  parent_appointment?: number;
}

interface TimeSlot {
  start: string;
  end: string;
  start_datetime: string;
  end_datetime: string;
}

const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];

const DAYS_OF_WEEK = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

export default function AgendaPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  // Estados principais
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [patients, setPatients] = useState<Patient[]>([]);

  // Detalhe de consulta
  const [selectedAppointment, setSelectedAppointment] = useState<AppointmentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // Modais de ações
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancellationReason, setCancellationReason] = useState("");

  // Formulário de novo agendamento
  const [newApptForm, setNewApptForm] = useState({
    patientId: "",
    date: new Date().toISOString().split("T")[0],
    useTimeSlots: true,
    duration: 50,
    selectedSlot: "",
    manualStart: "09:00",
    manualEnd: "09:50",
    sessionValue: "180.00",
    isRecurring: false,
    recurrenceRule: "WEEKLY",
    notes: "",
  });

  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submittingAppt, setSubmittingAppt] = useState(false);

  // Busca agendamentos do mês atual
  const fetchAppointments = async () => {
    setIsLoading(true);
    try {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      
      // Filtra o mês inteiro
      const startOfMonth = new Date(year, month, 1).toISOString();
      const endOfMonth = new Date(year, month + 1, 0, 23, 59, 59).toISOString();

      const response = await api.get("agenda/appointments/", {
        params: {
          start_time_gte: startOfMonth,
          start_time_lte: endOfMonth,
        },
      });

      const data = Array.isArray(response.data) ? response.data : (response.data as any).results || [];
      setAppointments(data);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao buscar agenda",
        description: "Não foi possível carregar as consultas do período.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Busca pacientes
  const fetchPatients = async () => {
    try {
      const response = await api.get("patients/");
      const data = Array.isArray(response.data) ? response.data : (response.data as any).results || [];
      // Apenas pacientes ativos
      setPatients(data.filter((p: any) => p.status === "active"));
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [currentDate]);

  useEffect(() => {
    fetchPatients();
  }, []);

  // Busca slots de disponibilidade quando muda a data ou duração no formulário
  const checkAvailability = async (dateStr: string, duration: number) => {
    if (!dateStr) return;
    setLoadingSlots(true);
    setAvailableSlots([]);
    try {
      const response = await api.post<TimeSlot[]>("agenda/appointments/check-availability/", {
        date: dateStr,
        duration: duration,
      });
      setAvailableSlots(response.data);
      if (response.data.length > 0) {
        setNewApptForm(prev => ({ ...prev, selectedSlot: JSON.stringify(response.data[0]) }));
      }
    } catch (error) {
      console.error("Falha ao buscar slots:", error);
    } finally {
      setLoadingSlots(false);
    }
  };

  // Efeito para recarregar slots disponíveis
  useEffect(() => {
    if (isNewModalOpen && newApptForm.useTimeSlots) {
      checkAvailability(newApptForm.date, newApptForm.duration);
    }
  }, [newApptForm.date, newApptForm.duration, newApptForm.useTimeSlots, isNewModalOpen]);

  // Navegar meses
  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const setToday = () => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDate(today);
  };

  // Verifica detalhes da consulta ao clicar nela
  const openAppointmentDetails = async (appt: Appointment) => {
    setLoadingDetail(true);
    setSelectedAppointment(null);
    setIsDetailModalOpen(true);
    try {
      const response = await api.get<AppointmentDetail>(`agenda/appointments/${appt.id}/`);
      setSelectedAppointment(response.data);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao buscar detalhes",
        description: "Não foi possível carregar as informações do agendamento.",
        variant: "destructive",
      });
      setIsDetailModalOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  // Ações de Status rápida
  const updateStatus = async (apptId: number, statusStr: string, reason?: string) => {
    try {
      const payload: any = { status: statusStr };
      if (reason) payload.cancellation_reason = reason;

      await api.patch(`agenda/appointments/${apptId}/status/`, payload);
      
      toast({
        title: "Status atualizado!",
        description: `O agendamento foi marcado como ${statusStr === "confirmed" ? "confirmado" : statusStr === "missed" ? "falta" : "cancelado"}.`,
        variant: "success",
      });

      // Atualiza listagem local
      fetchAppointments();
      
      // Fecha modais e limpa
      setIsCancelModalOpen(false);
      setCancellationReason("");
      setIsDetailModalOpen(false);
      setSelectedAppointment(null);
    } catch (error: any) {
      console.error(error);
      const serverMsg = error.response?.data?.status?.[0] || error.response?.data?.cancellation_reason?.[0];
      toast({
        title: "Erro ao atualizar status",
        description: serverMsg || "Não foi possível mudar o status desta consulta.",
        variant: "destructive",
      });
    }
  };

  // Salva novo agendamento
  const handleCreateAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newApptForm.patientId) {
      toast({
        title: "Selecione o paciente",
        description: "É obrigatório associar a consulta a um paciente.",
        variant: "destructive",
      });
      return;
    }

    setSubmittingAppt(true);

    let startTimeStr = "";
    let endTimeStr = "";

    if (newApptForm.useTimeSlots) {
      if (!newApptForm.selectedSlot) {
        toast({
          title: "Selecione um horário",
          description: "Nenhum horário livre selecionado.",
          variant: "destructive",
        });
        setSubmittingAppt(false);
        return;
      }
      const slotObj: TimeSlot = JSON.parse(newApptForm.selectedSlot);
      startTimeStr = slotObj.start_datetime;
      endTimeStr = slotObj.end_datetime;
    } else {
      startTimeStr = `${newApptForm.date}T${newApptForm.manualStart}:00`;
      endTimeStr = `${newApptForm.date}T${newApptForm.manualEnd}:00`;
    }

    try {
      const payload = {
        patient: Number(newApptForm.patientId),
        start_time: startTimeStr,
        end_time: endTimeStr,
        notes: newApptForm.notes,
        session_value: newApptForm.sessionValue,
        is_recurring: newApptForm.isRecurring,
        recurrence_rule: newApptForm.isRecurring ? newApptForm.recurrenceRule : null,
      };

      await api.post("agenda/appointments/", payload);
      toast({
        title: "Agendado com sucesso!",
        description: "A consulta foi adicionada à agenda clínica.",
        variant: "success",
      });

      setIsNewModalOpen(false);
      // Limpa form
      setNewApptForm(prev => ({
        ...prev,
        patientId: "",
        notes: "",
        isRecurring: false,
      }));
      fetchAppointments();
    } catch (error: any) {
      console.error(error);
      const serverErrors = error.response?.data;
      if (serverErrors && typeof serverErrors === "object") {
        const errorMsg = serverErrors.start_time?.[0] || serverErrors.end_time?.[0] || serverErrors.recurrence_rule?.[0] || "Erro de validação.";
        toast({
          title: "Falha ao agendar",
          description: errorMsg,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Erro no servidor",
          description: "Não foi possível criar a consulta na agenda.",
          variant: "destructive",
        });
      }
    } finally {
      setSubmittingAppt(false);
    }
  };

  // Constrói dias do calendário do mês atual
  const buildCalendarDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    // Primeiro dia da semana do primeiro dia do mês (0 = Domingo, 1 = Segunda, etc.)
    const firstDayIndex = new Date(year, month, 1).getDay();
    // Quantidade de dias no mês
    const totalDays = new Date(year, month + 1, 0).getDate();
    // Quantidade de dias no mês anterior
    const prevMonthDays = new Date(year, month, 0).getDate();

    const cells = [];

    // Preenche dias do mês anterior para completar a primeira semana
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      const date = new Date(year, month - 1, prevMonthDays - i);
      cells.push({
        date,
        isCurrentMonth: false,
        isToday: isSameDate(date, new Date()),
      });
    }

    // Preenche dias do mês atual
    for (let i = 1; i <= totalDays; i++) {
      const date = new Date(year, month, i);
      cells.push({
        date,
        isCurrentMonth: true,
        isToday: isSameDate(date, new Date()),
      });
    }

    // Preenche dias do próximo mês para fechar a grid de 42 quadrados (6 semanas)
    const remainingCells = 42 - cells.length;
    for (let i = 1; i <= remainingCells; i++) {
      const date = new Date(year, month + 1, i);
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

  // Filtra consultas por dia específico
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
      case "missed":
        return "bg-rose-500/10 text-rose-500 border-rose-500/20";
      case "cancelled":
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
      case "rescheduled":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
      default:
        return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    }
  };

  const calendarDays = buildCalendarDays();

  return (
    <div className="space-y-8">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground via-foreground/90 to-foreground/80">
            Agenda Clínica
          </h1>
          <p className="text-muted-foreground mt-1">
            Controle de horários de sessões, confirmações financeiras e recorrências
          </p>
        </div>
        <Button
          onClick={() => {
            setNewApptForm(prev => ({
              ...prev,
              date: selectedDate.toISOString().split("T")[0],
            }));
            setIsNewModalOpen(true);
          }}
          leftIcon={<Plus className="h-5 w-5" />}
          className="text-white font-semibold self-start sm:self-auto"
        >
          Novo Agendamento
        </Button>
      </div>

      {/* Grid Principal: Calendário e Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Lado Esquerdo: Calendário Mensal */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="border-border/30 bg-card/65 backdrop-blur-md p-6">
            {/* Header Calendário */}
            <div className="flex items-center justify-between pb-6 border-b border-border/20">
              <div className="flex items-center gap-3">
                <CalendarIcon className="h-5 w-5 text-primary" />
                <h3 className="text-xl font-extrabold tracking-tight">
                  {MONTHS[currentDate.getMonth()]} de {currentDate.getFullYear()}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={setToday}
                  className="border-border text-foreground text-xs"
                >
                  Hoje
                </Button>
                <div className="flex items-center border border-border/40 rounded-lg bg-secondary/20">
                  <button
                    onClick={prevMonth}
                    className="p-2 hover:bg-secondary/40 text-muted-foreground hover:text-foreground transition rounded-l-lg cursor-pointer"
                  >
                    <ChevronLeft className="h-4.5 w-4.5" />
                  </button>
                  <div className="h-4 w-[1px] bg-border/40" />
                  <button
                    onClick={nextMonth}
                    className="p-2 hover:bg-secondary/40 text-muted-foreground hover:text-foreground transition rounded-r-lg cursor-pointer"
                  >
                    <ChevronRight className="h-4.5 w-4.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Grid do Calendário */}
            <div className="mt-6">
              {/* Cabeçalho dias da semana */}
              <div className="grid grid-cols-7 gap-2 text-center text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                {DAYS_OF_WEEK.map((d) => (
                  <div key={d} className="py-1">{d}</div>
                ))}
              </div>

              {/* Grid 42 Células */}
              <div className="grid grid-cols-7 gap-2">
                {isLoading ? (
                  <div className="col-span-7 py-32 text-center flex flex-col items-center gap-3">
                    <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm text-muted-foreground animate-pulse">Carregando consultas...</span>
                  </div>
                ) : (
                  calendarDays.map((cell, index) => {
                    const dayAppts = getAppointmentsForDate(cell.date);
                    const isSelected = isSameDate(cell.date, selectedDate);
                    
                    return (
                      <div
                        key={index}
                        onClick={() => setSelectedDate(cell.date)}
                        className={`min-h-[90px] border p-2 rounded-lg flex flex-col justify-between transition-all cursor-pointer select-none relative group ${
                          cell.isCurrentMonth
                            ? "bg-card border-border/30 hover:border-primary/50"
                            : "bg-secondary/5 border-border/10 text-muted-foreground/40 hover:border-border/30"
                        } ${
                          isSelected
                            ? "ring-2 ring-primary border-transparent bg-primary/5 shadow-xs"
                            : ""
                        } ${
                          cell.isToday
                            ? "border-primary/50 relative after:absolute after:bottom-1 after:right-1.5 after:h-1.5 after:w-1.5 after:bg-primary after:rounded-full"
                            : ""
                        }`}
                      >
                        {/* Número do Dia */}
                        <div className={`text-xs font-bold self-end ${
                          cell.isToday ? "text-primary bg-primary/10 rounded-full h-5 w-5 flex items-center justify-center -mr-1 -mt-1" : "text-muted-foreground"
                        }`}>
                          {cell.date.getDate()}
                        </div>

                        {/* Eventos / Badges */}
                        <div className="mt-2 space-y-1 overflow-hidden flex-1 flex flex-col justify-end">
                          {dayAppts.slice(0, 2).map((appt) => (
                            <div
                              key={appt.id}
                              className={`text-[9px] px-1.5 py-0.5 rounded-xs border font-medium truncate leading-tight ${
                                appt.status === "confirmed"
                                  ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                                  : appt.status === "missed"
                                  ? "bg-rose-500/10 text-rose-500 border-rose-500/20"
                                  : appt.status === "cancelled"
                                  ? "bg-slate-500/10 text-slate-400 border-slate-500/20"
                                  : "bg-amber-500/10 text-amber-500 border-amber-500/20"
                              }`}
                            >
                              {new Date(appt.start_time).toLocaleTimeString("pt-BR", {
                                hour: "2-digit",
                                minute: "2-digit"
                              })} - {appt.patient_name}
                            </div>
                          ))}
                          {dayAppts.length > 2 && (
                            <div className="text-[8px] text-center font-bold text-primary bg-primary/10 px-1 py-0.5 rounded-xs border border-primary/20">
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
          <Card className="border-border/30 bg-card/65 backdrop-blur-md p-6 h-full flex flex-col justify-between">
            <div className="space-y-6">
              {/* Header Agenda Diária */}
              <div className="border-b border-border/20 pb-4">
                <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <CalendarDays className="h-4.5 w-4.5 text-primary" />
                  Agenda do Dia
                </h4>
                <p className="text-lg font-extrabold text-foreground mt-1.5">
                  {selectedDate.toLocaleDateString("pt-BR", {
                    weekday: "long",
                    day: "numeric",
                    month: "long"
                  })}
                </p>
              </div>

              {/* Lista de Sessões do Dia */}
              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-1">
                {selectedDayAppointments.length === 0 ? (
                  <div className="py-12 text-center text-muted-foreground space-y-3">
                    <Clock className="h-8 w-8 text-muted-foreground/30 mx-auto" />
                    <p className="text-xs">Nenhuma consulta agendada para este dia.</p>
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
                        className="p-3.5 bg-secondary/15 border border-border/30 hover:border-primary/30 rounded-xl transition-all relative overflow-hidden group"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div className="space-y-1">
                            <span className="text-xs font-bold text-primary block">
                              {startStr} - {endStr}
                            </span>
                            <span className="text-sm font-extrabold text-foreground block">
                              {appt.patient_name}
                            </span>
                            <span className="text-[10px] text-muted-foreground block">
                              Dr. {appt.therapist_name}
                            </span>
                          </div>
                          
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold border capitalize shrink-0 ${getStatusColor(appt.status)}`}>
                            {appt.status_display}
                          </span>
                        </div>

                        {/* Botão de Ver Detalhes */}
                        <div className="flex gap-2 justify-end mt-3 border-t border-border/20 pt-2 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => openAppointmentDetails(appt)}
                            className="h-7 w-7 text-muted-foreground hover:text-foreground cursor-pointer"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {appt.status === "scheduled" && (
                            <>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => updateStatus(appt.id, "confirmed")}
                                className="h-7 w-7 text-emerald-500 hover:bg-emerald-500/10 cursor-pointer"
                                title="Confirmar"
                              >
                                <CheckCircle className="h-4 w-4" />
                              </Button>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => {
                                  setSelectedAppointment({ ...appt, notes: "", cancellation_reason: "" });
                                  setIsCancelModalOpen(true);
                                }}
                                className="h-7 w-7 text-rose-500 hover:bg-rose-500/10 cursor-pointer"
                                title="Cancelar"
                              >
                                <XCircle className="h-4 w-4" />
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

            {/* Ação Rápida inferior */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setNewApptForm(prev => ({
                  ...prev,
                  date: selectedDate.toISOString().split("T")[0],
                }));
                setIsNewModalOpen(true);
              }}
              className="border-dashed border-border hover:bg-secondary/40 text-foreground w-full mt-4 flex items-center justify-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
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
        <form onSubmit={handleCreateAppointment} className="space-y-4">
          {/* Paciente */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-muted-foreground flex items-center gap-1.5">
              <User className="h-4 w-4 text-primary" /> Paciente *
            </label>
            <select
              value={newApptForm.patientId}
              onChange={(e) => setNewApptForm({ ...newApptForm, patientId: e.target.value })}
              required
              className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
            >
              <option value="">Selecione o paciente ativo...</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.full_name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Data */}
            <Input
              label="Data da Consulta *"
              type="date"
              value={newApptForm.date}
              onChange={(e) => setNewApptForm({ ...newApptForm, date: e.target.value })}
              required
              className="bg-secondary/20"
            />

            {/* Duração */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground">Duração (minutos)</label>
              <select
                value={newApptForm.duration}
                onChange={(e) => setNewApptForm({ ...newApptForm, duration: Number(e.target.value) })}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
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
          <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-primary flex items-center gap-1.5">
                <Clock className="h-4.5 w-4.5" /> Verificar Horários Livres (Sem conflitos)
              </span>
              <label className="relative inline-flex items-center cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={newApptForm.useTimeSlots}
                  onChange={(e) => setNewApptForm({ ...newApptForm, useTimeSlots: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-border/40 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            {newApptForm.useTimeSlots ? (
              <div className="space-y-2">
                {loadingSlots ? (
                  <div className="text-center py-4 flex items-center justify-center gap-2">
                    <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs text-muted-foreground animate-pulse">Buscando slots do terapeuta...</span>
                  </div>
                ) : availableSlots.length === 0 ? (
                  <div className="text-xs text-muted-foreground p-3 bg-secondary/20 rounded-lg text-center flex items-center gap-2 justify-center border border-border/30">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    Nenhum slot disponível configurado para este dia da semana.
                  </div>
                ) : (
                  <select
                    value={newApptForm.selectedSlot}
                    onChange={(e) => setNewApptForm({ ...newApptForm, selectedSlot: e.target.value })}
                    className="w-full h-11 bg-card border border-border rounded-lg px-3.5 text-sm focus:outline-hidden focus:border-primary"
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
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-in">
                <Input
                  label="Início Manual"
                  type="time"
                  value={newApptForm.manualStart}
                  onChange={(e) => setNewApptForm({ ...newApptForm, manualStart: e.target.value })}
                  className="bg-card"
                />
                <Input
                  label="Término Manual"
                  type="time"
                  value={newApptForm.manualEnd}
                  onChange={(e) => setNewApptForm({ ...newApptForm, manualEnd: e.target.value })}
                  className="bg-card"
                />
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Valor da Sessão */}
            <Input
              label="Valor da Sessão (R$)"
              type="number"
              step="0.01"
              value={newApptForm.sessionValue}
              onChange={(e) => setNewApptForm({ ...newApptForm, sessionValue: e.target.value })}
              required
              leftIcon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
              className="bg-secondary/20"
            />

            {/* Recorrência */}
            <div className="flex flex-col justify-end pb-3">
              <label className="flex items-center gap-2 text-sm font-semibold text-muted-foreground select-none cursor-pointer">
                <input
                  type="checkbox"
                  checked={newApptForm.isRecurring}
                  onChange={(e) => setNewApptForm({ ...newApptForm, isRecurring: e.target.checked })}
                  className="rounded-sm bg-secondary border-border focus:ring-primary text-primary"
                />
                <span>Consulta Recorrente?</span>
              </label>
            </div>
          </div>

          {/* Regra de recorrência (se marcado) */}
          {newApptForm.isRecurring && (
            <div className="flex flex-col gap-1.5 p-4 rounded-xl border border-indigo-500/20 bg-indigo-500/5 animate-scale-in">
              <label className="text-sm font-semibold text-muted-foreground">Frequência da Recorrência</label>
              <select
                value={newApptForm.recurrenceRule}
                onChange={(e) => setNewApptForm({ ...newApptForm, recurrenceRule: e.target.value })}
                className="w-full h-11 bg-card border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                <option value="WEEKLY">Semanal (Gera 4 sessões consecutivas)</option>
                <option value="BIWEEKLY">Quinzenal (Gera 4 sessões consecutivas)</option>
                <option value="MONTHLY">Mensal (Gera 4 sessões consecutivas)</option>
              </select>
            </div>
          )}

          {/* Notas */}
          <Textarea
            label="Observações do Agendamento (opcional)"
            placeholder="Alguma nota rápida sobre esta sessão..."
            value={newApptForm.notes}
            onChange={(e) => setNewApptForm({ ...newApptForm, notes: e.target.value })}
            className="bg-secondary/20 min-h-[80px]"
          />

          {/* Ações */}
          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsNewModalOpen(false)}
              className="border-border text-foreground px-5"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={submittingAppt}
              className="text-white font-semibold px-5"
            >
              Confirmar Agendamento
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL: DETALHES DE CONSULTA */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title="Detalhes do Agendamento"
        description="Ficha detalhada do horário agendado e controle de quitação financeira."
        className="max-w-md"
      >
        {loadingDetail ? (
          <div className="py-8 text-center flex flex-col items-center gap-3">
            <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-muted-foreground">Carregando detalhes...</span>
          </div>
        ) : selectedAppointment ? (
          <div className="space-y-5">
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-extrabold text-lg text-foreground">{selectedAppointment.patient_name}</h4>
                  <p className="text-xs text-muted-foreground">Dr(a). {selectedAppointment.therapist_name}</p>
                </div>
                <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold border capitalize ${getStatusColor(selectedAppointment.status)}`}>
                  {selectedAppointment.status_display}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 border-t border-b border-border/20 py-4">
                <div className="space-y-0.5">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase">Horário</p>
                  <p className="text-sm font-semibold flex items-center gap-1">
                    <Clock className="h-4 w-4 text-primary shrink-0" />
                    <span>
                      {new Date(selectedAppointment.start_time).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit"
                      })} - {new Date(selectedAppointment.end_time).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit"
                      })}
                    </span>
                  </p>
                </div>

                <div className="space-y-0.5">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase">Duração</p>
                  <p className="text-sm font-semibold">{selectedAppointment.duration_display}</p>
                </div>

                <div className="space-y-0.5">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase">Valor da Sessão</p>
                  <p className="text-sm font-semibold text-emerald-500 font-mono">
                    R$ {parseFloat(selectedAppointment.session_value).toFixed(2)}
                  </p>
                </div>

                <div className="space-y-0.5">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase">Recorrente</p>
                  <p className="text-sm font-semibold">{selectedAppointment.is_recurring ? `Sim (${selectedAppointment.recurrence_rule})` : "Não"}</p>
                </div>
              </div>

              {selectedAppointment.notes && (
                <div className="space-y-1">
                  <p className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1">
                    <FileText className="h-3.5 w-3.5" /> Observações
                  </p>
                  <p className="text-sm text-foreground bg-secondary/20 p-3 rounded-lg border border-border/20">
                    {selectedAppointment.notes}
                  </p>
                </div>
              )}

              {selectedAppointment.status === "cancelled" && selectedAppointment.cancellation_reason && (
                <div className="space-y-1 p-3.5 rounded-lg bg-rose-500/5 border border-rose-500/10">
                  <p className="text-xs font-bold text-rose-500 uppercase flex items-center gap-1">
                    <AlertCircle className="h-3.5 w-3.5" /> Motivo do Cancelamento
                  </p>
                  <p className="text-sm text-rose-300 font-medium">
                    {selectedAppointment.cancellation_reason}
                  </p>
                </div>
              )}
            </div>

            {/* Ações */}
            <div className="flex gap-2 pt-4 border-t border-border/40 justify-end">
              {selectedAppointment.status === "scheduled" && (
                <>
                  <Button
                    size="sm"
                    variant="glass"
                    onClick={() => updateStatus(selectedAppointment.id, "confirmed")}
                    className="border-emerald-500/20 hover:bg-emerald-500/10 text-emerald-500 text-xs font-bold"
                  >
                    Confirmar Presença
                  </Button>
                  <Button
                    size="sm"
                    variant="glass"
                    onClick={() => updateStatus(selectedAppointment.id, "missed")}
                    className="border-rose-500/20 hover:bg-rose-500/10 text-rose-500 text-xs font-bold"
                  >
                    Faltou
                  </Button>
                  <Button
                    size="sm"
                    variant="glass"
                    onClick={() => setIsCancelModalOpen(true)}
                    className="border-slate-500/20 hover:bg-slate-500/10 text-slate-400 text-xs font-bold"
                  >
                    Cancelar Sessão
                  </Button>
                </>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsDetailModalOpen(false)}
                className="border-border text-foreground text-xs"
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
            if (selectedAppointment) {
              updateStatus(selectedAppointment.id, "cancelled", cancellationReason);
            }
          }}
          className="space-y-4"
        >
          <Textarea
            label="Motivo do Cancelamento *"
            placeholder="Ex: Paciente solicitou desmarcação por imprevisto familiar..."
            value={cancellationReason}
            onChange={(e) => setCancellationReason(e.target.value)}
            required
            className="bg-secondary/20 min-h-[100px]"
          />

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsCancelModalOpen(false);
                setCancellationReason("");
              }}
              className="border-border text-foreground"
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
