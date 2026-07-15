/**
 * Schemas de validação Zod para agendamentos.
 */

import { z } from "zod";

const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;

export const appointmentSchema = z
  .object({
    patient: z.number().int().min(1, "Selecione um paciente."),
    date: z
      .string()
      .min(1, "Data é obrigatória.")
      .refine((val) => !isNaN(Date.parse(val)), "Data inválida."),
    start_time: z
      .string()
      .min(1, "Horário de início é obrigatório.")
      .regex(timeRegex, "Formato: HH:MM."),
    end_time: z
      .string()
      .min(1, "Horário de término é obrigatório.")
      .regex(timeRegex, "Formato: HH:MM."),
    status: z.enum([
      "scheduled",
      "confirmed",
      "completed",
      "cancelled",
      "missed",
    ]),
    notes: z
      .string()
      .max(1000, "Observações limitadas a 1000 caracteres.")
      .optional()
      .or(z.literal("")),
  })
  .refine(
    (data) => {
      if (data.start_time && data.end_time) {
        return data.start_time < data.end_time;
      }
      return true;
    },
    {
      message: "O horário de término deve ser após o horário de início.",
      path: ["end_time"],
    },
  );

export type AppointmentFormData = z.infer<typeof appointmentSchema>;
