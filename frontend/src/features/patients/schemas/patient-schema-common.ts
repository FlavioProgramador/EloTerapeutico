import { z } from "zod";

export const optionalText = z.string().optional().or(z.literal(""));
export const optionalPhone = z
  .string()
  .regex(/^\(\d{2}\)\s\d{4,5}-\d{4}$/, "Formato: (99) 99999-9999.")
  .optional()
  .or(z.literal(""));

export function isValidCpf(value: string) {
  const cpf = value.replace(/\D/g, "");
  if (cpf.length !== 11 || /^(\d)\1+$/.test(cpf)) return false;
  const digit = (length: number) => {
    let sum = 0;
    for (let index = 0; index < length; index += 1) {
      sum += Number(cpf[index]) * (length + 1 - index);
    }
    const result = (sum * 10) % 11;
    return result === 10 ? 0 : result;
  };
  return digit(9) === Number(cpf[9]) && digit(10) === Number(cpf[10]);
}

export const optionalCpf = optionalText.refine(
  (value) => !value || isValidCpf(value),
  "Informe um CPF válido.",
);
