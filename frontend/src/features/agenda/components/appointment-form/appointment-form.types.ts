import type { Dispatch, SetStateAction } from "react";

import type { AppointmentModality, AppointmentType } from "../../types";

export interface AppointmentFormState {
  patient: string;
  therapist: string;
  date: string;
  time: string;
  duration: string;
  modality: AppointmentModality;
  appointmentType: AppointmentType;
  room: string;
  sessionValue: string;
  notes: string;
  reminder: boolean;
  recurring: boolean;
  frequency: "weekly" | "biweekly" | "monthly" | "custom";
  occurrences: string;
  endsOn: string;
  conflictStrategy: "error" | "skip";
}

export type AppointmentFormSetter = Dispatch<
  SetStateAction<AppointmentFormState>
>;
