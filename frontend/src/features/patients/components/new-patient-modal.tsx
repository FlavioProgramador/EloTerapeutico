"use client";

import { PatientFormDrawer } from "./patient-form-drawer";

interface Props {
  open: boolean;
  patientId?: number;
  onClose: () => void;
  onCreated?: (patientId: number) => void;
  onSaved?: (patientId: number) => void;
}

export function NewPatientModal({
  open,
  patientId,
  onClose,
  onCreated,
  onSaved,
}: Props) {
  return (
    <PatientFormDrawer
      open={open}
      patientId={patientId}
      onClose={onClose}
      onSaved={(id) => {
        onSaved?.(id);
        if (!patientId) onCreated?.(id);
      }}
    />
  );
}

export { PatientFormDrawer };
