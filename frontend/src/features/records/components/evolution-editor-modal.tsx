"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CalendarDays,
  ChevronDown,
  FileText,
  Link2,
  LockKeyhole,
  ShieldCheck,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { EvolutionPayload, EvolutionWorkspace } from "../types";
import type {
  ClinicalEvolutionTemplate,
  EvolutionAppointmentOption,
  EvolutionAttachment,
  EvolutionModalPayload,
  PendingEvolutionAttachment,
} from "../evolution-modal.types";
import { evolutionModalService } from "../services/evolution-modal.service";
import { ClinicalMarkdownEditor } from "./clinical-markdown-editor";
import { EvolutionAttachmentDropzone } from "./evolution-attachment-dropzone";

interface EvolutionEditorProps {
  open: boolean;
  evolution?: EvolutionWorkspace | null;
  saving: boolean;
  finalizing: boolean;
  onClose: () => void;
  onSave: (payload: EvolutionPayload) => Promise<void>;
  onFinalize: (id: number) => Promise<void>;
}

type EvolutionWithModalData = EvolutionWorkspace & {
  attachments?: EvolutionAttachment[];
  appointment_data?: EvolutionAppointmentOption | null;
  content_format?: "markdown" | "plain_text";
};

interface FormState {
  appointment: string;
  sessionDate: string;
  content: string;
  confidential: boolean;
  dateOverrideConfirmed: boolean;
}

const fieldClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15 disabled:cursor-not-allowed disabled:opacity-60";

export function EvolutionEditor(props: EvolutionEditorProps) {
  const { patientId: patientParam } = useParams<{ patientId: string }>();
  const patientId = Number(patientParam);
  const queryClient = useQueryClient();
  const dialogRef = useRef<HTMLDivElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const templateButtonRef = useRef<HTMLButtonElement>(null);
  const modalEvolution = props.evolution as
    | EvolutionWithModalData
    | null
    | undefined;
  const editing = Boolean(modalEvolution?.id);
  const [form, setForm] = useState<FormState>(() =>
    initialForm(modalEvolution),
  );
  const [pendingFiles, setPendingFiles] = useState<
    PendingEvolutionAttachment[]
  >([]);
  const [existingAttachments, setExistingAttachments] = useState<
    EvolutionAttachment[]
  >([]);
  const [removedAttachmentIds, setRemovedAttachmentIds] = useState<number[]>(
    [],
  );
  const [dirty, setDirty] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [persistedEvolutionId, setPersistedEvolutionId] = useState<
    number | null
  >(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [templateMenuOpen, setTemplateMenuOpen] = useState(false);
  const [pendingTemplate, setPendingTemplate] =
    useState<ClinicalEvolutionTemplate | null>(null);

  const appointmentQuery = useQuery({
    queryKey: ["record-workspace", patientId, "evolution-appointments"],
    queryFn: () => evolutionModalService.listAppointments(patientId),
    enabled: props.open && Number.isFinite(patientId) && patientId > 0,
    staleTime: 15_000,
  });
  const templatesQuery = useQuery({
    queryKey: ["record-workspace", "clinical-templates"],
    queryFn: evolutionModalService.listTemplates,
    enabled: props.open,
    staleTime: 60_000,
  });

  const currentAppointment = useMemo(() => {
    if (!form.appointment) return null;
    const currentData = modalEvolution?.appointment_data;
    if (currentData?.id === Number(form.appointment)) return currentData;
    return (
      appointmentQuery.data?.find(
        (item) => item.id === Number(form.appointment),
      ) ?? null
    );
  }, [
    appointmentQuery.data,
    form.appointment,
    modalEvolution?.appointment_data,
  ]);

  const appointmentOptions = useMemo(() => {
    const options = appointmentQuery.data ? [...appointmentQuery.data] : [];
    const currentData = modalEvolution?.appointment_data;
    if (currentData && !options.some((item) => item.id === currentData.id)) {
      options.unshift(currentData);
    }
    return options;
  }, [appointmentQuery.data, modalEvolution?.appointment_data]);

  const busy = submitting || props.saving || props.finalizing;
  const linkedAppointmentDate = currentAppointment
    ? toDateInput(new Date(currentAppointment.start_time))
    : null;
  const dateDiffersFromAppointment = Boolean(
    linkedAppointmentDate && form.sessionDate !== linkedAppointmentDate,
  );

  useEffect(() => {
    if (!props.open) return;
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    setForm(initialForm(modalEvolution));
    setExistingAttachments(modalEvolution?.attachments ?? []);
    setPendingFiles([]);
    setRemovedAttachmentIds([]);
    setPersistedEvolutionId(modalEvolution?.id ?? null);
    setErrors({});
    setDirty(false);
    setTemplateMenuOpen(false);
    setPendingTemplate(null);
  }, [props.open, modalEvolution]);

  useEffect(() => {
    if (!props.open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const dialog = dialogRef.current;
    const firstFocusable = dialog?.querySelector<HTMLElement>(
      "button:not([disabled]), select:not([disabled]), input:not([disabled]), textarea:not([disabled])",
    );
    requestAnimationFrame(() => firstFocusable?.focus());

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        requestClose();
        return;
      }
      if (event.key !== "Tab" || !dialog) return;
      const focusable = Array.from(
        dialog.querySelectorAll<HTMLElement>(
          "button:not([disabled]), select:not([disabled]), input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])",
        ),
      ).filter((item) => item.offsetParent !== null);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
      returnFocusRef.current?.focus();
    };
    // requestClose intentionally reads the current state through the render closure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.open, dirty, busy]);

  useEffect(
    () => () => {
      pendingFiles.forEach((item) => {
        if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
      });
    },
    [pendingFiles],
  );

  const changeForm = <K extends keyof FormState>(
    key: K,
    value: FormState[K],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
    setDirty(true);
    setErrors((current) => ({ ...current, [key]: "", form: "" }));
  };

  const requestClose = () => {
    if (busy) return;
    if (
      dirty &&
      !window.confirm(
        "Há alterações não salvas. Deseja fechar e descartar o preenchimento?",
      )
    ) {
      return;
    }
    props.onClose();
  };

  const selectAppointment = (value: string) => {
    if (!value) {
      changeForm("appointment", "");
      setForm((current) => ({ ...current, dateOverrideConfirmed: false }));
      return;
    }
    const selected = appointmentOptions.find(
      (item) => item.id === Number(value),
    );
    if (!selected) return;
    const suggestedDate = toDateInput(new Date(selected.start_time));
    const shouldReplaceDate =
      form.sessionDate === suggestedDate ||
      !dirty ||
      window.confirm(
        `A consulta ocorreu em ${formatDate(selected.start_time)}. Deseja atualizar a data do atendimento para esta data?`,
      );
    setForm((current) => ({
      ...current,
      appointment: value,
      sessionDate: shouldReplaceDate ? suggestedDate : current.sessionDate,
      dateOverrideConfirmed: !shouldReplaceDate,
    }));
    setDirty(true);
  };

  const chooseTemplate = (template: ClinicalEvolutionTemplate) => {
    setTemplateMenuOpen(false);
    if (!form.content.trim()) {
      changeForm("content", template.content);
      return;
    }
    setPendingTemplate(template);
  };

  const applyTemplate = (mode: "replace" | "append") => {
    if (!pendingTemplate) return;
    changeForm(
      "content",
      mode === "replace"
        ? pendingTemplate.content
        : `${form.content.trim()}\n\n${pendingTemplate.content}`,
    );
    setPendingTemplate(null);
  };

  const validate = () => {
    const next: Record<string, string> = {};
    if (!form.sessionDate) next.sessionDate = "Informe a data do atendimento.";
    if (!form.content.trim())
      next.content = "Informe a evolução ou as anotações.";
    if (dateDiffersFromAppointment && !form.dateOverrideConfirmed) {
      next.sessionDate =
        "Confirme a alteração manual da data vinculada à consulta.";
    }
    const invalidFile = pendingFiles.find((item) => item.error);
    if (invalidFile)
      next.attachments = "Remova ou corrija os arquivos inválidos.";
    setErrors(next);
    if (Object.keys(next).length) {
      requestAnimationFrame(() => {
        dialogRef.current
          ?.querySelector<HTMLElement>("[aria-invalid='true']")
          ?.focus();
      });
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) return;
    setSubmitting(true);
    setErrors({});
    let evolutionId = persistedEvolutionId ?? modalEvolution?.id ?? null;
    try {
      const payload: EvolutionModalPayload = {
        appointment: form.appointment ? Number(form.appointment) : null,
        session_date: form.sessionDate,
        content: form.content,
        therapist_observations: form.content,
        content_format: "markdown",
        is_confidential: form.confidential,
        confirm_appointment_date_override:
          dateDiffersFromAppointment && form.dateOverrideConfirmed,
      };
      const saved = evolutionId
        ? await evolutionModalService.update(evolutionId, payload)
        : await evolutionModalService.create(patientId, payload);
      evolutionId = saved.id;
      setPersistedEvolutionId(saved.id);

      for (const attachmentId of removedAttachmentIds) {
        await evolutionModalService.removeAttachment(saved.id, attachmentId);
      }

      const failedIds = new Set<string>();
      const uploaded: EvolutionAttachment[] = [];
      for (const item of pendingFiles) {
        if (item.error) {
          failedIds.add(item.id);
          continue;
        }
        try {
          const result = await evolutionModalService.uploadAttachment(
            saved.id,
            item.file,
            (progress) =>
              setPendingFiles((current) =>
                current.map((candidate) =>
                  candidate.id === item.id
                    ? { ...candidate, progress }
                    : candidate,
                ),
              ),
          );
          uploaded.push(result);
          if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
        } catch (error) {
          failedIds.add(item.id);
          setPendingFiles((current) =>
            current.map((candidate) =>
              candidate.id === item.id
                ? {
                    ...candidate,
                    progress: 0,
                    error: getApiMessage(
                      error,
                      "Falha ao enviar este arquivo.",
                    ),
                  }
                : candidate,
            ),
          );
        }
      }

      if (uploaded.length) {
        setExistingAttachments((current) => [...current, ...uploaded]);
      }
      setPendingFiles((current) =>
        current.filter((item) => failedIds.has(item.id)),
      );
      setRemovedAttachmentIds([]);

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["record-workspace", patientId, "evolutions"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["record-workspace", patientId, "summary"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["record-workspace", patientId, "documents"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["record-workspace", "evolution", saved.id],
        }),
      ]);

      if (failedIds.size) {
        setDirty(true);
        setErrors({
          attachments:
            "A evolução foi salva, mas um ou mais anexos falharam. Corrija e tente novamente.",
        });
        toast.warning("Evolução salva com anexos pendentes.");
        return;
      }

      setDirty(false);
      toast.success(editing ? "Evolução atualizada." : "Evolução adicionada.");
      props.onClose();
    } catch (error) {
      const apiErrors = getApiErrors(error);
      setErrors(apiErrors);
      toast.error("Não foi possível salvar a evolução.", {
        description: apiErrors.form || Object.values(apiErrors)[0],
      });
      requestAnimationFrame(() => {
        dialogRef.current
          ?.querySelector<HTMLElement>("[aria-invalid='true']")
          ?.focus();
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (!props.open) return null;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-0 backdrop-blur-[2px] sm:p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) requestClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="evolution-modal-title"
        aria-describedby="evolution-modal-description"
        className="flex h-full w-full flex-col overflow-hidden border-border bg-card shadow-2xl sm:h-auto sm:max-h-[94vh] sm:max-w-2xl sm:rounded-xl sm:border"
      >
        <header className="flex shrink-0 items-start justify-between border-b border-border px-5 py-4">
          <div>
            <h2
              id="evolution-modal-title"
              className="text-base font-bold text-foreground"
            >
              {editing ? "Editar Evolução" : "Nova Evolução"}
            </h2>
            <p
              id="evolution-modal-description"
              className="mt-1 text-xs text-muted-foreground"
            >
              {editing
                ? "Atualize os dados permitidos deste registro clínico."
                : "Adicione uma nova evolução ao prontuário do paciente."}
            </p>
          </div>
          <button
            type="button"
            onClick={requestClose}
            disabled={busy}
            aria-label="Fechar modal"
            className="grid size-8 place-items-center rounded-md text-muted-foreground transition hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50"
          >
            <X className="size-4" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="space-y-5">
            <section className="space-y-2">
              <label
                htmlFor="evolution-appointment"
                className="flex items-center gap-2 text-xs font-semibold text-foreground"
              >
                <Link2 className="size-4 text-muted-foreground" />
                Vincular a Consulta
              </label>
              <select
                id="evolution-appointment"
                value={form.appointment}
                onChange={(event) => selectAppointment(event.target.value)}
                disabled={busy || appointmentQuery.isLoading}
                className={fieldClass}
              >
                <option value="">
                  {appointmentQuery.isLoading
                    ? "Carregando consultas..."
                    : "Sem vínculo"}
                </option>
                {appointmentOptions.map((appointment) => (
                  <option key={appointment.id} value={appointment.id}>
                    {formatAppointmentOption(appointment)}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-muted-foreground">
                Vincule esta evolução a uma consulta específica do paciente.
              </p>
              {appointmentQuery.isError && (
                <p role="alert" className="text-[11px] text-destructive">
                  Não foi possível carregar as consultas. O registro ainda pode
                  ser criado sem vínculo.
                </p>
              )}
            </section>

            <section className="space-y-2">
              <label
                htmlFor="evolution-session-date"
                className="flex items-center gap-2 text-xs font-semibold text-foreground"
              >
                <CalendarDays className="size-4 text-muted-foreground" />
                Data do Atendimento
              </label>
              <input
                id="evolution-session-date"
                type="date"
                value={form.sessionDate}
                max={toDateInput(new Date())}
                onChange={(event) => {
                  changeForm("sessionDate", event.target.value);
                  setForm((current) => ({
                    ...current,
                    dateOverrideConfirmed: false,
                  }));
                }}
                disabled={busy}
                required
                aria-invalid={Boolean(errors.sessionDate)}
                aria-describedby={
                  errors.sessionDate
                    ? "evolution-session-date-error"
                    : undefined
                }
                className={cn(
                  fieldClass,
                  errors.sessionDate && "border-destructive",
                )}
              />
              {dateDiffersFromAppointment && (
                <label className="flex items-start gap-2 rounded-md border border-amber-500/25 bg-amber-500/10 p-3 text-[11px] text-foreground">
                  <input
                    type="checkbox"
                    checked={form.dateOverrideConfirmed}
                    onChange={(event) =>
                      changeForm("dateOverrideConfirmed", event.target.checked)
                    }
                    disabled={busy}
                    className="mt-0.5"
                  />
                  Confirmo que a data informada difere da consulta vinculada (
                  {linkedAppointmentDate
                    ? formatDate(`${linkedAppointmentDate}T12:00:00`)
                    : "data não disponível"}
                  ).
                </label>
              )}
              {errors.sessionDate && (
                <p
                  id="evolution-session-date-error"
                  role="alert"
                  className="text-[11px] text-destructive"
                >
                  {errors.sessionDate}
                </p>
              )}
            </section>

            <section className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label className="text-xs font-semibold text-foreground">
                  Evolução / Anotações{" "}
                  <span className="text-destructive">*</span>
                </label>
                <div className="relative">
                  <Button
                    ref={templateButtonRef}
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => setTemplateMenuOpen((value) => !value)}
                    disabled={busy}
                    leftIcon={<FileText className="size-3.5" />}
                    rightIcon={<ChevronDown className="size-3.5" />}
                  >
                    Usar Template
                  </Button>
                  {templateMenuOpen && (
                    <div className="absolute right-0 top-11 z-20 max-h-64 w-72 overflow-y-auto rounded-lg border border-border bg-popover p-1 shadow-xl">
                      {templatesQuery.isLoading ? (
                        <p className="px-3 py-4 text-xs text-muted-foreground">
                          Carregando templates...
                        </p>
                      ) : templatesQuery.isError ? (
                        <p className="px-3 py-4 text-xs text-destructive">
                          Falha ao carregar templates.
                        </p>
                      ) : templatesQuery.data?.length ? (
                        templatesQuery.data.map((template) => (
                          <button
                            key={template.id}
                            type="button"
                            onClick={() => chooseTemplate(template)}
                            className="w-full rounded-md px-3 py-2 text-left transition hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                          >
                            <strong className="block text-xs text-foreground">
                              {template.name}
                            </strong>
                            <span className="mt-0.5 block text-[10px] text-muted-foreground">
                              {template.is_system
                                ? "Template da clínica"
                                : "Meu template"}
                            </span>
                          </button>
                        ))
                      ) : (
                        <p className="px-3 py-4 text-xs text-muted-foreground">
                          Nenhum template disponível.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {pendingTemplate && (
                <div className="rounded-lg border border-primary/25 bg-primary/5 p-3">
                  <p className="text-xs font-semibold text-foreground">
                    Como aplicar “{pendingTemplate.name}”?
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => applyTemplate("replace")}
                    >
                      Substituir texto
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => applyTemplate("append")}
                    >
                      Anexar ao final
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setPendingTemplate(null)}
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}

              <ClinicalMarkdownEditor
                value={form.content}
                onChange={(value) => changeForm("content", value)}
                error={errors.content}
                disabled={busy}
              />
              {errors.content && (
                <p
                  id="evolution-content-error"
                  role="alert"
                  className="text-[11px] text-destructive"
                >
                  {errors.content}
                </p>
              )}
            </section>

            <section>
              <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-secondary/10 p-4">
                <input
                  type="checkbox"
                  checked={form.confidential}
                  onChange={(event) =>
                    changeForm("confidential", event.target.checked)
                  }
                  disabled={busy}
                  aria-describedby="evolution-confidential-description"
                  className="mt-0.5 size-4 rounded border-border"
                />
                <span>
                  <strong className="flex items-center gap-2 text-xs text-foreground">
                    <LockKeyhole className="size-3.5 text-muted-foreground" />
                    Marcar como confidencial
                  </strong>
                  <span
                    id="evolution-confidential-description"
                    className="mt-1 block text-[11px] leading-4 text-muted-foreground"
                  >
                    Apenas você (autor) e administradores com permissão clínica
                    explícita poderão visualizar esta evolução. Secretárias e
                    outros profissionais não autorizados não terão acesso.
                  </span>
                </span>
              </label>
            </section>

            <section className="space-y-2">
              <label className="text-xs font-semibold text-foreground">
                Anexos
              </label>
              <EvolutionAttachmentDropzone
                pending={pendingFiles}
                existing={existingAttachments}
                removedExistingIds={removedAttachmentIds}
                onPendingChange={(files) => {
                  setPendingFiles(files);
                  setDirty(true);
                  setErrors((current) => ({ ...current, attachments: "" }));
                }}
                onRemoveExisting={(id) => {
                  setRemovedAttachmentIds((current) => [...current, id]);
                  setDirty(true);
                }}
                disabled={busy}
              />
              {errors.attachments && (
                <p role="alert" className="text-[11px] text-destructive">
                  {errors.attachments}
                </p>
              )}
            </section>

            <div className="flex items-start gap-2 rounded-lg border border-primary/20 bg-primary/5 p-3 text-[11px] text-muted-foreground">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />O
              conteúdo é enviado somente ao servidor autenticado, armazenado de
              forma criptografada e registrado em auditoria. Nenhum texto
              clínico é salvo no navegador.
            </div>

            {errors.form && (
              <p
                role="alert"
                aria-live="assertive"
                className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive"
              >
                {errors.form}
              </p>
            )}
          </div>
        </div>

        <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-border bg-card px-5 py-3">
          <Button
            type="button"
            variant="outline"
            onClick={requestClose}
            disabled={busy}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={submit}
            isLoading={submitting}
            disabled={busy || !form.content.trim() || !form.sessionDate}
          >
            {editing || persistedEvolutionId
              ? "Salvar Alterações"
              : "Adicionar Registro"}
          </Button>
        </footer>
      </div>
    </div>
  );
}

function initialForm(evolution?: EvolutionWithModalData | null): FormState {
  return {
    appointment: evolution?.appointment ? String(evolution.appointment) : "",
    sessionDate: evolution?.session_date || toDateInput(new Date()),
    content: evolution?.content || evolution?.therapist_observations || "",
    confidential: Boolean(evolution?.is_confidential),
    dateOverrideConfirmed: false,
  };
}

function toDateInput(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function formatAppointmentOption(item: EvolutionAppointmentOption) {
  const start = new Date(item.start_time);
  return `${start.toLocaleDateString("pt-BR")} às ${start.toLocaleTimeString(
    "pt-BR",
    { hour: "2-digit", minute: "2-digit" },
  )} — ${item.type_display} · ${item.therapist_name} · ${item.status_display}`;
}

function getApiErrors(error: unknown): Record<string, string> {
  if (!error || typeof error !== "object" || !("response" in error)) {
    return {
      form: "Falha de conexão. Verifique sua internet e tente novamente.",
    };
  }
  const data = (error as { response?: { data?: unknown; status?: number } })
    .response?.data;
  const status = (error as { response?: { status?: number } }).response?.status;
  if (status === 401) return { form: "Sua sessão expirou. Entre novamente." };
  if (status === 403)
    return { form: "Você não possui permissão para esta ação." };
  if (status === 409)
    return {
      form: "O registro foi alterado por outro usuário. Recarregue a página.",
    };
  if (!data || typeof data !== "object") {
    return { form: "O servidor não conseguiu concluir a operação." };
  }
  const result: Record<string, string> = {};
  Object.entries(data as Record<string, unknown>).forEach(([key, value]) => {
    if (typeof value === "string") result[normalizeErrorKey(key)] = value;
    else if (Array.isArray(value) && typeof value[0] === "string") {
      result[normalizeErrorKey(key)] = value[0];
    }
  });
  if (!Object.keys(result).length)
    result.form = "Revise os dados e tente novamente.";
  return result;
}

function normalizeErrorKey(key: string) {
  if (key === "session_date") return "sessionDate";
  if (key === "non_field_errors" || key === "detail") return "form";
  return key;
}

function getApiMessage(error: unknown, fallback: string) {
  const messages = getApiErrors(error);
  return messages.form || Object.values(messages)[0] || fallback;
}

export function handleEditorShortcut(
  event: ReactKeyboardEvent,
  action: () => void,
) {
  if (event.key === "Enter") action();
}
