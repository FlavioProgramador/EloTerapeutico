"use client";

import axios from "axios";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Check,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";
import {
  forwardRef,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { useForm, type FieldPath } from "react-hook-form";

import { useAuth } from "@/contexts/auth";
import { useOrganization } from "@/contexts/organization";
import {
  buildOnboardingStepPayload,
  getOnboardingStepFields,
  normalizeOnboardingStep,
  onboardingPayloadToForm,
  organizationOnboardingDefaults,
  type OnboardingFormField,
  type OrganizationOnboardingPayload,
} from "@/features/organizations/onboarding-flow";
import {
  organizationOnboardingSchema,
  type OrganizationOnboardingForm,
} from "@/features/organizations/schemas/onboarding";
import type { Organization } from "@/features/organizations/types";
import { api } from "@/lib/api";
import {
  extractApiErrorMessage,
  type ApiErrorEnvelope,
} from "@/lib/auth-flow";
import { sanitizePublicMessage } from "@/lib/errors/sanitize-error";

const steps = [
  "Organização",
  "Perfil profissional",
  "Atendimento",
  "Configurações",
  "Revisão",
  "Conclusão",
];

const onboardingFormFields = new Set<OnboardingFormField>(
  Object.keys(organizationOnboardingDefaults) as OnboardingFormField[],
);

function getErrorPayload(error: unknown): Record<string, unknown> | null {
  if (!axios.isAxiosError(error)) return null;
  const payload = error.response?.data;
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return null;
  }
  return payload as Record<string, unknown>;
}

function firstSafeMessage(value: unknown): string | null {
  const direct = sanitizePublicMessage(value);
  if (direct) return direct;

  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstSafeMessage(item);
      if (message) return message;
    }
  } else if (value && typeof value === "object") {
    for (const item of Object.values(value as Record<string, unknown>)) {
      const message = firstSafeMessage(item);
      if (message) return message;
    }
  }

  return null;
}

function publicApiErrorMessage(error: unknown, fallback: string): string {
  const payload = getErrorPayload(error);
  return extractApiErrorMessage(
    payload as ApiErrorEnvelope | null,
    fallback,
  );
}

const TextField = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & {
    label: string;
    error?: string;
  }
>(({ label, error, id, ...props }, ref) => {
  const inputId = id ?? props.name;
  const errorId = error && inputId ? `${inputId}-error` : undefined;

  return (
    <label className="space-y-1.5 text-xs font-medium text-foreground">
      <span>{label}</span>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={errorId}
        {...props}
        className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/10"
      />
      {error ? (
        <span id={errorId} className="block text-[11px] text-destructive">
          {error}
        </span>
      ) : null}
    </label>
  );
});
TextField.displayName = "TextField";

function ToggleField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-4 rounded-lg border border-border p-3 text-sm">
      <span>{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 accent-primary"
      />
    </label>
  );
}

export default function OnboardingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const {
    activeOrganization,
    isLoading: organizationLoading,
    isSwitching,
    refreshOrganizations,
    switchOrganization,
  } = useOrganization();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState("");
  const hydratedOrganizationId = useRef<string | null>(null);

  const form = useForm<OrganizationOnboardingForm>({
    resolver: zodResolver(organizationOnboardingSchema),
    defaultValues: organizationOnboardingDefaults,
    mode: "onBlur",
  });

  const onboardingQueryKey = [
    "organization-onboarding",
    activeOrganization?.id,
  ] as const;

  const onboarding = useQuery({
    queryKey: onboardingQueryKey,
    queryFn: async () => {
      const { data } = await api.get<OrganizationOnboardingPayload>(
        `organizations/${activeOrganization?.id}/onboarding/`,
      );
      return data;
    },
    enabled: Boolean(activeOrganization?.id),
    retry: false,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login?next=/onboarding");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    const data = onboarding.data;
    if (!data || saving) return;

    if (data.status === "completed") {
      router.replace("/dashboard");
      return;
    }

    const sameOrganization =
      hydratedOrganizationId.current === data.organization.id;
    if (sameOrganization && form.formState.isDirty) return;

    form.reset(onboardingPayloadToForm(data, user));
    hydratedOrganizationId.current = data.organization.id;
    setStep(normalizeOnboardingStep(data.step));
  }, [
    form,
    form.formState.isDirty,
    onboarding.data,
    router,
    saving,
    user,
  ]);

  const values = form.watch();
  const loading = authLoading || organizationLoading || onboarding.isLoading;
  const busy = saving || isSwitching;

  const applyOnboardingResponse = (data: OrganizationOnboardingPayload) => {
    queryClient.setQueryData(
      ["organization-onboarding", data.organization.id],
      data,
    );
    form.reset(onboardingPayloadToForm(data, user));
    hydratedOrganizationId.current = data.organization.id;
    setStep(normalizeOnboardingStep(data.step));
  };

  const applyServerFieldErrors = (error: unknown): boolean => {
    const payload = getErrorPayload(error);
    if (!payload) return false;

    let found = false;
    for (const [field, detail] of Object.entries(payload)) {
      if (!onboardingFormFields.has(field as OnboardingFormField)) continue;
      const message = firstSafeMessage(detail);
      if (!message) continue;
      form.setError(field as FieldPath<OrganizationOnboardingForm>, {
        type: "server",
        message,
      });
      found = true;
    }
    return found;
  };

  const validateCurrentStep = async (): Promise<boolean> => {
    const fields = getOnboardingStepFields(
      step,
    ) as FieldPath<OrganizationOnboardingForm>[];
    if (!fields.length) return true;
    return form.trigger(fields, { shouldFocus: true });
  };

  const createFirstOrganization = async () => {
    if (!(await validateCurrentStep())) return;

    const data = form.getValues();
    setSaving(true);
    setPageError("");
    form.clearErrors();

    try {
      const response = await api.post<Organization>("organizations/", {
        name: data.name,
        organization_type: data.organization_type,
        legal_name: data.legal_name,
        document: data.document,
        email: data.email,
        phone: data.phone,
        timezone: data.timezone,
      });

      await switchOrganization(response.data.id);

      const onboardingResponse = await api.patch<OrganizationOnboardingPayload>(
        `organizations/${response.data.id}/onboarding/`,
        buildOnboardingStepPayload(1, data),
      );
      applyOnboardingResponse(onboardingResponse.data);
    } catch (error) {
      const hasFieldErrors = applyServerFieldErrors(error);
      setPageError(
        hasFieldErrors
          ? "Revise os campos destacados. Seus dados foram mantidos."
          : publicApiErrorMessage(
              error,
              "Não foi possível criar sua organização. Seus dados foram mantidos.",
            ),
      );
    } finally {
      setSaving(false);
    }
  };

  const saveStep = async () => {
    if (!activeOrganization) return;
    if (!(await validateCurrentStep())) return;

    setSaving(true);
    setPageError("");
    form.clearErrors();

    try {
      const response = await api.patch<OrganizationOnboardingPayload>(
        `organizations/${activeOrganization.id}/onboarding/`,
        buildOnboardingStepPayload(step, form.getValues()),
      );
      applyOnboardingResponse(response.data);
    } catch (error) {
      const hasFieldErrors = applyServerFieldErrors(error);
      setPageError(
        hasFieldErrors
          ? "Revise os campos destacados. Seus dados foram mantidos."
          : publicApiErrorMessage(
              error,
              "Não foi possível salvar esta etapa. Seus dados foram mantidos.",
            ),
      );
    } finally {
      setSaving(false);
    }
  };

  const complete = async () => {
    if (!activeOrganization) return;
    setSaving(true);
    setPageError("");

    try {
      await api.post(
        `organizations/${activeOrganization.id}/onboarding/complete/`,
        { confirm: true },
      );
      await refreshOrganizations();
      router.replace("/dashboard");
    } catch (error) {
      setPageError(
        publicApiErrorMessage(
          error,
          "Ainda existem informações obrigatórias pendentes.",
        ),
      );
    } finally {
      setSaving(false);
    }
  };

  const stepContent = useMemo(() => {
    if (step === 1) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField
            label="Nome do consultório ou clínica"
            {...form.register("name")}
            error={form.formState.errors.name?.message}
          />
          <label className="space-y-1.5 text-xs font-medium">
            <span>Como você trabalha?</span>
            <select
              {...form.register("organization_type")}
              className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
            >
              <option value="individual">Trabalho sozinho</option>
              <option value="clinic">Clínica ou equipe</option>
              <option value="company">Empresa</option>
            </select>
          </label>
          <TextField
            label="Nome legal (opcional)"
            {...form.register("legal_name")}
            error={form.formState.errors.legal_name?.message}
          />
          <TextField
            label="CPF ou CNPJ (opcional)"
            {...form.register("document")}
            error={form.formState.errors.document?.message}
          />
          <TextField
            label="E-mail"
            type="email"
            {...form.register("email")}
            error={form.formState.errors.email?.message}
          />
          <TextField
            label="Telefone"
            {...form.register("phone")}
            error={form.formState.errors.phone?.message}
          />
        </div>
      );
    }

    if (step === 2) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField
            label="Nome profissional"
            {...form.register("display_name")}
            error={form.formState.errors.display_name?.message}
          />
          <TextField
            label="Título profissional"
            {...form.register("professional_title")}
            error={form.formState.errors.professional_title?.message}
          />
          <TextField
            label="Conselho"
            placeholder="CRP, CREFITO..."
            {...form.register("council_type")}
            error={form.formState.errors.council_type?.message}
          />
          <TextField
            label="Número do conselho"
            {...form.register("council_number")}
            error={form.formState.errors.council_number?.message}
          />
          <TextField
            label="UF ou região"
            {...form.register("council_region")}
            error={form.formState.errors.council_region?.message}
          />
          <TextField
            label="Especialidades separadas por vírgula"
            {...form.register("specialties_text")}
            error={form.formState.errors.specialties_text?.message}
          />
          <TextField
            label="E-mail público"
            type="email"
            {...form.register("public_email")}
            error={form.formState.errors.public_email?.message}
          />
          <TextField
            label="Telefone profissional"
            {...form.register("professional_phone")}
            error={form.formState.errors.professional_phone?.message}
          />
          <label className="space-y-1.5 text-xs font-medium md:col-span-2">
            <span>Apresentação profissional</span>
            <textarea
              {...form.register("bio")}
              rows={4}
              className="w-full rounded-lg border border-border bg-background p-3 text-sm"
            />
            {form.formState.errors.bio?.message ? (
              <span className="block text-[11px] text-destructive">
                {form.formState.errors.bio.message}
              </span>
            ) : null}
          </label>
        </div>
      );
    }

    if (step === 3) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField
            label="Duração padrão (minutos)"
            type="number"
            {...form.register("default_appointment_duration")}
            error={form.formState.errors.default_appointment_duration?.message}
          />
          <TextField
            label="Valor padrão da sessão"
            type="number"
            step="0.01"
            {...form.register("default_session_value")}
            error={form.formState.errors.default_session_value?.message}
          />
          <ToggleField
            label="Atendimento presencial"
            checked={values.accepts_in_person}
            onChange={(checked) =>
              form.setValue("accepts_in_person", checked, { shouldDirty: true })
            }
          />
          <ToggleField
            label="Atendimento online"
            checked={values.accepts_online}
            onChange={(checked) =>
              form.setValue("accepts_online", checked, { shouldDirty: true })
            }
          />
          <TextField
            label="Antecedência mínima (minutos)"
            type="number"
            {...form.register("minimum_booking_notice_minutes")}
            error={form.formState.errors.minimum_booking_notice_minutes?.message}
          />
          <TextField
            label="Janela máxima de agendamento (dias)"
            type="number"
            {...form.register("maximum_booking_days")}
            error={form.formState.errors.maximum_booking_days?.message}
          />
          <TextField
            label="Política de cancelamento (horas)"
            type="number"
            {...form.register("cancellation_notice_hours")}
            error={form.formState.errors.cancellation_notice_hours?.message}
          />
        </div>
      );
    }

    if (step === 4) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <ToggleField
            label="Permitir agendamento online"
            checked={values.allow_online_booking}
            onChange={(checked) =>
              form.setValue("allow_online_booking", checked, { shouldDirty: true })
            }
          />
          <ToggleField
            label="Habilitar portal do paciente"
            checked={values.allow_patient_portal}
            onChange={(checked) =>
              form.setValue("allow_patient_portal", checked, { shouldDirty: true })
            }
          />
          <ToggleField
            label="Enviar lembretes"
            checked={values.send_appointment_reminders}
            onChange={(checked) =>
              form.setValue("send_appointment_reminders", checked, {
                shouldDirty: true,
              })
            }
          />
          <TextField
            label="Horas antes do lembrete"
            type="number"
            {...form.register("reminder_hours_before")}
            error={form.formState.errors.reminder_hours_before?.message}
          />
          <TextField
            label="Nome nos documentos"
            {...form.register("business_name_on_documents")}
            error={form.formState.errors.business_name_on_documents?.message}
          />
          <div className="rounded-lg border border-dashed border-border p-3 text-xs text-muted-foreground">
            Telemedicina será habilitada quando a infraestrutura de vídeo estiver
            configurada.
          </div>
        </div>
      );
    }

    if (step === 5) {
      return (
        <div className="grid gap-3 text-sm md:grid-cols-2">
          <div className="rounded-xl border border-border p-4">
            <strong>Organização</strong>
            <p className="mt-2 text-muted-foreground">
              {values.name} ·{" "}
              {values.organization_type === "individual" ? "Individual" : "Equipe"}
            </p>
          </div>
          <div className="rounded-xl border border-border p-4">
            <strong>Profissional</strong>
            <p className="mt-2 text-muted-foreground">
              {values.display_name} ·{" "}
              {values.professional_title || "Título não informado"}
            </p>
          </div>
          <div className="rounded-xl border border-border p-4">
            <strong>Atendimento</strong>
            <p className="mt-2 text-muted-foreground">
              {values.default_appointment_duration} minutos · R${" "}
              {Number(values.default_session_value).toFixed(2)}
            </p>
          </div>
          <div className="rounded-xl border border-border p-4">
            <strong>Recursos</strong>
            <p className="mt-2 text-muted-foreground">
              Lembretes {values.send_appointment_reminders ? "ativos" : "inativos"}
              {" · "}Portal {values.allow_patient_portal ? "ativo" : "inativo"}
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center gap-4 py-8 text-center">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-primary/10 text-primary">
          <Check className="h-7 w-7" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">
            Configuração pronta para concluir
          </h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Confirme para acessar o painel. As informações poderão ser alteradas
            posteriormente.
          </p>
        </div>
      </div>
    );
  }, [form, step, values]);

  if (loading) {
    return (
      <main className="grid min-h-screen place-items-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background px-4 py-10 text-foreground">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-primary text-primary-foreground">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Configure seu espaço de trabalho</h1>
            <p className="text-sm text-muted-foreground">
              Funciona para atendimento individual ou clínica com equipe.
            </p>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-3 gap-2 md:grid-cols-6">
          {steps.map((label, index) => (
            <div
              key={label}
              className={`rounded-lg border px-2 py-2 text-center text-[11px] ${
                index + 1 <= step
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border text-muted-foreground"
              }`}
            >
              <span className="font-bold">{index + 1}</span>
              <span className="hidden md:block">{label}</span>
            </div>
          ))}
        </div>

        <section className="rounded-2xl border border-border bg-card p-5 shadow-sm md:p-8">
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Etapa {step} de 6
            </p>
            <h2 className="mt-1 text-xl font-semibold">{steps[step - 1]}</h2>
          </div>

          {stepContent}

          {pageError ? (
            <p
              role="alert"
              className="mt-5 rounded-lg bg-destructive/10 p-3 text-sm text-destructive"
            >
              {pageError}
            </p>
          ) : null}

          <div className="mt-8 flex items-center justify-between border-t border-border pt-5">
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                step === 1
                  ? logout()
                  : setStep((current) => Math.max(current - 1, 1))
              }
              className="inline-flex h-10 items-center gap-2 rounded-lg border border-border px-4 text-sm disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
              Voltar
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={
                activeOrganization
                  ? step === 6
                    ? complete
                    : saveStep
                  : createFirstOrganization
              }
              className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-60"
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {step === 6 ? "Concluir onboarding" : "Salvar e continuar"}
              {!busy && step < 6 ? <ChevronRight className="h-4 w-4" /> : null}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
