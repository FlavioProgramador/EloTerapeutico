"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Bell,
  Building2,
  CalendarClock,
  KeyRound,
  Loader2,
  MessageSquare,
  Plug,
  Save,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/contexts/auth";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
} from "@/features/communications/use-communications";
import type { NotificationCategory } from "@/features/communications/types";
import { settingsService } from "./settings.service";
import {
  useAuthSessions,
  usePracticeSettings,
  useRevokeSession,
  useSaveWorkingHours,
  useSettingsProfile,
  useUpdatePracticeSettings,
  useUpdateSettingsProfile,
  useWorkingHours,
} from "./use-settings";
import type { PracticeSettings, SettingsProfile, WorkingHour } from "./types";

type SectionId =
  | "profile"
  | "practice"
  | "agenda"
  | "communications"
  | "notifications"
  | "security"
  | "integrations";

const sections: Array<{
  id: SectionId;
  label: string;
  icon: typeof UserRound;
}> = [
  { id: "profile", label: "Perfil profissional", icon: UserRound },
  { id: "practice", label: "Dados do consultório", icon: Building2 },
  { id: "agenda", label: "Agenda e atendimentos", icon: CalendarClock },
  { id: "communications", label: "Comunicação interna", icon: MessageSquare },
  { id: "notifications", label: "Notificações", icon: Bell },
  { id: "security", label: "Segurança e sessões", icon: ShieldCheck },
  { id: "integrations", label: "Integrações", icon: Plug },
];

const weekdays = [
  "Segunda-feira",
  "Terça-feira",
  "Quarta-feira",
  "Quinta-feira",
  "Sexta-feira",
  "Sábado",
  "Domingo",
];

const notificationCategories: Array<[NotificationCategory, string]> = [
  ["agenda", "Agenda"],
  ["patients", "Pacientes"],
  ["records", "Prontuário"],
  ["documents", "Documentos"],
  ["financial", "Financeiro"],
  ["billing", "Assinatura"],
  ["communications", "Comunicação interna"],
  ["forms", "Formulários"],
  ["security", "Segurança"],
  ["system", "Sistema"],
];

function Field({
  label,
  value,
  onChange,
  type = "text",
  disabled = false,
  placeholder,
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: string;
  disabled?: boolean;
  placeholder?: string;
}) {
  return (
    <label className="space-y-2">
      <span className="text-xs font-semibold text-foreground">{label}</span>
      <input
        type={type}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none transition focus:border-primary disabled:cursor-not-allowed disabled:opacity-60"
      />
    </label>
  );
}

function Toggle({
  label,
  description,
  checked,
  onChange,
  disabled = false,
}: {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex items-start justify-between gap-4 rounded-lg border border-border bg-background p-4">
      <span>
        <span className="block text-sm font-semibold text-foreground">{label}</span>
        {description && (
          <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
            {description}
          </span>
        )}
      </span>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-1 h-4 w-4 accent-primary"
      />
    </label>
  );
}

function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm sm:p-6">
      <h2 className="text-lg font-bold text-foreground">{title}</h2>
      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{description}</p>
      <div className="mt-6">{children}</div>
    </section>
  );
}

export function SettingsPageContent() {
  const [active, setActive] = useState<SectionId>("profile");
  const profileQuery = useSettingsProfile();
  const practiceQuery = usePracticeSettings();
  const workingHoursQuery = useWorkingHours();
  const sessionsQuery = useAuthSessions();
  const notificationPreferences = useNotificationPreferences();
  const updateProfile = useUpdateSettingsProfile();
  const updatePractice = useUpdatePracticeSettings();
  const saveWorkingHours = useSaveWorkingHours();
  const revokeSession = useRevokeSession();
  const updateNotificationPreferences = useUpdateNotificationPreferences();
  const { updateUser } = useAuth();

  const [profile, setProfile] = useState<SettingsProfile | null>(null);
  const [practice, setPractice] = useState<PracticeSettings | null>(null);
  const [hours, setHours] = useState<Array<Omit<WorkingHour, "weekday_display">>>([]);
  const [password, setPassword] = useState({
    current_password: "",
    new_password: "",
    new_password_confirm: "",
  });

  useEffect(() => {
    if (profileQuery.data) setProfile(profileQuery.data);
  }, [profileQuery.data]);
  useEffect(() => {
    if (practiceQuery.data) setPractice(practiceQuery.data);
  }, [practiceQuery.data]);
  useEffect(() => {
    if (!workingHoursQuery.data) return;
    setHours(
      weekdays.map((_, weekday) => {
        const current = workingHoursQuery.data?.find((item) => item.weekday === weekday);
        return current
          ? {
              id: current.id,
              weekday,
              start_time: current.start_time.slice(0, 5),
              end_time: current.end_time.slice(0, 5),
              is_active: current.is_active,
            }
          : {
              id: 0,
              weekday,
              start_time: "08:00",
              end_time: "18:00",
              is_active: weekday < 5,
            };
      }),
    );
  }, [workingHoursQuery.data]);

  const loading =
    profileQuery.isLoading ||
    practiceQuery.isLoading ||
    notificationPreferences.isLoading;

  const profilePayload = useMemo(() => {
    if (!profile) return null;
    const {
      id: _id,
      email: _email,
      role: _role,
      date_joined: _dateJoined,
      last_login: _lastLogin,
      avatar: _avatar,
      ...editable
    } = profile;
    return editable;
  }, [profile]);

  async function saveProfile() {
    if (!profilePayload) return;
    try {
      const saved = await updateProfile.mutateAsync(profilePayload);
      setProfile(saved);
      updateUser({
        full_name: saved.full_name,
        specialty: saved.specialty,
        phone: saved.phone,
        clinic_name: saved.clinic_name,
        default_session_value: saved.default_session_value,
      });
      toast.success("Perfil atualizado com sucesso.");
    } catch {
      toast.error("Não foi possível salvar o perfil.");
    }
  }

  async function savePractice() {
    if (!practice) return;
    try {
      const saved = await updatePractice.mutateAsync(practice);
      setPractice(saved);
      toast.success("Configurações atualizadas.");
    } catch {
      toast.error("Não foi possível salvar as configurações.");
    }
  }

  async function changePassword() {
    try {
      const result = await settingsService.changePassword(password);
      toast.success(result.message);
      setPassword({ current_password: "", new_password: "", new_password_confirm: "" });
    } catch {
      toast.error("Não foi possível alterar a senha. Revise os campos.");
    }
  }

  if (loading || !profile || !practice || !notificationPreferences.data) {
    return (
      <div className="mx-auto max-w-7xl space-y-4">
        <Skeleton className="h-16 w-full" />
        <div className="grid gap-4 lg:grid-cols-[15rem_1fr]">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-[34rem] w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-foreground">Configurações</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Preferências reais da sua conta, agenda, comunicação, notificações e segurança.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[15rem_minmax(0,1fr)]">
        <nav className="h-fit rounded-xl border border-border bg-card p-2" aria-label="Seções de configurações">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                type="button"
                onClick={() => setActive(section.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-xs font-semibold transition ${
                  active === section.id
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" /> {section.label}
              </button>
            );
          })}
        </nav>

        <div className="min-w-0 space-y-5">
          {active === "profile" && (
            <Panel
              title="Perfil profissional"
              description="Dados exibidos em documentos, agenda e identificação do profissional."
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Nome completo" value={profile.full_name} onChange={(value) => setProfile({ ...profile, full_name: value })} />
                <Field label="Nome de exibição" value={profile.display_name} onChange={(value) => setProfile({ ...profile, display_name: value })} />
                <Field label="E-mail" value={profile.email} disabled onChange={() => undefined} />
                <Field label="Telefone" value={profile.phone} onChange={(value) => setProfile({ ...profile, phone: value })} />
                <Field label="Profissão" value={profile.profession} onChange={(value) => setProfile({ ...profile, profession: value })} />
                <Field label="Especialidade" value={profile.specialty} onChange={(value) => setProfile({ ...profile, specialty: value })} />
                <Field label="Registro profissional" value={profile.crp_number} onChange={(value) => setProfile({ ...profile, crp_number: value })} />
                <Field label="Duração padrão (min)" type="number" value={profile.default_session_duration} onChange={(value) => setProfile({ ...profile, default_session_duration: Number(value) })} />
                <Field label="Valor padrão da sessão" type="number" value={profile.default_session_value} onChange={(value) => setProfile({ ...profile, default_session_value: value })} />
                <label className="space-y-2">
                  <span className="text-xs font-semibold text-foreground">Modalidade padrão</span>
                  <select value={profile.default_modality} onChange={(event) => setProfile({ ...profile, default_modality: event.target.value as SettingsProfile["default_modality"] })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm">
                    <option value="in_person">Presencial</option>
                    <option value="online">Online</option>
                    <option value="hybrid">Híbrida</option>
                  </select>
                </label>
                <Field label="Fuso horário" value={profile.timezone} onChange={(value) => setProfile({ ...profile, timezone: value })} />
                <Field label="Idioma" value={profile.language} onChange={(value) => setProfile({ ...profile, language: value })} />
              </div>
              <label className="mt-4 block space-y-2">
                <span className="text-xs font-semibold text-foreground">Apresentação profissional</span>
                <textarea value={profile.bio} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} rows={5} className="w-full rounded-lg border border-border bg-background p-3 text-sm outline-none focus:border-primary" />
              </label>
              <div className="mt-5 flex justify-end">
                <Button onClick={saveProfile} disabled={updateProfile.isPending}>
                  {updateProfile.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                  Salvar perfil
                </Button>
              </div>
            </Panel>
          )}

          {active === "practice" && (
            <Panel
              title="Dados do consultório"
              description="Enquanto o projeto não possui uma entidade de clínica/equipe, estes dados pertencem à conta autenticada."
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Nome da clínica" value={profile.clinic_name} onChange={(value) => setProfile({ ...profile, clinic_name: value })} />
                <Field label="Nome fantasia" value={practice.trade_name} onChange={(value) => setPractice({ ...practice, trade_name: value })} />
                <Field label="CPF/CNPJ" value={practice.document} onChange={(value) => setPractice({ ...practice, document: value })} />
                <Field label="Telefone institucional" value={practice.phone} onChange={(value) => setPractice({ ...practice, phone: value })} />
                <Field label="E-mail institucional" type="email" value={practice.email} onChange={(value) => setPractice({ ...practice, email: value })} />
                <Field label="Moeda" value={practice.currency} onChange={(value) => setPractice({ ...practice, currency: value.toUpperCase().slice(0, 3) })} />
                <Field label="Fuso horário" value={practice.timezone} onChange={(value) => setPractice({ ...practice, timezone: value })} />
              </div>
              <div className="mt-5 flex justify-end gap-2">
                <Button variant="outline" onClick={saveProfile} disabled={updateProfile.isPending}>Salvar nome</Button>
                <Button onClick={savePractice} disabled={updatePractice.isPending}>
                  <Save className="mr-2 h-4 w-4" /> Salvar consultório
                </Button>
              </div>
            </Panel>
          )}

          {active === "agenda" && (
            <div className="space-y-5">
              <Panel title="Regras da agenda" description="Estas preferências são aplicadas ao cálculo de disponibilidade e à validação de novos agendamentos.">
                <div className="grid gap-4 sm:grid-cols-3">
                  <Field label="Intervalo entre sessões (min)" type="number" value={practice.appointment_interval_minutes} onChange={(value) => setPractice({ ...practice, appointment_interval_minutes: Number(value) })} />
                  <Field label="Antecedência mínima (h)" type="number" value={practice.minimum_booking_notice_hours} onChange={(value) => setPractice({ ...practice, minimum_booking_notice_hours: Number(value) })} />
                  <Field label="Prazo de cancelamento (h)" type="number" value={practice.cancellation_notice_hours} onChange={(value) => setPractice({ ...practice, cancellation_notice_hours: Number(value) })} />
                  <Field label="Lembrete padrão (min)" type="number" value={practice.reminder_minutes} onChange={(value) => setPractice({ ...practice, reminder_minutes: Number(value) })} />
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Toggle label="Permitir horários simultâneos" description="Remove apenas o conflito do profissional; paciente, sala e bloqueios continuam protegidos." checked={practice.allow_overbooking} onChange={(checked) => setPractice({ ...practice, allow_overbooking: checked })} />
                  <Toggle label="Lembretes automáticos" checked={practice.reminders_enabled} onChange={(checked) => setPractice({ ...practice, reminders_enabled: checked })} />
                  <Toggle label="Considerar feriados" description="Preferência registrada; o calendário de feriados ainda depende de integração futura." checked={practice.consider_holidays} onChange={(checked) => setPractice({ ...practice, consider_holidays: checked })} />
                </div>
                <div className="mt-5 flex justify-end"><Button onClick={savePractice}><Save className="mr-2 h-4 w-4" />Salvar regras</Button></div>
              </Panel>

              <Panel title="Horários de atendimento" description="Defina o expediente usado para sugerir horários livres.">
                {workingHoursQuery.isLoading ? <Skeleton className="h-64 w-full" /> : (
                  <div className="space-y-2">
                    {hours.map((item, index) => (
                      <div key={item.weekday} className="grid items-center gap-3 rounded-lg border border-border p-3 sm:grid-cols-[1fr_7rem_7rem_auto]">
                        <label className="flex items-center gap-2 text-sm font-semibold"><input type="checkbox" checked={item.is_active} onChange={(event) => setHours((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, is_active: event.target.checked } : row))} className="accent-primary" />{weekdays[item.weekday]}</label>
                        <input type="time" value={item.start_time} disabled={!item.is_active} onChange={(event) => setHours((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, start_time: event.target.value } : row))} className="h-9 rounded-lg border border-border bg-background px-2 text-xs" />
                        <input type="time" value={item.end_time} disabled={!item.is_active} onChange={(event) => setHours((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, end_time: event.target.value } : row))} className="h-9 rounded-lg border border-border bg-background px-2 text-xs" />
                        <span className="text-[10px] text-muted-foreground">{item.is_active ? "Ativo" : "Fechado"}</span>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-5 flex justify-end"><Button onClick={() => saveWorkingHours.mutate(hours)} disabled={saveWorkingHours.isPending}><Save className="mr-2 h-4 w-4" />Salvar horários</Button></div>
              </Panel>
            </div>
          )}

          {active === "communications" && (
            <Panel title="Comunicação interna" description="Controla avisos internos do sistema. O projeto ainda não possui chat entre profissionais, grupos ou anexos de conversa.">
              <div className="grid gap-3 sm:grid-cols-2">
                <Toggle label="Habilitar avisos internos" checked={practice.internal_communications_enabled} onChange={(checked) => setPractice({ ...practice, internal_communications_enabled: checked })} />
                <Toggle label="Mostrar prévia da mensagem" checked={practice.message_preview_enabled} onChange={(checked) => setPractice({ ...practice, message_preview_enabled: checked })} />
                <Toggle label="Marcar como lida ao abrir" checked={practice.auto_mark_read} onChange={(checked) => setPractice({ ...practice, auto_mark_read: checked })} />
                <Toggle label="Permitir menções" description="Preparação para futura comunicação entre membros da equipe." checked={practice.mentions_enabled} onChange={(checked) => setPractice({ ...practice, mentions_enabled: checked })} />
                <Toggle label="Notificar menções" checked={practice.notify_mentions} onChange={(checked) => setPractice({ ...practice, notify_mentions: checked })} disabled={!practice.mentions_enabled} />
                <Toggle label="Horário de silêncio" checked={practice.quiet_hours_enabled} onChange={(checked) => setPractice({ ...practice, quiet_hours_enabled: checked })} />
              </div>
              {practice.quiet_hours_enabled && (
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <Field label="Início do silêncio" type="time" value={practice.quiet_hours_start ?? "22:00"} onChange={(value) => setPractice({ ...practice, quiet_hours_start: value })} />
                  <Field label="Fim do silêncio" type="time" value={practice.quiet_hours_end ?? "07:00"} onChange={(value) => setPractice({ ...practice, quiet_hours_end: value })} />
                </div>
              )}
              <label className="mt-4 block space-y-2"><span className="text-xs font-semibold">Política de comunicação</span><textarea value={practice.communication_policy} onChange={(event) => setPractice({ ...practice, communication_policy: event.target.value })} rows={5} className="w-full rounded-lg border border-border bg-background p-3 text-sm" /></label>
              <div className="mt-5 flex justify-end"><Button onClick={savePractice}><Save className="mr-2 h-4 w-4" />Salvar comunicação</Button></div>
            </Panel>
          )}

          {active === "notifications" && (
            <Panel title="Preferências de notificações" description="O sistema funciona in-app e por e-mail. WhatsApp e push permanecem bloqueados até existir integração válida e consentimento.">
              <div className="grid gap-3 sm:grid-cols-2">
                <Toggle label="Notificações no sistema" checked={notificationPreferences.data.in_app_enabled} onChange={(checked) => updateNotificationPreferences.mutate({ in_app_enabled: checked })} />
                <Toggle label="Notificações por e-mail" checked={notificationPreferences.data.email_enabled} onChange={(checked) => updateNotificationPreferences.mutate({ email_enabled: checked })} />
                <Toggle label="WhatsApp" description="Indisponível até configurar um provedor oficial." checked={false} onChange={() => undefined} disabled />
                <Toggle label="Push" description="Preparado no modelo, mas ainda sem cliente push registrado." checked={false} onChange={() => undefined} disabled />
                <Toggle label="Horário de silêncio" checked={notificationPreferences.data.quiet_hours_enabled} onChange={(checked) => updateNotificationPreferences.mutate({ quiet_hours_enabled: checked })} />
                <Toggle label="Resumo diário" checked={notificationPreferences.data.daily_digest_enabled} onChange={(checked) => updateNotificationPreferences.mutate({ daily_digest_enabled: checked })} />
              </div>
              <div className="mt-5 overflow-x-auto rounded-lg border border-border">
                <table className="w-full min-w-[32rem] text-left text-xs">
                  <thead className="bg-secondary"><tr><th className="px-4 py-3">Categoria</th><th className="px-4 py-3 text-center">No sistema</th><th className="px-4 py-3 text-center">E-mail</th></tr></thead>
                  <tbody>
                    {notificationCategories.map(([category, label]) => {
                      const config = notificationPreferences.data.category_preferences[category] ?? {};
                      return (
                        <tr key={category} className="border-t border-border"><td className="px-4 py-3 font-semibold">{label}</td>{(["in_app", "email"] as const).map((channel) => (<td key={channel} className="px-4 py-3 text-center"><input type="checkbox" checked={config[channel] ?? (channel === "in_app" ? notificationPreferences.data.in_app_enabled : notificationPreferences.data.email_enabled)} onChange={(event) => updateNotificationPreferences.mutate({ category_preferences: { ...notificationPreferences.data.category_preferences, [category]: { ...config, [channel]: event.target.checked } } })} className="accent-primary" /></td>))}</tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="mt-4 text-xs text-muted-foreground">Alertas críticos de segurança podem continuar visíveis dentro do sistema para proteger a conta.</p>
            </Panel>
          )}

          {active === "security" && (
            <div className="space-y-5">
              <Panel title="Sessões ativas" description="Revogue dispositivos que você não reconhece. Tokens e identificadores internos não são exibidos.">
                {sessionsQuery.isLoading ? <Skeleton className="h-40 w-full" /> : (
                  <div className="space-y-2">
                    {sessionsQuery.data?.map((session) => (
                      <div key={session.public_id} className="flex flex-col gap-3 rounded-lg border border-border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-semibold">{session.user_agent || "Dispositivo não identificado"}</p><p className="mt-1 text-xs text-muted-foreground">Última atividade: {new Date(session.last_seen_at).toLocaleString("pt-BR")}{session.is_current ? " · Sessão atual" : ""}</p></div><Button variant="outline" disabled={session.is_current || revokeSession.isPending} onClick={() => revokeSession.mutate(session.public_id)}>Encerrar</Button></div>
                    ))}
                  </div>
                )}
              </Panel>
              <Panel title="Alterar senha" description="A alteração revoga todas as sessões existentes por segurança.">
                <div className="grid gap-4 sm:grid-cols-3"><Field label="Senha atual" type="password" value={password.current_password} onChange={(value) => setPassword({ ...password, current_password: value })} /><Field label="Nova senha" type="password" value={password.new_password} onChange={(value) => setPassword({ ...password, new_password: value })} /><Field label="Confirmar nova senha" type="password" value={password.new_password_confirm} onChange={(value) => setPassword({ ...password, new_password_confirm: value })} /></div>
                <div className="mt-5 flex justify-end"><Button onClick={changePassword}><KeyRound className="mr-2 h-4 w-4" />Alterar senha</Button></div>
              </Panel>
            </div>
          )}

          {active === "integrations" && (
            <Panel title="Integrações" description="A saúde operacional das integrações permanece em uma rota administrativa dedicada.">
              <Link href="/dashboard/configuracoes/integracoes" className="inline-flex rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">Abrir integrações</Link>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
