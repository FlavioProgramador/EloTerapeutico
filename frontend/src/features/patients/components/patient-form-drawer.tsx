"use client";

import { usePatientFormState } from "../hooks/use-patient-form-state";
import { usePatientFormSubmit } from "../hooks/use-patient-form-submit";
import { DOCUMENT_FIELD_CONFIG } from "./patient-form-admin-config";
import { ATTENDANCE_FIELD_CONFIG } from "./patient-form-attendance-config";
import { applyPatientFormApiErrors } from "./patient-form-api-errors";
import { PatientFormAssignment } from "./patient-form-assignment";
import { PatientFormDrawerShell } from "./patient-form-drawer-shell";
import { PatientFormFieldGrid } from "./patient-form-field-grid";
import { PERSONAL_FIELD_CONFIG } from "./patient-form-personal-config";
import { PatientFormSupplementary } from "./patient-form-supplementary";
import { PatientPhotoField } from "./patient-photo-field";

interface Props {
  open: boolean;
  patientId?: number;
  onClose: () => void;
  onSaved: (patientId: number) => void;
}

export function PatientFormDrawer(props: Props) {
  const state = usePatientFormState(
    props.open,
    props.patientId,
    false,
    props.onClose,
  );
  const submit = usePatientFormSubmit({
    patientId: props.patientId,
    form: state.form,
    onClose: props.onClose,
    onSaved: props.onSaved,
    onError: (error) => applyPatientFormApiErrors(error, state.form),
  });
  const close = () => {
    if (!submit.pending) state.close();
  };

  return (
    <PatientFormDrawerShell
      open={props.open}
      title={submit.editing ? "Editar Paciente" : "Novo Paciente"}
      dirty={state.form.formState.isDirty}
      submitting={submit.pending}
      submitLabel={
        submit.editing ? "Salvar Alterações" : "Cadastrar Paciente"
      }
      onClose={close}
      onSubmit={submit.submit}
    >
      {submit.editing && state.patientQuery.isLoading ? (
        <div className="space-y-4" aria-busy="true">
          {Array.from({ length: 5 }).map((_, index) => (
            <div
              key={index}
              className="h-32 animate-pulse rounded-xl bg-secondary"
            />
          ))}
        </div>
      ) : (
        <form onSubmit={submit.submit} className="space-y-4" noValidate>
          <section className="rounded-xl border border-border bg-card/40 p-4">
            <PatientPhotoField
              preview={state.preview}
              current={state.patientQuery.data?.photo ?? null}
              error={state.form.formState.errors.photo?.message?.toString()}
              onChange={state.changePhoto}
              onRemove={state.removePhoto}
            />
          </section>
          <PatientFormFieldGrid
            form={state.form}
            title="Dados Pessoais"
            fields={PERSONAL_FIELD_CONFIG}
          />
          <PatientFormFieldGrid
            form={state.form}
            title="Documentos"
            fields={DOCUMENT_FIELD_CONFIG}
          />
          <PatientFormFieldGrid
            form={state.form}
            title="Atendimento"
            fields={ATTENDANCE_FIELD_CONFIG}
          />
          <PatientFormAssignment
            form={state.form}
            user={state.user}
            professionals={state.professionalsQuery.data ?? []}
          />
          <PatientFormSupplementary
            form={state.form}
            isMinor={state.isMinor}
          />
          <button type="submit" className="sr-only">
            Salvar
          </button>
        </form>
      )}
    </PatientFormDrawerShell>
  );
}
