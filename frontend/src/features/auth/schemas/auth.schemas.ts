/**
 * Schemas de validação Zod para autenticação.
 * Mensagens em português, validações rigorosas mas com bom UX.
 */

import { z } from "zod";

// ─── Login ─────────────────────────────────────────────────────────────────────

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "E-mail é obrigatório.")
    .email("Informe um e-mail válido."),
  password: z
    .string()
    .min(1, "Senha é obrigatória.")
    .min(8, "A senha deve ter pelo menos 8 caracteres."),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// ─── Registro ─────────────────────────────────────────────────────────────────

export const registerSchema = z
  .object({
    full_name: z
      .string()
      .min(1, "Nome completo é obrigatório.")
      .min(3, "O nome deve ter pelo menos 3 caracteres.")
      .max(150, "O nome não pode ter mais de 150 caracteres."),
    email: z
      .string()
      .min(1, "E-mail é obrigatório.")
      .email("Informe um e-mail válido."),
    password: z
      .string()
      .min(8, "A senha deve ter pelo menos 8 caracteres.")
      .regex(/[A-Z]/, "A senha deve conter pelo menos uma letra maiúscula.")
      .regex(/[0-9]/, "A senha deve conter pelo menos um número."),
    confirm_password: z.string().min(1, "Confirme sua senha."),
    role: z.enum(["therapist", "secretary", "admin"]).default("therapist"),
    crp: z.string().optional(),
    specialty: z.string().optional(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "As senhas não coincidem.",
    path: ["confirm_password"],
  });

export type RegisterFormData = z.input<typeof registerSchema>;

