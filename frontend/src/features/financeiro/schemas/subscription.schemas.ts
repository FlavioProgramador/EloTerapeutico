import { z } from "zod";

export const subscriptionSchema = z.object({
  patient: z.number().int().positive("Selecione um paciente."),
  frequency: z.enum(["weekly", "biweekly", "monthly"]),
  weekday: z.number().int().min(0).max(6),
  appointment_time: z.string().min(1, "Informe o horário."),
  first_appointment_date: z.string().min(1, "Informe a primeira data."),
  duration_minutes: z.number().int().min(15).max(240),
  monthly_amount: z.string().min(1, "Informe o valor.").refine(
    (value) => Number(value.replace(",", ".")) > 0,
    "Informe um valor maior que zero.",
  ),
  due_day: z.number().int().min(1).max(28),
  first_due_date: z.string().optional().or(z.literal("")),
  reminder_days_before: z.number().int().min(0).max(30).optional(),
  preferred_payment_method: z.string().optional(),
  payment_link: z.string().url("Informe um link válido.").optional().or(z.literal("")),
  notes: z.string().max(500).optional(),
});

export type SubscriptionFormData = z.infer<typeof subscriptionSchema>;
