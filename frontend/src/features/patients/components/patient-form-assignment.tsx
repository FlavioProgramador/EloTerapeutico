import type { UseFormReturn } from "react-hook-form";

import type { User } from "@/contexts/auth";
import type { PatientFormData } from "../schemas/patient.schemas";
import type { PatientProfessionalOption } from "../types/patient-form.types";

const inputClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/15";

interface Props {
  form: UseFormReturn<PatientFormData>;
  user: User | null;
  professionals: PatientProfessionalOption[];
}

export function PatientFormAssignment({ form, user, professionals }: Props) {
  const {
    register,
    watch,
    formState: { errors },
  } = form;
  const payerType = watch("payer_type");

  return (
    <section className="rounded-xl border border-border bg-card/40 p-4">
      <h3 className="border-b border-border pb-3 text-sm font-semibold">
        Profissionais e lembretes
      </h3>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {payerType === "insurance" && (
          <label className="space-y-1 text-[11px] font-medium sm:col-span-2">
            Nome do convênio
            <input {...register("insurance_name")} className={inputClass} />
            {errors.insurance_name?.message && (
              <span className="block text-[10px] text-destructive">
                {errors.insurance_name.message}
              </span>
            )}
          </label>
        )}
        <label className="space-y-1 text-[11px] font-medium sm:col-span-2">
          Profissional responsável
          {user?.role === "therapist" ? (
            <div className="flex h-10 items-center rounded-md border border-border bg-secondary/30 px-3 text-xs">
              {user.full_name}
            </div>
          ) : (
            <select {...register("therapist")} className={inputClass}>
              <option value="">Selecione um profissional</option>
              {professionals.map((professional) => (
                <option key={professional.id} value={professional.id}>
                  {professional.full_name}
                </option>
              ))}
            </select>
          )}
          {errors.therapist?.message && (
            <span className="block text-[10px] text-destructive">
              {errors.therapist.message}
            </span>
          )}
        </label>
        <label className="flex items-center gap-2 text-xs sm:col-span-2">
          <input type="checkbox" {...register("reminders_enabled")} />
          Lembretes ativados
        </label>
      </div>
    </section>
  );
}
