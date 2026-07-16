import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { toast } from "sonner";

import type {
  ClinicalEvolutionTemplate,
  EvolutionAttachment,
  EvolutionModalPayload,
  PendingEvolutionAttachment,
} from "../evolution-modal.types";
import { evolutionModalService } from "../services/evolution-modal.service";
import type {
  EvolutionEditorFormState,
  EvolutionEditorProps,
  EvolutionWithModalData,
} from "../components/evolution-editor/evolution-editor.types";
import {
  createEvolutionEditorForm,
  formatEvolutionDate,
  getEvolutionApiErrors,
  getEvolutionApiMessage,
  toDateInput,
} from "../components/evolution-editor/evolution-editor.utils";

export function useEvolutionEditorController(props: EvolutionEditorProps) {
  const { patientId: patientParam } = useParams<{ patientId: string }>();
  const patientId = Number(patientParam);
  const queryClient = useQueryClient();
  const dialogRef = useRef<HTMLDivElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const templateButtonRef = useRef<HTMLButtonElement>(null);
  const pendingFilesRef = useRef<PendingEvolutionAttachment[]>([]);
  const modalEvolution = props.evolution as
    | EvolutionWithModalData
    | null
    | undefined;
  const editing = Boolean(modalEvolution?.id);

  const [form, setForm] = useState<EvolutionEditorFormState>(() =>
    createEvolutionEditorForm(modalEvolution),
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

  const changeForm = useCallback(
    <K extends keyof EvolutionEditorFormState>(
      key: K,
      value: EvolutionEditorFormState[K],
    ) => {
      setForm((current) => ({ ...current, [key]: value }));
      setDirty(true);
      setErrors((current) => ({ ...current, [key]: "", form: "" }));
    },
    [],
  );

  const requestClose = useCallback(() => {
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
  }, [busy, dirty, props]);

  useEffect(() => {
    if (!props.open) return;
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    setForm(createEvolutionEditorForm(modalEvolution));
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
  }, [props.open, requestClose]);

  useEffect(() => {
    pendingFilesRef.current = pendingFiles;
  }, [pendingFiles]);

  useEffect(
    () => () => {
      pendingFilesRef.current.forEach((item) => {
        if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
      });
    },
    [],
  );

  function selectAppointment(value: string) {
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
        `A consulta ocorreu em ${formatEvolutionDate(selected.start_time)}. Deseja atualizar a data do atendimento para esta data?`,
      );
    setForm((current) => ({
      ...current,
      appointment: value,
      sessionDate: shouldReplaceDate ? suggestedDate : current.sessionDate,
      dateOverrideConfirmed: !shouldReplaceDate,
    }));
    setDirty(true);
  }

  function chooseTemplate(template: ClinicalEvolutionTemplate) {
    setTemplateMenuOpen(false);
    if (!form.content.trim()) {
      changeForm("content", template.content);
      return;
    }
    setPendingTemplate(template);
  }

  function applyTemplate(mode: "replace" | "append") {
    if (!pendingTemplate) return;
    changeForm(
      "content",
      mode === "replace"
        ? pendingTemplate.content
        : `${form.content.trim()}\n\n${pendingTemplate.content}`,
    );
    setPendingTemplate(null);
  }

  function validate() {
    const next: Record<string, string> = {};
    if (!form.sessionDate) next.sessionDate = "Informe a data do atendimento.";
    if (!form.content.trim()) {
      next.content = "Informe a evolução ou as anotações.";
    }
    if (dateDiffersFromAppointment && !form.dateOverrideConfirmed) {
      next.sessionDate =
        "Confirme a alteração manual da data vinculada à consulta.";
    }
    if (pendingFiles.some((item) => item.error)) {
      next.attachments = "Remova ou corrija os arquivos inválidos.";
    }
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
  }

  async function submit() {
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
                    error: getEvolutionApiMessage(
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
      const apiErrors = getEvolutionApiErrors(error);
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
  }

  function updatePendingFiles(files: PendingEvolutionAttachment[]) {
    setPendingFiles(files);
    setDirty(true);
    setErrors((current) => ({ ...current, attachments: "" }));
  }

  function removeExistingAttachment(id: number) {
    setRemovedAttachmentIds((current) => [...current, id]);
    setDirty(true);
  }

  return {
    dialogRef,
    templateButtonRef,
    form,
    setForm,
    pendingFiles,
    existingAttachments,
    removedAttachmentIds,
    errors,
    pendingTemplate,
    setPendingTemplate,
    templateMenuOpen,
    setTemplateMenuOpen,
    appointmentQuery,
    templatesQuery,
    appointmentOptions,
    linkedAppointmentDate,
    dateDiffersFromAppointment,
    editing,
    busy,
    submitting,
    persistedEvolutionId,
    changeForm,
    requestClose,
    selectAppointment,
    chooseTemplate,
    applyTemplate,
    submit,
    updatePendingFiles,
    removeExistingAttachment,
    todayDate: toDateInput(new Date()),
  };
}

export type EvolutionEditorController = ReturnType<
  typeof useEvolutionEditorController
>;
