"use client";

import { useEffect, useMemo, useState, forwardRef } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { Building2, Check, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { useAuth } from "@/contexts/auth";
import { useOrganization } from "@/contexts/organization";
import {
  organizationOnboardingSchema,
  type OrganizationOnboardingForm,
} from "@/features/organizations/schemas/onboarding";
import type { Organization, OrganizationMembership } from "@/features/organizations/types";
import { api } from "@/lib/api";

interface OnboardingPayload {
  organization: Organization;
  membership: OrganizationMembership;
  settings: Record<string, unknown>;
  professional_profile: Record<string, unknown> | null;
  status: string;
  step: number;
  completed_at: string | null;
}

const steps = [
  "Organização",
  "Perfil profissional",
  "Atendimento",
  "Configurações",
  "Revisão",
  "Conclusão",
];

const defaultValues: OrganizationOnboardingForm = {
  name: "",
  organization_type: "individual",
  legal_name: "",
  document: "",
  email: "",
  phone: "",
  timezone: "America/Sao_Paulo",
  display_name: "",
  professional_title: "",
  council_type: "",
  council_number: "",
  council_region: "",
  specialties_text: "",
  bio: "",
  public_email: "",
  professional_phone: "",
  default_appointment_duration: 50,
  default_session_value: 0,
  accepts_online: true,
  accepts_in_person: true,
  minimum_booking_notice_minutes: 0,
  maximum_booking_days: 90,
  cancellation_notice_hours: 24,
  allow_online_booking: false,
  allow_patient_portal: false,
  send_appointment_reminders: true,
  reminder_hours_before: 24,
  business_name_on_documents: "",
  document_header: "",
  document_footer: "",
};

const TextField = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }
>(({ label, error, ...props }, ref) => {
  return (
    <label className="space-y-1.5 text-xs font-medium text-foreground">
      <span>{label}</span>
      <input
        ref={ref}
        {...props}
        className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/10"
      />
      {error ? <span className="block text-[11px] text-destructive">{error}</span> : null}
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
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const {
    activeOrganization,
    isLoading: organizationLoading,
    refreshOrganizations,
    switchOrganization,
  } = useOrganization();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState("");

  const form = useForm<OrganizationOnboardingForm>({
    resolver: zodResolver(organizationOnboardingSchema),
    defaultValues,
    mode: "onBlur",
  });

  const onboarding = useQuery({
    queryKey: ["organization-onboarding", activeOrganization?.id],
    queryFn: async () => {
      const { data } = await api.get<OnboardingPayload>(
        `organizations/${activeOrganization?.id}/onboarding/`,
      );
      return data;
    },
    enabled: Boolean(activeOrganization?.id),
    retry: false,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.replace("/login?next=/onboarding");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    const data = onboarding.data;
    if (!data) return;
    const profile = data.professional_profile ?? {};
    const settings = data.settings ?? {};
    form.reset({
      ...defaultValues,
      name: data.organization.name,
      organization_type: data.organization.organization_type,
      legal_name: data.organization.legal_name,
      document: data.organization.document,
      email: data.organization.email,
      phone: data.organization.phone,
      timezone: data.organization.timezone,
      display_name: String(profile.display_name ?? user?.full_name ?? ""),
      professional_title: String(profile.professional_title ?? ""),
      council_type: String(profile.council_type ?? ""),
      council_number: String(profile.council_number ?? ""),
      council_region: String(profile.council_region ?? ""),
      specialties_text: Array.isArray(profile.specialties)
        ? profile.specialties.join(", ")
        : "",
      bio: String(profile.bio ?? ""),
      public_email: String(profile.public_email ?? user?.email ?? ""),
      professional_phone: String(profile.phone ?? ""),
      default_appointment_duration: Number(profile.default_appointment_duration ?? 50),
      default_session_value: Number(profile.default_session_value ?? 0),
      accepts_online: Boolean(profile.accepts_online ?? true),
      accepts_in_person: Boolean(profile.accepts_in_person ?? true),
      minimum_booking_notice_minutes: Number(settings.minimum_booking_notice_minutes ?? 0),
      maximum_booking_days: Number(settings.maximum_booking_days ?? 90),
      cancellation_notice_hours: Number(settings.cancellation_notice_hours ?? 24),
      allow_online_booking: Boolean(settings.allow_online_booking ?? false),
      allow_patient_portal: Boolean(settings.allow_patient_portal ?? false),
      send_appointment_reminders: Boolean(settings.send_appointment_reminders ?? true),
      reminder_hours_before: Number(settings.reminder_hours_before ?? 24),
      business_name_on_documents: String(settings.business_name_on_documents ?? data.organization.name),
      document_header: String(settings.document_header ?? ""),
      document_footer: String(settings.document_footer ?? ""),
    });
    setStep(Math.min(Math.max(data.step || 1, 1), 6));
    if (data.status === "completed") router.replace("/dashboard");
  }, [form, onboarding.data, router, user?.email, user?.full_name]);

  const values = form.watch();
  const loading = authLoading || organizationLoading || onboarding.isLoading;

  const createFirstOrganization = async () => {
    const isValid = await form.trigger([
      "name",
      "organization_type",
      "legal_name",
      "document",
      "email",
      "phone",
    ]);
    if (!isValid) return;

    const data = form.getValues();
    setSaving(true);
    setPageError("");
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
      await api.patch(`organizations/${response.data.id}/onboarding/`, { step: 2 });
      await refreshOrganizations();
      await switchOrganization(response.data.id);
      setStep(2);
    } catch {
      setPageError("Não foi possível criar sua organização.");
    } finally {
      setSaving(false);
    }
  };

  const saveStep = async () => {
    if (!activeOrganization) return;
    
    let fieldsToValidate: any[] = [];
    if (step === 1) fieldsToValidate = ["name", "organization_type", "legal_name", "document", "email", "phone", "timezone"];
    else if (step === 2) fieldsToValidate = ["display_name", "professional_title", "council_type", "council_number", "council_region", "specialties_text", "bio", "public_email", "professional_phone"];
    else if (step === 3) fieldsToValidate = ["default_appointment_duration", "default_session_value", "minimum_booking_notice_minutes", "maximum_booking_days", "cancellation_notice_hours"];
    else if (step === 4) fieldsToValidate = ["reminder_hours_before", "business_name_on_documents", "document_header", "document_footer"];
    
    if (fieldsToValidate.length > 0) {
      const isValid = await form.trigger(fieldsToValidate);
      if (!isValid) return;
    }

    setSaving(true);
    setPageError("");
    try {
      const data = form.getValues();
      const payload: Record<string, unknown> = { step: Math.min(step + 1, 6) };
      if (step === 1) {
        payload.organization = {
          name: data.name,
          organization_type: data.organization_type,
          legal_name: data.legal_name,
          document: data.document,
          email: data.email,
          phone: data.phone,
          timezone: data.timezone,
        };
      } else if (step === 2 || step === 3) {
        payload.professional_profile = {
          display_name: data.display_name,
          professional_title: data.professional_title,
          council_type: data.council_type,
          council_number: data.council_number,
          council_region: data.council_region,
          specialties: data.specialties_text
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          bio: data.bio,
          phone: data.professional_phone,
          public_email: data.public_email,
          default_appointment_duration: data.default_appointment_duration,
          default_session_value: data.default_session_value,
          accepts_online: data.accepts_online,
          accepts_in_person: data.accepts_in_person,
        };
      } else if (step === 4) {
        payload.settings = {
          default_timezone: data.timezone,
          default_appointment_duration: data.default_appointment_duration,
          minimum_booking_notice_minutes: data.minimum_booking_notice_minutes,
          maximum_booking_days: data.maximum_booking_days,
          cancellation_notice_hours: data.cancellation_notice_hours,
          allow_online_booking: data.allow_online_booking,
          allow_patient_portal: data.allow_patient_portal,
          allow_telemedicine: false,
          send_appointment_reminders: data.send_appointment_reminders,
          reminder_hours_before: data.reminder_hours_before,
          business_name_on_documents: data.business_name_on_documents,
          document_header: data.document_header,
          document_footer: data.document_footer,
        };
      }
      await api.patch(
        `organizations/${activeOrganization.id}/onboarding/`,
        payload,
      );
      await onboarding.refetch();
      setStep((current) => Math.min(current + 1, 6));
    } catch {
      setPageError("Não foi possível salvar esta etapa. Revise os campos.");
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
    } catch {
      setPageError("Ainda existem informações obrigatórias pendentes.");
    } finally {
      setSaving(false);
    }
  };

  const stepContent = useMemo(() => {
    if (step === 1) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="Nome do consultório ou clínica" {...form.register("name")} error={form.formState.errors.name?.message} />
          <label className="space-y-1.5 text-xs font-medium">
            <span>Como você trabalha?</span>
            <select {...form.register("organization_type")} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm">
              <option value="individual">Trabalho sozinho</option>
              <option value="clinic">Clínica ou equipe</option>
              <option value="company">Empresa</option>
            </select>
          </label>
          <TextField label="Nome legal (opcional)" {...form.register("legal_name")} error={form.formState.errors.legal_name?.message} />
          <TextField label="CPF ou CNPJ (opcional)" {...form.register("document")} error={form.formState.errors.document?.message} />
          <TextField label="E-mail" type="email" {...form.register("email")} error={form.formState.errors.email?.message} />
          <TextField label="Telefone" {...form.register("phone")} error={form.formState.errors.phone?.message} />
        </div>
      );
    }
    if (step === 2) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="Nome profissional" {...form.register("display_name")} error={form.formState.errors.display_name?.message} />
          <TextField label="Título profissional" {...form.register("professional_title")} error={form.formState.errors.professional_title?.message} />
          <TextField label="Conselho" placeholder="CRP, CREFITO..." {...form.register("council_type")} error={form.formState.errors.council_type?.message} />
          <TextField label="Número do conselho" {...form.register("council_number")} error={form.formState.errors.council_number?.message} />
          <TextField label="UF ou região" {...form.register("council_region")} error={form.formState.errors.council_region?.message} />
          <TextField label="Especialidades separadas por vírgula" {...form.register("specialties_text")} error={form.formState.errors.specialties_text?.message} />
          <TextField label="E-mail público" type="email" {...form.register("public_email")} error={form.formState.errors.public_email?.message} />
          <TextField label="Telefone profissional" {...form.register("professional_phone")} error={form.formState.errors.professional_phone?.message} />
          <label className="space-y-1.5 text-xs font-medium md:col-span-2">
            <span>Apresentação profissional</span>
            <textarea {...form.register("bio")} rows={4} className="w-full rounded-lg border border-border bg-background p-3 text-sm" />
            {form.formState.errors.bio?.message ? <span className="block text-[11px] text-destructive">{form.formState.errors.bio.message}</span> : null}
          </label>
        </div>
      );
    }
    if (step === 3) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="Duração padrão (minutos)" type="number" {...form.register("default_appointment_duration")} />
          <TextField label="Valor padrão da sessão" type="number" step="0.01" {...form.register("default_session_value")} />
          <ToggleField label="Atendimento presencial" checked={values.accepts_in_person} onChange={(checked) => form.setValue("accepts_in_person", checked)} />
          <ToggleField label="Atendimento online" checked={values.accepts_online} onChange={(checked) => form.setValue("accepts_online", checked)} />
          <TextField label="Antecedência mínima (minutos)" type="number" {...form.register("minimum_booking_notice_minutes")} />
          <TextField label="Janela máxima de agendamento (dias)" type="number" {...form.register("maximum_booking_days")} />
          <TextField label="Política de cancelamento (horas)" type="number" {...form.register("cancellation_notice_hours")} />
        </div>
      );
    }
    if (step === 4) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <ToggleField label="Permitir agendamento online" checked={values.allow_online_booking} onChange={(checked) => form.setValue("allow_online_booking", checked)} />
          <ToggleField label="Habilitar portal do paciente" checked={values.allow_patient_portal} onChange={(checked) => form.setValue("allow_patient_portal", checked)} />
          <ToggleField label="Enviar lembretes" checked={values.send_appointment_reminders} onChange={(checked) => form.setValue("send_appointment_reminders", checked)} />
          <TextField label="Horas antes do lembrete" type="number" {...form.register("reminder_hours_before")} />
          <TextField label="Nome nos documentos" {...form.register("business_name_on_documents")} />
          <div className="rounded-lg border border-dashed border-border p-3 text-xs text-muted-foreground">
            Telemedicina será habilitada quando a infraestrutura de vídeo estiver configurada.
          </div>
        </div>
      );
    }
    if (step === 5) {
      return (
        <div className="grid gap-3 text-sm md:grid-cols-2">
          <div className="rounded-xl border border-border p-4"><strong>Organização</strong><p className="mt-2 text-muted-foreground">{values.name} · {values.organization_type === "individual" ? "Individual" : "Equipe"}</p></div>
          <div className="rounded-xl border border-border p-4"><strong>Profissional</strong><p className="mt-2 text-muted-foreground">{values.display_name} · {values.professional_title || "Título não informado"}</p></div>
          <div className="rounded-xl border border-border p-4"><strong>Atendimento</strong><p className="mt-2 text-muted-foreground">{values.default_appointment_duration} minutos · R$ {Number(values.default_session_value).toFixed(2)}</p></div>
          <div className="rounded-xl border border-border p-4"><strong>Recursos</strong><p className="mt-2 text-muted-foreground">Lembretes {values.send_appointment_reminders ? "ativos" : "inativos"} · Portal {values.allow_patient_portal ? "ativo" : "inativo"}</p></div>
        </div>
      );
    }
    return (
      <div className="flex flex-col items-center gap-4 py-8 text-center">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-primary/10 text-primary"><Check className="h-7 w-7" /></div>
        <div><h2 className="text-xl font-semibold">Configuração pronta para concluir</h2><p className="mt-2 max-w-md text-sm text-muted-foreground">Confirme para acessar o painel. As informações poderão ser alteradas posteriormente.</p></div>
      </div>
    );
  }, [form, step, values]);

  if (loading) {
    return <main className="grid min-h-screen place-items-center bg-background"><Loader2 className="h-8 w-8 animate-spin text-primary" /></main>;
  }

  return (
    <main className="min-h-screen bg-background px-4 py-10 text-foreground">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-xl bg-primary text-primary-foreground"><Building2 className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Configure seu espaço de trabalho</h1><p className="text-sm text-muted-foreground">Funciona para atendimento individual ou clínica com equipe.</p></div></div>
        <div className="mb-6 grid grid-cols-3 gap-2 md:grid-cols-6">{steps.map((label, index) => <div key={label} className={`rounded-lg border px-2 py-2 text-center text-[11px] ${index + 1 <= step ? "border-primary/40 bg-primary/10 text-primary" : "border-border text-muted-foreground"}`}><span className="font-bold">{index + 1}</span><span className="hidden md:block">{label}</span></div>)}</div>
        <section className="rounded-2xl border border-border bg-card p-5 shadow-sm md:p-8">
          <div className="mb-6"><p className="text-xs font-semibold uppercase tracking-wider text-primary">Etapa {step} de 6</p><h2 className="mt-1 text-xl font-semibold">{steps[step - 1]}</h2></div>
          {stepContent}
          {pageError ? <p className="mt-5 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{pageError}</p> : null}
          <div className="mt-8 flex items-center justify-between border-t border-border pt-5">
            <button type="button" disabled={step === 1 || saving} onClick={() => setStep((current) => Math.max(current - 1, 1))} className="inline-flex h-10 items-center gap-2 rounded-lg border border-border px-4 text-sm disabled:opacity-40"><ChevronLeft className="h-4 w-4" />Voltar</button>
            <button type="button" disabled={saving} onClick={activeOrganization ? (step === 6 ? complete : saveStep) : createFirstOrganization} className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-60">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}{step === 6 ? "Concluir onboarding" : "Salvar e continuar"}{!saving && step < 6 ? <ChevronRight className="h-4 w-4" /> : null}</button>
          </div>
        </section>
      </div>
    </main>
  );
}
