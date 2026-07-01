import { z } from "zod";

import { patientAttendanceFields } from "./patient-schema-attendance";
import { patientContactFields } from "./patient-schema-contact";
import { patientFinancialFields } from "./patient-schema-financial";
import { patientPersonalFields } from "./patient-schema-personal";
import { validatePatientRules } from "./patient-schema-rules";

export const patientSchema = z
  .object({
    ...patientPersonalFields,
    ...patientAttendanceFields,
    ...patientContactFields,
    ...patientFinancialFields,
  })
  .superRefine(validatePatientRules);

export type PatientFormData = z.infer<typeof patientSchema>;
