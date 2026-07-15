"use client";

import { useEffect, useState } from "react";
import { FileCheck2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import type { Patient } from "@/types";
import type { DocumentTemplate, GeneratedDocument } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  patients: Patient[];
  templates: DocumentTemplate[];
  initialPatientId?: number;
  submitting?: boolean;
  onCreate: (
    payload: {
      template_public_id: string;
      patient_id: number;
      title?: string;
      local_emissao?: string;
    },
    generateNow: boolean,
  ) => Promise<GeneratedDocument | void>;
}

const fieldClass =
  "h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20";

export function GenerateDocumentModal({
  open,
  onClose,
  patients,
  templates,
  initialPatientId,
  submitting,
  onCreate,
}: Props) {
  const [patientId, setPatientId] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [title, setTitle] = useState("");
  const [localEmissao, setLocalEmissao] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setPatientId(initialPatientId ? String(initialPatientId) : "");
    setTemplateId("");
    setTitle("");
    setLocalEmissao("");
    setError("");
  }, [initialPatientId, open]);

  const submit = async (generateNow: boolean) => {
    if (!patientId || !templateId) {
      setError("Selecione o paciente e o template.");
      return;
    }
    setError("");
    await onCreate(
      {
        patient_id: Number(patientId),
        template_public_id: templateId,
        title,
        local_emissao: localEmissao,
      },
      generateNow,
    );
  };

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Gerar documento"
      description="Selecione um modelo e revise o rascunho antes de concluir a emissão."
      className="max-w-xl"
    >
      <div className="space-y-4">
        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          Paciente <span className="text-danger">*</span>
          <select
            className={fieldClass}
            value={patientId}
            onChange={(event) => setPatientId(event.target.value)}
          >
            <option value="">Selecione um paciente</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.social_name || patient.full_name}
              </option>
            ))}
          </select>
        </label>
        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          Template <span className="text-danger">*</span>
          <select
            className={fieldClass}
            value={templateId}
            onChange={(event) => {
              const value = event.target.value;
              setTemplateId(value);
              const selected = templates.find(
                (item) => item.public_id === value,
              );
              if (selected && !title) setTitle(selected.name);
            }}
          >
            <option value="">Selecione um template ativo</option>
            {templates
              .filter((template) => template.status === "active")
              .map((template) => (
                <option key={template.public_id} value={template.public_id}>
                  {template.name}
                </option>
              ))}
          </select>
        </label>
        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          Título do documento
          <input
            className={fieldClass}
            value={title}
            maxLength={200}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Usa o nome do template quando vazio"
          />
        </label>
        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          Local de emissão
          <input
            className={fieldClass}
            value={localEmissao}
            maxLength={160}
            onChange={(event) => setLocalEmissao(event.target.value)}
            placeholder="Ex.: São Gonçalo/RJ"
          />
        </label>
        {error && (
          <p
            role="alert"
            className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger"
          >
            {error}
          </p>
        )}
        <p className="rounded-lg border border-primary/15 bg-primary/5 px-3 py-2 text-[11px] leading-5 text-muted-foreground">
          O conteúdo final é salvo como snapshot. Alterações posteriores no
          template não modificam documentos já criados.
        </p>
        <div className="flex flex-col-reverse justify-end gap-2 border-t border-border pt-4 sm:flex-row">
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            variant="secondary"
            size="sm"
            isLoading={submitting}
            leftIcon={<Save className="h-4 w-4" />}
            onClick={() => submit(false)}
          >
            Salvar rascunho
          </Button>
          <Button
            size="sm"
            isLoading={submitting}
            leftIcon={<FileCheck2 className="h-4 w-4" />}
            onClick={() => submit(true)}
          >
            Gerar PDF
          </Button>
        </div>
      </div>
    </Modal>
  );
}
