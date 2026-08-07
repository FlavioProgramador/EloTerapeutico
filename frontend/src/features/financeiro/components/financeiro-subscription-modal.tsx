"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useId } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import type { Patient } from "@/types";
import { useCreateMonthlySubscription } from "../hooks/use-financeiro-dashboard";
import {
  subscriptionSchema,
  type SubscriptionFormData,
} from "../schemas/subscription.schemas";

interface Props {
  open: boolean;
  patients: Patient[];
  onClose: () => void;
}
const weekdays = [
  "Segunda-feira",
  "Terça-feira",
  "Quarta-feira",
  "Quinta-feira",
  "Sexta-feira",
  "Sábado",
  "Domingo",
];

export function FinanceiroSubscriptionModal({
  open,
  patients,
  onClose,
}: Props) {
  const baseId = useId();
  const patientSelectId = `${baseId}-patient`;
  const frequencySelectId = `${baseId}-frequency`;
  const weekdaySelectId = `${baseId}-weekday`;

  const mutation = useCreateMonthlySubscription();
  const form = useForm<SubscriptionFormData>({
    resolver: zodResolver(subscriptionSchema),
    defaultValues: {
      frequency: "weekly",
      weekday: 0,
      appointment_time: "09:00",
      duration_minutes: 50,
      monthly_amount: "",
      due_day: 5,
      preferred_payment_method: "uninformed",
      reminder_days_before: 0,
      notes: "",
    },
  });

  useEffect(() => {
    if (open)
      form.reset({
        patient: undefined,
        frequency: "weekly",
        weekday: 0,
        appointment_time: "09:00",
        first_appointment_date: "",
        duration_minutes: 50,
        monthly_amount: "",
        due_day: 5,
        first_due_date: "",
        reminder_days_before: 0,
        preferred_payment_method: "uninformed",
        payment_link: "",
        notes: "",
      });
  }, [open, form]);

  const submit = form.handleSubmit((data) =>
    mutation.mutate(
      {
        ...data,
        monthly_amount: data.monthly_amount.replace(",", "."),
        first_due_date: data.first_due_date || undefined,
        payment_link: data.payment_link || undefined,
      },
      { onSuccess: onClose },
    ),
  );

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Nova mensalidade"
      description="Configure uma assinatura mensal para o paciente."
      className="max-w-xl"
    >
      <form className="space-y-5" onSubmit={submit}>
        <div className="space-y-1.5">
          <label htmlFor={patientSelectId} className="block text-sm font-semibold">
            Paciente *
          </label>
          <select
            id={patientSelectId}
            disabled={mutation.isPending}
            className="flex h-11 w-full rounded-lg border border-input bg-card px-3.5 py-2 text-base shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            {...form.register("patient", { valueAsNumber: true })}
          >
            <option value="">Selecione um paciente</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.full_name}
              </option>
            ))}
          </select>
          {form.formState.errors.patient && (
            <span className="block text-xs text-danger" role="alert">
              {form.formState.errors.patient.message}
            </span>
          )}
        </div>

        <div className="border-t border-border pt-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Configuração do agendamento
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor={frequencySelectId} className="block text-sm font-semibold">
                Frequência
              </label>
              <select
                id={frequencySelectId}
                disabled={mutation.isPending}
                className="flex h-11 w-full rounded-lg border border-input bg-card px-3.5 py-2 text-base shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                {...form.register("frequency")}
              >
                <option value="weekly">Semanal</option>
                <option value="biweekly">Quinzenal</option>
                <option value="monthly">Mensal</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label htmlFor={weekdaySelectId} className="block text-sm font-semibold">
                Dia da semana
              </label>
              <select
                id={weekdaySelectId}
                disabled={mutation.isPending}
                className="flex h-11 w-full rounded-lg border border-input bg-card px-3.5 py-2 text-base shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                {...form.register("weekday", { valueAsNumber: true })}
              >
                {weekdays.map((day, index) => (
                  <option key={day} value={index}>
                    {day}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Horário"
              type="time"
              disabled={mutation.isPending}
              {...form.register("appointment_time")}
            />
            <Input
              label="Duração (minutos)"
              type="number"
              min={15}
              disabled={mutation.isPending}
              {...form.register("duration_minutes", { valueAsNumber: true })}
            />
            <Input
              label="Primeiro agendamento"
              type="date"
              disabled={mutation.isPending}
              error={form.formState.errors.first_appointment_date?.message}
              {...form.register("first_appointment_date")}
            />
          </div>
        </div>

        <div className="border-t border-border pt-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Configuração financeira
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Valor da mensalidade"
              placeholder="0,00"
              inputMode="decimal"
              disabled={mutation.isPending}
              error={form.formState.errors.monthly_amount?.message}
              {...form.register("monthly_amount")}
            />
            <Input
              label="Dia do vencimento"
              type="number"
              min={1}
              max={28}
              disabled={mutation.isPending}
              {...form.register("due_day", { valueAsNumber: true })}
            />
            <Input
              label="Vencimento da 1ª cobrança"
              type="date"
              disabled={mutation.isPending}
              {...form.register("first_due_date")}
            />
            <Input
              label="Lembrete (dias antes)"
              type="number"
              min={0}
              max={30}
              disabled={mutation.isPending}
              {...form.register("reminder_days_before", {
                valueAsNumber: true,
              })}
            />
          </div>
          <div className="mt-4">
            <Input
              label="Link de pagamento (opcional)"
              placeholder="https://..."
              disabled={mutation.isPending}
              error={form.formState.errors.payment_link?.message}
              {...form.register("payment_link")}
            />
          </div>
        </div>

        <Textarea
          label="Observações"
          placeholder="Informações adicionais"
          disabled={mutation.isPending}
          {...form.register("notes")}
        />
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={mutation.isPending}
          >
            Cancelar
          </Button>
          <Button type="submit" isLoading={mutation.isPending}>
            Criar mensalidade
          </Button>
        </div>
      </form>
    </Modal>
  );
}
