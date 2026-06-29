/**
 * Schemas de validação Zod para transações financeiras.
 */

import { z } from "zod";

export const transactionSchema = z.object({
  description: z
    .string()
    .min(1, "Descrição é obrigatória.")
    .max(255, "Descrição limitada a 255 caracteres."),
  amount: z
    .string()
    .min(1, "Valor é obrigatório.")
    .refine(
      (val) => !isNaN(parseFloat(val.replace(",", "."))) && parseFloat(val.replace(",", ".")) > 0,
      "Informe um valor válido maior que zero."
    ),
  type: z.enum(["income", "expense"], "Tipo é obrigatório."),
  category: z.enum(["session", "subscription", "material", "refund", "other"], "Categoria é obrigatória."),
  status: z
    .enum(["pending", "paid", "overdue", "cancelled"]),
  due_date: z
    .string()
    .min(1, "Data de vencimento é obrigatória.")
    .refine((val) => !isNaN(Date.parse(val)), "Data inválida."),
  payment_date: z.string().optional().or(z.literal("")),
  payment_method: z
    .enum(["pix", "credit_card", "debit_card", "cash", "bank_transfer", "other"])
    .optional(),
  patient: z.union([z.string(), z.number()]).optional(),
  appointment: z.union([z.string(), z.number()]).optional(),
  notes: z.string().max(500).optional().or(z.literal("")),
});

export type TransactionFormData = z.infer<typeof transactionSchema>;
