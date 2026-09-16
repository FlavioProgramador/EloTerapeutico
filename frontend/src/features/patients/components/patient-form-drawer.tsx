"use client";

import { useState, useMemo, useId } from "react";
import { usePatientFormState } from "../hooks/use-patient-form-state";
import { usePatientFormSubmit } from "../hooks/use-patient-form-submit";
import { applyPatientFormApiErrors } from "./patient-form-api-errors";
import { PatientFormDrawerShell } from "./patient-form-drawer-shell";
import { PatientPhotoField } from "./patient-photo-field";
import { AlertTriangle, UserRound, ChevronDown, ChevronUp } from "lucide-react";
import {
  formatCep,
  formatCpf,
  formatMoney,
  formatPhone,
} from "./patient-form-formatters";

interface Props {
  open: boolean;
  patientId?: number;
  onClose: () => void;
  onSaved: (patientId: number) => void;
}

const inputClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none transition placeholder:text-muted-foreground/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";
const selectClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";
const textareaClass =
  "min-h-24 w-full resize-y rounded-md border border-border bg-background px-3 py-3 text-xs text-foreground outline-none transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 placeholder:text-muted-foreground/50 disabled:opacity-50 disabled:cursor-not-allowed";

const UF_OPTIONS = [
  "",
  "AC",
  "AL",
  "AP",
  "AM",
  "BA",
  "CE",
  "DF",
  "ES",
  "GO",
  "MA",
  "MT",
  "MS",
  "MG",
  "PA",
  "PB",
  "PR",
  "PE",
  "PI",
  "RJ",
  "RN",
  "RS",
  "RO",
  "RR",
  "SC",
  "SP",
  "SE",
  "TO",
];

const MARITAL_OPTIONS = [
  ["", "Selecione..."],
  ["single", "Solteiro(a)"],
  ["married", "Casado(a)"],
  ["divorced", "Divorciado(a)"],
  ["widowed", "Viúvo(a)"],
  ["other", "Outro"],
];

const GENDER_OPTIONS = [
  ["N", "Prefiro não informar"],
  ["F", "Feminino"],
  ["M", "Masculino"],
  ["O", "Outro"],
];

const PATIENT_MARITAL_OPTIONS = [
  ["", "Não informado"],
  ["single", "Solteiro(a)"],
  ["married", "Casado(a)"],
  ["divorced", "Divorciado(a)"],
  ["widowed", "Viúvo(a)"],
  ["other", "Outro"],
];

function FormField({
  label,
  error,
  id,
  className = "",
  children,
}: {
  label: string;
  error?: string;
  id?: string;
  className?: string;
  children: React.ReactNode;
}) {
  const errorId = id ? `${id}-error` : undefined;
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <label
        htmlFor={id}
        className="text-[11px] font-semibold text-foreground/80"
      >
        {label}
      </label>
      {children}
      {error && (
        <span
          id={errorId}
          className="text-[10px] font-normal text-destructive mt-0.5"
          role="alert"
        >
          {error}
        </span>
      )}
    </div>
  );
}

export function PatientFormDrawer(props: Props) {
  const state = usePatientFormState(
    props.open,
    props.patientId,
    false,
    props.onClose,
  );
  const baseId = useId();
  const submit = usePatientFormSubmit({
    patientId: props.patientId,
    form: state.form,
    onClose: props.onClose,
    onSaved: props.onSaved,
    onError: (error) => applyPatientFormApiErrors(error, state.form),
  });

  const [isAddingTherapist, setIsAddingTherapist] = useState(false);
  const [showAdditionalFields, setShowAdditionalFields] = useState(false);

  const {
    register,
    setValue,
    watch,
    formState: { errors },
  } = state.form;

  const watchNotes = watch("notes") || "";
  const watchPayerType = watch("payer_type");
  const watchTherapist = watch("therapist");

  const today = useMemo(() => new Date().toISOString().split("T")[0], []);

  const selectedProfessional = useMemo(() => {
    if (!watchTherapist) return null;
    return (state.professionalsQuery.data ?? []).find(
      (p) => String(p.id) === String(watchTherapist),
    );
  }, [watchTherapist, state.professionalsQuery.data]);

  const therapistName = useMemo(() => {
    if (selectedProfessional) return selectedProfessional.full_name;
    if (state.user?.role === "therapist") return state.user.full_name;
    return "";
  }, [selectedProfessional, state.user]);

  const close = () => {
    if (!submit.pending) state.close();
  };

  return (
    <PatientFormDrawerShell
      open={props.open}
      title={submit.editing ? "Editar Paciente" : "Novo Paciente"}
      dirty={state.form.formState.isDirty}
      submitting={submit.pending}
      submitLabel={submit.editing ? "Salvar Alterações" : "Cadastrar Paciente"}
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
        <form onSubmit={submit.submit} className="space-y-6 pb-8" noValidate>
          {/* 1. DADOS PESSOAIS */}
          <div className="space-y-4">
            <div className="border-b border-border/60 pb-1.5">
              <h3 className="text-sm font-bold text-foreground/90">
                Dados Pessoais
              </h3>
            </div>

            <PatientPhotoField
              preview={state.preview}
              current={state.patientQuery.data?.photo ?? null}
              error={state.form.formState.errors.photo?.message?.toString()}
              onChange={state.changePhoto}
              onRemove={state.removePhoto}
              id={`${baseId}-photo`}
            />

            <FormField
              label="Nome completo *"
              error={errors.full_name?.message}
              id={`${baseId}-full-name`}
              className="w-full"
            >
              <input
                id={`${baseId}-full-name`}
                type="text"
                placeholder="Nome do paciente"
                aria-describedby={
                  errors.full_name ? `${baseId}-full-name-error` : undefined
                }
                aria-invalid={!!errors.full_name}
                disabled={submit.pending}
                {...register("full_name")}
                className={inputClass}
              />
            </FormField>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="E-mail"
                error={errors.email?.message}
                id={`${baseId}-email`}
              >
                <input
                  id={`${baseId}-email`}
                  type="email"
                  placeholder="email@exemplo.com"
                  aria-describedby={
                    errors.email ? `${baseId}-email-error` : undefined
                  }
                  aria-invalid={!!errors.email}
                  disabled={submit.pending}
                  {...register("email")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Telefone"
                error={errors.phone?.message}
                id={`${baseId}-phone`}
              >
                <input
                  id={`${baseId}-phone`}
                  type="text"
                  placeholder="(11) 99999-9999 ou +55 21 99999-9999"
                  aria-describedby={
                    errors.phone ? `${baseId}-phone-error` : undefined
                  }
                  aria-invalid={!!errors.phone}
                  disabled={submit.pending}
                  {...register("phone")}
                  className={inputClass}
                  onChange={(e) =>
                    setValue("phone", formatPhone(e.target.value), {
                      shouldDirty: true,
                      shouldValidate: true,
                    })
                  }
                />
              </FormField>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Data de Nascimento *"
                error={errors.birth_date?.message}
                id={`${baseId}-birth-date`}
              >
                <input
                  id={`${baseId}-birth-date`}
                  type="date"
                  max={today}
                  aria-describedby={
                    errors.birth_date ? `${baseId}-birth-date-error` : undefined
                  }
                  aria-invalid={!!errors.birth_date}
                  disabled={submit.pending}
                  {...register("birth_date")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Início dos Atendimentos"
                error={errors.treatment_start_date?.message}
                id={`${baseId}-treatment-start-date`}
              >
                <input
                  id={`${baseId}-treatment-start-date`}
                  type="date"
                  max={today}
                  aria-describedby={
                    errors.treatment_start_date
                      ? `${baseId}-treatment-start-date-error`
                      : undefined
                  }
                  aria-invalid={!!errors.treatment_start_date}
                  disabled={submit.pending}
                  {...register("treatment_start_date")}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="CPF *"
                error={errors.cpf?.message}
                id={`${baseId}-cpf`}
              >
                <input
                  id={`${baseId}-cpf`}
                  type="text"
                  placeholder="000.000.000-00"
                  aria-describedby={
                    errors.cpf ? `${baseId}-cpf-error` : undefined
                  }
                  aria-invalid={!!errors.cpf}
                  disabled={submit.pending}
                  {...register("cpf")}
                  className={inputClass}
                  onChange={(e) =>
                    setValue("cpf", formatCpf(e.target.value), {
                      shouldDirty: true,
                      shouldValidate: true,
                    })
                  }
                />
              </FormField>

              <FormField
                label="RG"
                error={errors.rg?.message}
                id={`${baseId}-rg`}
              >
                <input
                  id={`${baseId}-rg`}
                  type="text"
                  placeholder="00.000.000-0"
                  aria-describedby={
                    errors.rg ? `${baseId}-rg-error` : undefined
                  }
                  aria-invalid={!!errors.rg}
                  disabled={submit.pending}
                  {...register("rg")}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Profissão"
                error={errors.profession?.message}
                id={`${baseId}-profession`}
              >
                <input
                  id={`${baseId}-profession`}
                  type="text"
                  placeholder="Profissão"
                  aria-describedby={
                    errors.profession ? `${baseId}-profession-error` : undefined
                  }
                  aria-invalid={!!errors.profession}
                  disabled={submit.pending}
                  {...register("profession")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Rede Social"
                error={errors.social_network?.message}
                id={`${baseId}-social-network`}
              >
                <input
                  id={`${baseId}-social-network`}
                  type="text"
                  placeholder="@instagram"
                  aria-describedby={
                    errors.social_network
                      ? `${baseId}-social-network-error`
                      : undefined
                  }
                  aria-invalid={!!errors.social_network}
                  disabled={submit.pending}
                  {...register("social_network")}
                  className={inputClass}
                />
              </FormField>
            </div>
          </div>

          {/* 2. ATENDIMENTO */}
          <div className="space-y-4">
            <div className="border-b border-border/60 pb-1.5">
              <h3 className="text-sm font-bold text-foreground/90">
                Atendimento
              </h3>
            </div>

            <FormField
              label="Convênio"
              error={errors.payer_type?.message}
              id={`${baseId}-payer-type`}
            >
              <select
                id={`${baseId}-payer-type`}
                aria-describedby={
                  errors.payer_type ? `${baseId}-payer-type-error` : undefined
                }
                aria-invalid={!!errors.payer_type}
                disabled={submit.pending}
                {...register("payer_type")}
                className={selectClass}
              >
                <option value="private">Particular</option>
                <option value="insurance">Convênio</option>
              </select>
            </FormField>

            {watchPayerType === "insurance" && (
              <FormField
                label="Nome do convênio *"
                error={errors.insurance_name?.message}
                id={`${baseId}-insurance-name`}
              >
                <input
                  id={`${baseId}-insurance-name`}
                  type="text"
                  placeholder="Nome do convênio"
                  aria-describedby={
                    errors.insurance_name
                      ? `${baseId}-insurance-name-error`
                      : undefined
                  }
                  aria-invalid={!!errors.insurance_name}
                  disabled={submit.pending}
                  {...register("insurance_name")}
                  className={inputClass}
                />
              </FormField>
            )}

            <FormField
              label="Valor do Atendimento (R$)"
              error={errors.session_value?.message}
              id={`${baseId}-session-value`}
            >
              <input
                id={`${baseId}-session-value`}
                type="text"
                placeholder="0,00"
                aria-describedby={
                  errors.session_value
                    ? `${baseId}-session-value-error`
                    : undefined
                }
                aria-invalid={!!errors.session_value}
                disabled={submit.pending}
                {...register("session_value")}
                className={inputClass}
                onChange={(e) =>
                  setValue("session_value", formatMoney(e.target.value), {
                    shouldDirty: true,
                    shouldValidate: true,
                  })
                }
              />
            </FormField>

            <FormField
              label="Destinatário dos Lembretes via WhatsApp"
              error={errors.reminder_recipient?.message}
              id={`${baseId}-reminder-recipient`}
            >
              <select
                id={`${baseId}-reminder-recipient`}
                aria-describedby={
                  errors.reminder_recipient
                    ? `${baseId}-reminder-recipient-error`
                    : undefined
                }
                aria-invalid={!!errors.reminder_recipient}
                disabled={submit.pending}
                {...register("reminder_recipient")}
                className={selectClass}
              >
                <option value="patient">Paciente</option>
                <option value="financial_responsible">
                  Responsável financeiro
                </option>
                <option value="both">Ambos</option>
                <option value="none">Não enviar</option>
              </select>
            </FormField>

            {/* Profissionais Responsáveis assignment */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-foreground/80">
                Profissionais Responsáveis
              </span>
              {watchTherapist || state.user?.role === "therapist" ? (
                <div className="flex items-center justify-between rounded-lg border border-border/80 bg-secondary/15 p-3">
                  <div className="flex items-center gap-3">
                    <div className="grid h-8 w-8 place-items-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {therapistName
                        ? therapistName.charAt(0).toUpperCase()
                        : "?"}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-foreground">
                        {therapistName || "Carregando..."}
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        Profissional responsável
                      </div>
                    </div>
                  </div>
                  {state.user?.role !== "therapist" && (
                    <button
                      type="button"
                      disabled={submit.pending}
                      onClick={() => {
                        setValue("therapist", "", { shouldDirty: true });
                        setIsAddingTherapist(true);
                      }}
                      className="text-[11px] font-medium text-destructive hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 rounded px-1 disabled:opacity-50 disabled:pointer-events-none"
                    >
                      Remover
                    </button>
                  )}
                </div>
              ) : isAddingTherapist ? (
                <div className="flex items-center gap-2">
                  <select
                    value={watchTherapist || ""}
                    disabled={submit.pending}
                    onChange={(e) => {
                      setValue("therapist", e.target.value, {
                        shouldDirty: true,
                        shouldValidate: true,
                      });
                      setIsAddingTherapist(false);
                    }}
                    className={selectClass}
                  >
                    <option value="">Selecione um profissional...</option>
                    {(state.professionalsQuery.data ?? []).map((p) => (
                      <option key={p.id} value={String(p.id)}>
                        {p.full_name}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    disabled={submit.pending}
                    onClick={() => setIsAddingTherapist(false)}
                    className="text-xs text-muted-foreground hover:underline px-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 rounded disabled:opacity-50 disabled:pointer-events-none"
                  >
                    Cancelar
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground/60">
                    Nenhum profissional atribuído.
                  </p>
                  <button
                    type="button"
                    disabled={submit.pending}
                    onClick={() => setIsAddingTherapist(true)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border/80 bg-secondary/20 px-3 py-1.5 text-xs font-semibold text-foreground/80 hover:bg-secondary/40 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none"
                  >
                    <UserRound className="h-3.5 w-3.5 text-muted-foreground/80" aria-hidden="true" />{" "}
                    Adicionar
                  </button>
                </div>
              )}
              {errors.therapist?.message && (
                <span className="block text-[10px] text-destructive mt-0.5">
                  {errors.therapist.message}
                </span>
              )}
            </div>
          </div>

          {/* 3. ENDEREÇO */}
          <div className="space-y-4">
            <div className="border-b border-border/60 pb-1.5">
              <h3 className="text-sm font-bold text-foreground/90">Endereço</h3>
            </div>

            <FormField
              label="CEP"
              error={errors.address_zip_code?.message}
              id={`${baseId}-address-zip-code`}
              className="w-1/2 pr-1.5"
            >
              <input
                id={`${baseId}-address-zip-code`}
                type="text"
                placeholder="00000-000"
                aria-describedby={
                  errors.address_zip_code
                    ? `${baseId}-address-zip-code-error`
                    : undefined
                }
                aria-invalid={!!errors.address_zip_code}
                disabled={submit.pending}
                {...register("address_zip_code")}
                className={inputClass}
                onChange={(e) =>
                  setValue("address_zip_code", formatCep(e.target.value), {
                    shouldDirty: true,
                    shouldValidate: true,
                  })
                }
              />
            </FormField>

            <div className="flex gap-3">
              <FormField
                label="Rua/Avenida"
                error={errors.address_street?.message}
                id={`${baseId}-address-street`}
                className="flex-[3]"
              >
                <input
                  id={`${baseId}-address-street`}
                  type="text"
                  placeholder="Nome da rua"
                  aria-describedby={
                    errors.address_street
                      ? `${baseId}-address-street-error`
                      : undefined
                  }
                  aria-invalid={!!errors.address_street}
                  disabled={submit.pending}
                  {...register("address_street")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Número"
                error={errors.address_number?.message}
                id={`${baseId}-address-number`}
                className="flex-[1]"
              >
                <input
                  id={`${baseId}-address-number`}
                  type="text"
                  placeholder="123"
                  aria-describedby={
                    errors.address_number
                      ? `${baseId}-address-number-error`
                      : undefined
                  }
                  aria-invalid={!!errors.address_number}
                  disabled={submit.pending}
                  {...register("address_number")}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Complemento"
                error={errors.address_complement?.message}
                id={`${baseId}-address-complement`}
              >
                <input
                  id={`${baseId}-address-complement`}
                  type="text"
                  placeholder="Apto, Bloco..."
                  aria-describedby={
                    errors.address_complement
                      ? `${baseId}-address-complement-error`
                      : undefined
                  }
                  aria-invalid={!!errors.address_complement}
                  disabled={submit.pending}
                  {...register("address_complement")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Bairro"
                error={errors.address_neighborhood?.message}
                id={`${baseId}-address-neighborhood`}
              >
                <input
                  id={`${baseId}-address-neighborhood`}
                  type="text"
                  placeholder="Nome do bairro"
                  aria-describedby={
                    errors.address_neighborhood
                      ? `${baseId}-address-neighborhood-error`
                      : undefined
                  }
                  aria-invalid={!!errors.address_neighborhood}
                  disabled={submit.pending}
                  {...register("address_neighborhood")}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Cidade"
                error={errors.address_city?.message}
                id={`${baseId}-address-city`}
              >
                <input
                  id={`${baseId}-address-city`}
                  type="text"
                  placeholder="Cidade"
                  aria-describedby={
                    errors.address_city
                      ? `${baseId}-address-city-error`
                      : undefined
                  }
                  aria-invalid={!!errors.address_city}
                  disabled={submit.pending}
                  {...register("address_city")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Estado"
                error={errors.address_state?.message}
                id={`${baseId}-address-state`}
              >
                <select
                  id={`${baseId}-address-state`}
                  aria-describedby={
                    errors.address_state
                      ? `${baseId}-address-state-error`
                      : undefined
                  }
                  aria-invalid={!!errors.address_state}
                  disabled={submit.pending}
                  {...register("address_state")}
                  className={selectClass}
                >
                  <option value="">UF</option>
                  {UF_OPTIONS.filter(Boolean).map((uf) => (
                    <option key={uf} value={uf}>
                      {uf}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>
          </div>

          {/* 4. CONTATO DE EMERGÊNCIA (Alerta amarelo) */}
          <div className="rounded-xl border border-amber-500/25 bg-amber-500/5 p-4 space-y-4 mt-6">
            <div className="flex items-center gap-1.5 text-amber-500 text-xs font-bold">
              <AlertTriangle className="h-4 w-4" aria-hidden="true" />
              <span>Contato de Emergência</span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Nome do Contato"
                error={errors.emergency_contact_name?.message}
                id={`${baseId}-emergency-contact-name`}
              >
                <input
                  id={`${baseId}-emergency-contact-name`}
                  type="text"
                  placeholder="Nome do contato de emergência"
                  aria-describedby={
                    errors.emergency_contact_name
                      ? `${baseId}-emergency-contact-name-error`
                      : undefined
                  }
                  aria-invalid={!!errors.emergency_contact_name}
                  disabled={submit.pending}
                  {...register("emergency_contact_name")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Telefone de Emergência"
                error={errors.emergency_contact_phone?.message}
                id={`${baseId}-emergency-contact-phone`}
              >
                <input
                  id={`${baseId}-emergency-contact-phone`}
                  type="text"
                  placeholder="(11) 99999-9999 ou +55 21 99999-9999"
                  aria-describedby={
                    errors.emergency_contact_phone
                      ? `${baseId}-emergency-contact-phone-error`
                      : undefined
                  }
                  aria-invalid={!!errors.emergency_contact_phone}
                  disabled={submit.pending}
                  {...register("emergency_contact_phone")}
                  className={inputClass}
                  onChange={(e) =>
                    setValue(
                      "emergency_contact_phone",
                      formatPhone(e.target.value),
                      {
                        shouldDirty: true,
                        shouldValidate: true,
                      },
                    )
                  }
                />
              </FormField>
            </div>
          </div>

          {/* RESPONSÁVEL LEGAL (Exibido apenas para menores de 18 anos) */}
          {state.isMinor && (
            <div className="space-y-4">
              <div className="border-b border-border/60 pb-1.5">
                <h3 className="text-sm font-bold text-destructive/90">
                  Responsável Legal (Paciente Menor)
                </h3>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <FormField
                  label="Nome *"
                  error={errors.guardian_name?.message}
                  id={`${baseId}-guardian-name`}
                >
                  <input
                    id={`${baseId}-guardian-name`}
                    type="text"
                    placeholder="Nome do responsável legal"
                    aria-describedby={
                      errors.guardian_name
                        ? `${baseId}-guardian-name-error`
                        : undefined
                    }
                    aria-invalid={!!errors.guardian_name}
                    disabled={submit.pending}
                    {...register("guardian_name")}
                    className={inputClass}
                  />
                </FormField>

                <FormField
                  label="CPF *"
                  error={errors.guardian_cpf?.message}
                  id={`${baseId}-guardian-cpf`}
                >
                  <input
                    id={`${baseId}-guardian-cpf`}
                    type="text"
                    placeholder="000.000.000-00"
                    aria-describedby={
                      errors.guardian_cpf
                        ? `${baseId}-guardian-cpf-error`
                        : undefined
                    }
                    aria-invalid={!!errors.guardian_cpf}
                    disabled={submit.pending}
                    {...register("guardian_cpf")}
                    className={inputClass}
                    onChange={(e) =>
                      setValue("guardian_cpf", formatCpf(e.target.value), {
                        shouldDirty: true,
                        shouldValidate: true,
                      })
                    }
                  />
                </FormField>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <FormField
                  label="Telefone *"
                  error={errors.guardian_phone?.message}
                  id={`${baseId}-guardian-phone`}
                >
                  <input
                    id={`${baseId}-guardian-phone`}
                    type="text"
                    placeholder="(11) 99999-9999 ou +55 21 99999-9999"
                    aria-describedby={
                      errors.guardian_phone
                        ? `${baseId}-guardian-phone-error`
                        : undefined
                    }
                    aria-invalid={!!errors.guardian_phone}
                    disabled={submit.pending}
                    {...register("guardian_phone")}
                    className={inputClass}
                    onChange={(e) =>
                      setValue("guardian_phone", formatPhone(e.target.value), {
                        shouldDirty: true,
                        shouldValidate: true,
                      })
                    }
                  />
                </FormField>

                <FormField
                  label="E-mail *"
                  error={errors.guardian_email?.message}
                  id={`${baseId}-guardian-email`}
                >
                  <input
                    id={`${baseId}-guardian-email`}
                    type="email"
                    placeholder="email@exemplo.com"
                    aria-describedby={
                      errors.guardian_email
                        ? `${baseId}-guardian-email-error`
                        : undefined
                    }
                    aria-invalid={!!errors.guardian_email}
                    disabled={submit.pending}
                    {...register("guardian_email")}
                    className={inputClass}
                  />
                </FormField>
              </div>

              <FormField
                label="Vínculo / Relacionamento"
                error={errors.guardian_relationship?.message}
                id={`${baseId}-guardian-relationship`}
              >
                <input
                  id={`${baseId}-guardian-relationship`}
                  type="text"
                  placeholder="Ex: Mãe, Pai, Tutor..."
                  aria-describedby={
                    errors.guardian_relationship
                      ? `${baseId}-guardian-relationship-error`
                      : undefined
                  }
                  aria-invalid={!!errors.guardian_relationship}
                  disabled={submit.pending}
                  {...register("guardian_relationship")}
                  className={inputClass}
                />
              </FormField>
            </div>
          )}

          {/* 5. RESPONSÁVEL FINANCEIRO */}
          <div className="space-y-4">
            <div className="border-b border-border/60 pb-1.5">
              <h3 className="text-sm font-bold text-foreground/90">
                Responsável Financeiro
              </h3>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Nome"
                error={errors.financial_responsible_name?.message}
                id={`${baseId}-financial-responsible-name`}
              >
                <input
                  id={`${baseId}-financial-responsible-name`}
                  type="text"
                  placeholder="Nome do responsável financeiro"
                  aria-describedby={
                    errors.financial_responsible_name
                      ? `${baseId}-financial-responsible-name-error`
                      : undefined
                  }
                  aria-invalid={!!errors.financial_responsible_name}
                  disabled={submit.pending}
                  {...register("financial_responsible_name")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="CPF"
                error={errors.financial_responsible_cpf?.message}
                id={`${baseId}-financial-responsible-cpf`}
              >
                <input
                  id={`${baseId}-financial-responsible-cpf`}
                  type="text"
                  placeholder="000.000.000-00"
                  aria-describedby={
                    errors.financial_responsible_cpf
                      ? `${baseId}-financial-responsible-cpf-error`
                      : undefined
                  }
                  aria-invalid={!!errors.financial_responsible_cpf}
                  disabled={submit.pending}
                  {...register("financial_responsible_cpf")}
                  className={inputClass}
                  onChange={(e) =>
                    setValue(
                      "financial_responsible_cpf",
                      formatCpf(e.target.value),
                      {
                        shouldDirty: true,
                        shouldValidate: true,
                      },
                    )
                  }
                />
              </FormField>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Telefone"
                error={errors.financial_responsible_phone?.message}
                id={`${baseId}-financial-responsible-phone`}
              >
                <input
                  id={`${baseId}-financial-responsible-phone`}
                  type="text"
                  placeholder="(11) 99999-9999 ou +55 21 99999-9999"
                  aria-describedby={
                    errors.financial_responsible_phone
                      ? `${baseId}-financial-responsible-phone-error`
                      : undefined
                  }
                  aria-invalid={!!errors.financial_responsible_phone}
                  disabled={submit.pending}
                  {...register("financial_responsible_phone")}
                  className={inputClass}
                  onChange={(e) =>
                    setValue(
                      "financial_responsible_phone",
                      formatPhone(e.target.value),
                      {
                        shouldDirty: true,
                        shouldValidate: true,
                      },
                    )
                  }
                />
              </FormField>

              <FormField
                label="E-mail"
                error={errors.financial_responsible_email?.message}
                id={`${baseId}-financial-responsible-email`}
              >
                <input
                  id={`${baseId}-financial-responsible-email`}
                  type="email"
                  placeholder="email@exemplo.com"
                  aria-describedby={
                    errors.financial_responsible_email
                      ? `${baseId}-financial-responsible-email-error`
                      : undefined
                  }
                  aria-invalid={!!errors.financial_responsible_email}
                  disabled={submit.pending}
                  {...register("financial_responsible_email")}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <FormField
                label="Estado Civil"
                error={errors.financial_responsible_marital_status?.message}
                id={`${baseId}-financial-responsible-marital-status`}
              >
                <select
                  id={`${baseId}-financial-responsible-marital-status`}
                  aria-describedby={
                    errors.financial_responsible_marital_status
                      ? `${baseId}-financial-responsible-marital-status-error`
                      : undefined
                  }
                  aria-invalid={!!errors.financial_responsible_marital_status}
                  disabled={submit.pending}
                  {...register("financial_responsible_marital_status")}
                  className={selectClass}
                >
                  {MARITAL_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField
                label="Naturalidade"
                error={errors.financial_responsible_naturality?.message}
                id={`${baseId}-financial-responsible-naturality`}
              >
                <input
                  id={`${baseId}-financial-responsible-naturality`}
                  type="text"
                  placeholder="Cidade/Estado"
                  aria-describedby={
                    errors.financial_responsible_naturality
                      ? `${baseId}-financial-responsible-naturality-error`
                      : undefined
                  }
                  aria-invalid={!!errors.financial_responsible_naturality}
                  disabled={submit.pending}
                  {...register("financial_responsible_naturality")}
                  className={inputClass}
                />
              </FormField>

              <FormField
                label="Ocupação"
                error={errors.financial_responsible_occupation?.message}
                id={`${baseId}-financial-responsible-occupation`}
              >
                <input
                  id={`${baseId}-financial-responsible-occupation`}
                  type="text"
                  placeholder="Ocupação"
                  aria-describedby={
                    errors.financial_responsible_occupation
                      ? `${baseId}-financial-responsible-occupation-error`
                      : undefined
                  }
                  aria-invalid={!!errors.financial_responsible_occupation}
                  disabled={submit.pending}
                  {...register("financial_responsible_occupation")}
                  className={inputClass}
                />
              </FormField>
            </div>
          </div>

          {/* CAMPOS ADICIONAIS COLLAPSIBLE (Mantém as capacidades extras do sistema ocultas por padrão) */}
          <div className="pt-2">
            <button
              type="button"
              aria-expanded={showAdditionalFields}
              disabled={submit.pending}
              onClick={() => setShowAdditionalFields(!showAdditionalFields)}
              className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground font-semibold py-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 rounded px-1 disabled:opacity-50 disabled:pointer-events-none"
            >
              {showAdditionalFields ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Ocultar campos adicionais</span>
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Mostrar campos adicionais</span>
                </>
              )}
            </button>

            {showAdditionalFields && (
              <div className="grid gap-4 mt-3 p-4 rounded-xl border border-border/50 bg-secondary/5 space-y-2 animate-in fade-in duration-200">
                <div className="grid gap-3 sm:grid-cols-2">
                  <FormField
                    label="Gênero"
                    error={errors.gender?.message}
                    id={`${baseId}-gender`}
                  >
                    <select
                      id={`${baseId}-gender`}
                      aria-describedby={
                        errors.gender ? `${baseId}-gender-error` : undefined
                      }
                      aria-invalid={!!errors.gender}
                      disabled={submit.pending}
                      {...register("gender")}
                      className={selectClass}
                    >
                      {GENDER_OPTIONS.map(([val, lbl]) => (
                        <option key={val} value={val}>
                          {lbl}
                        </option>
                      ))}
                    </select>
                  </FormField>

                  <FormField
                    label="Estado Civil do Paciente"
                    error={errors.marital_status?.message}
                    id={`${baseId}-marital-status`}
                  >
                    <select
                      id={`${baseId}-marital-status`}
                      aria-describedby={
                        errors.marital_status
                          ? `${baseId}-marital-status-error`
                          : undefined
                      }
                      aria-invalid={!!errors.marital_status}
                      disabled={submit.pending}
                      {...register("marital_status")}
                      className={selectClass}
                    >
                      {PATIENT_MARITAL_OPTIONS.map(([val, lbl]) => (
                        <option key={val} value={val}>
                          {lbl}
                        </option>
                      ))}
                    </select>
                  </FormField>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <FormField
                    label="Tipo de Atendimento"
                    error={errors.attendance_type?.message}
                    id={`${baseId}-attendance-type`}
                  >
                    <select
                      id={`${baseId}-attendance-type`}
                      aria-describedby={
                        errors.attendance_type
                          ? `${baseId}-attendance-type-error`
                          : undefined
                      }
                      aria-invalid={!!errors.attendance_type}
                      disabled={submit.pending}
                      {...register("attendance_type")}
                      className={selectClass}
                    >
                      <option value="individual">Individual</option>
                      <option value="couple">Casal</option>
                      <option value="family">Familiar</option>
                      <option value="group">Grupo</option>
                      <option value="other">Outro</option>
                    </select>
                  </FormField>

                  <FormField
                    label="Modalidade"
                    error={errors.modality?.message}
                    id={`${baseId}-modality`}
                  >
                    <select
                      id={`${baseId}-modality`}
                      aria-describedby={
                        errors.modality ? `${baseId}-modality-error` : undefined
                      }
                      aria-invalid={!!errors.modality}
                      disabled={submit.pending}
                      {...register("modality")}
                      className={selectClass}
                    >
                      <option value="in_person">Presencial</option>
                      <option value="online">Online</option>
                      <option value="hybrid">Híbrido</option>
                    </select>
                  </FormField>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <FormField
                    label="Frequência"
                    error={errors.planned_frequency?.message}
                    id={`${baseId}-planned-frequency`}
                  >
                    <select
                      id={`${baseId}-planned-frequency`}
                      aria-describedby={
                        errors.planned_frequency
                          ? `${baseId}-planned-frequency-error`
                          : undefined
                      }
                      aria-invalid={!!errors.planned_frequency}
                      disabled={submit.pending}
                      {...register("planned_frequency")}
                      className={selectClass}
                    >
                      <option value="">Não definida</option>
                      <option value="weekly">Semanal</option>
                      <option value="biweekly">Quinzenal</option>
                      <option value="monthly">Mensal</option>
                      <option value="as_needed">Conforme necessidade</option>
                    </select>
                  </FormField>

                  <FormField
                    label="Etiquetas (separadas por vírgula)"
                    error={errors.tags?.message}
                    id={`${baseId}-tags`}
                  >
                    <input
                      id={`${baseId}-tags`}
                      type="text"
                      placeholder="Ex: TCC, Ansiedade"
                      aria-describedby={
                        errors.tags ? `${baseId}-tags-error` : undefined
                      }
                      aria-invalid={!!errors.tags}
                      disabled={submit.pending}
                      {...register("tags")}
                      className={inputClass}
                    />
                  </FormField>
                </div>

                <FormField
                  label="Origem / Indicação"
                  error={errors.referral_source?.message}
                  id={`${baseId}-referral-source`}
                >
                  <input
                    id={`${baseId}-referral-source`}
                    type="text"
                    placeholder="Ex: Google, Recomendação médica"
                    aria-describedby={
                      errors.referral_source
                        ? `${baseId}-referral-source-error`
                        : undefined
                    }
                    aria-invalid={!!errors.referral_source}
                    disabled={submit.pending}
                    {...register("referral_source")}
                    className={inputClass}
                  />
                </FormField>
              </div>
            )}
          </div>

          {/* 6. OBSERVAÇÕES */}
          <div className="space-y-4">
            <div className="border-b border-border/60 pb-1.5">
              <h3 className="text-sm font-bold text-foreground/90">
                Observações
              </h3>
            </div>

            <FormField
              label="Observações"
              error={errors.notes?.message}
              id={`${baseId}-notes`}
            >
              <textarea
                id={`${baseId}-notes`}
                placeholder="Observações sobre o paciente..."
                aria-describedby={
                  errors.notes ? `${baseId}-notes-error` : undefined
                }
                aria-invalid={!!errors.notes}
                disabled={submit.pending}
                {...register("notes")}
                className={textareaClass}
              />
              <div className="flex justify-between items-center text-[10px] text-muted-foreground mt-1">
                <span>
                  Informações clínicas devem ser registradas no prontuário.
                </span>
                <span>{watchNotes.length}/2000</span>
              </div>
            </FormField>

            <div className="flex items-start gap-2 text-xs text-foreground/95 mt-4">
              <input
                id={`${baseId}-consent`}
                type="checkbox"
                disabled={submit.pending}
                {...register("consent_terms_accepted")}
                className="mt-0.5 rounded border-border text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              />
              <label
                htmlFor={`${baseId}-consent`}
                className="select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Confirmo que os consentimentos necessários foram coletados.
              </label>
            </div>
          </div>

          <button type="submit" className="sr-only">
            Salvar
          </button>
        </form>
      )}
    </PatientFormDrawerShell>
  );
}
