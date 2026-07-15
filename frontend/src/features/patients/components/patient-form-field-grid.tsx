import type { FieldPath, FieldPathValue, UseFormReturn } from "react-hook-form";

import type { PatientFormData } from "../schemas/patient.schemas";
import {
  formatCep,
  formatCpf,
  formatMoney,
  formatPhone,
} from "./patient-form-formatters";
import type { PatientFieldConfig } from "./patient-form-personal-config";

const inputClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none transition placeholder:text-muted-foreground/70 focus:border-primary focus:ring-2 focus:ring-primary/15";

function applyMask(mask: PatientFieldConfig["mask"], value: string) {
  if (mask === "cpf") return formatCpf(value);
  if (mask === "phone") return formatPhone(value);
  if (mask === "cep") return formatCep(value);
  if (mask === "money") return formatMoney(value);
  return value;
}

export function PatientFormFieldGrid({
  form,
  title,
  fields,
  attention,
}: {
  form: UseFormReturn<PatientFormData>;
  title: string;
  fields: PatientFieldConfig[];
  attention?: boolean;
}) {
  const {
    register,
    setValue,
    formState: { errors },
  } = form;
  const today = new Date().toISOString().split("T")[0];

  return (
    <section
      className={`rounded-xl border p-4 ${
        attention
          ? "border-warning/30 bg-warning/5"
          : "border-border bg-card/40"
      }`}
    >
      <h3 className="border-b border-border pb-3 text-sm font-semibold text-foreground">
        {title}
      </h3>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {fields.map((field) => {
          const name = field.name as FieldPath<PatientFormData>;
          const message = errors[field.name]?.message;
          const error = typeof message === "string" ? message : undefined;
          const className = `${inputClass} ${field.type === "textarea" ? "h-auto min-h-28 py-3" : ""}`;

          return (
            <label
              key={field.name}
              className={`space-y-1 text-[11px] font-medium text-foreground ${
                field.full ? "sm:col-span-2" : ""
              }`}
            >
              <span>{field.label}</span>
              {field.type === "select" ? (
                <select {...register(name)} className={className}>
                  {field.options?.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              ) : field.type === "textarea" ? (
                <textarea {...register(name)} className={className} />
              ) : (
                <input
                  type={field.type ?? "text"}
                  max={field.type === "date" ? today : undefined}
                  inputMode={field.mask ? "numeric" : undefined}
                  {...register(name)}
                  className={className}
                  onChange={
                    field.mask
                      ? (event) =>
                          setValue(
                            name,
                            applyMask(
                              field.mask,
                              event.target.value,
                            ) as FieldPathValue<PatientFormData, typeof name>,
                            { shouldDirty: true, shouldValidate: true },
                          )
                      : undefined
                  }
                />
              )}
              {error && (
                <span
                  className="block text-[10px] font-normal text-destructive"
                  role="alert"
                >
                  {error}
                </span>
              )}
            </label>
          );
        })}
      </div>
    </section>
  );
}
