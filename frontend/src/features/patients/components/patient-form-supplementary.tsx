import type { UseFormReturn } from "react-hook-form";

import type { PatientFormData } from "../schemas/patient.schemas";
import {
  ADDRESS_FIELD_CONFIG,
  EMERGENCY_FIELD_CONFIG,
} from "./patient-form-admin-config";
import { PatientFormFieldGrid } from "./patient-form-field-grid";
import {
  FINANCIAL_FIELD_CONFIG,
  GUARDIAN_FIELD_CONFIG,
} from "./patient-form-financial-config";

const textareaClass =
  "min-h-28 w-full resize-y rounded-md border border-border bg-background px-3 py-3 text-xs text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/15";

export function PatientFormSupplementary({
  form,
  isMinor,
}: {
  form: UseFormReturn<PatientFormData>;
  isMinor: boolean;
}) {
  const { register, watch } = form;
  const reminderRecipient = watch("reminder_recipient");
  const notes = watch("notes") || "";

  return (
    <>
      <PatientFormFieldGrid
        form={form}
        title="Endereço"
        fields={ADDRESS_FIELD_CONFIG}
      />
      <PatientFormFieldGrid
        form={form}
        title="Contato de Emergência"
        fields={EMERGENCY_FIELD_CONFIG}
        attention
      />
      {isMinor && (
        <PatientFormFieldGrid
          form={form}
          title="Responsável Legal"
          fields={GUARDIAN_FIELD_CONFIG}
        />
      )}
      <PatientFormFieldGrid
        form={form}
        title="Responsável Financeiro"
        fields={FINANCIAL_FIELD_CONFIG}
      />
      {["financial_responsible", "both"].includes(reminderRecipient) && (
        <p className="rounded-lg border border-warning/30 bg-warning/5 p-3 text-[11px] text-warning">
          Nome e telefone do responsável são obrigatórios para este destinatário.
        </p>
      )}
      <section className="rounded-xl border border-border bg-card/40 p-4">
        <h3 className="border-b border-border pb-3 text-sm font-semibold">
          Observações
        </h3>
        <textarea
          {...register("notes")}
          className={`${textareaClass} mt-4`}
          placeholder="Observações sobre o paciente..."
        />
        <div className="mt-1 text-right text-[10px] text-muted-foreground">
          {notes.length}/2000
        </div>
        <p className="mt-2 text-[10px] text-muted-foreground">
          Informações clínicas devem ser registradas no prontuário.
        </p>
        <label className="mt-4 flex items-start gap-2 text-xs">
          <input type="checkbox" {...register("consent_terms_accepted")} />
          Confirmo que os consentimentos necessários foram coletados.
        </label>
      </section>
    </>
  );
}
