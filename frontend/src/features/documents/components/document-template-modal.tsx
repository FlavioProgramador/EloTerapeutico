"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Braces, FileText, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import type {
  DocumentTemplate,
  DocumentTemplatePayload,
  EvolutionTemplate,
  EvolutionTemplatePayload,
  PlaceholderDefinition,
} from "../types";

const documentTypes: Array<{ value: DocumentTemplatePayload["document_type"]; label: string }> = [
  { value: "declaration", label: "Declaração" },
  { value: "report", label: "Relatório" },
  { value: "referral", label: "Encaminhamento" },
  { value: "certificate", label: "Atestado" },
  { value: "consent", label: "Termo de consentimento" },
  { value: "other", label: "Outro" },
];

const inputClass =
  "h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20";
const textareaClass =
  "w-full resize-y rounded-lg border border-border bg-background px-3 py-2.5 text-sm leading-6 text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20";

interface DocumentTemplateModalProps {
  open: boolean;
  onClose: () => void;
  initial?: DocumentTemplate | null;
  placeholders: PlaceholderDefinition[];
  submitting?: boolean;
  onSubmit: (payload: DocumentTemplatePayload) => Promise<void>;
}

export function DocumentTemplateModal({
  open,
  onClose,
  initial,
  placeholders,
  submitting,
  onSubmit,
}: DocumentTemplateModalProps) {
  const contentRef = useRef<HTMLTextAreaElement>(null);
  const [form, setForm] = useState<DocumentTemplatePayload>({
    name: "",
    description: "",
    category: "Declaração",
    document_type: "declaration",
    specialty: "",
    content: "",
    header_content: "",
    footer_content: "",
    include_professional_identification: true,
    include_clinic_identification: true,
    requires_signature: true,
    status: "active",
  });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    setForm({
      name: initial?.name ?? "",
      description: initial?.description ?? "",
      category: initial?.category ?? "Declaração",
      document_type: initial?.document_type ?? "declaration",
      specialty: initial?.specialty ?? "",
      content: initial?.content ?? "",
      header_content: initial?.header_content ?? "",
      footer_content: initial?.footer_content ?? "",
      include_professional_identification:
        initial?.include_professional_identification ?? true,
      include_clinic_identification: initial?.include_clinic_identification ?? true,
      requires_signature: initial?.requires_signature ?? true,
      status: initial?.status ?? "active",
    });
  }, [initial, open]);

  const grouped = useMemo(() => {
    return placeholders.reduce<Record<string, PlaceholderDefinition[]>>((acc, placeholder) => {
      (acc[placeholder.group] ??= []).push(placeholder);
      return acc;
    }, {});
  }, [placeholders]);

  const insertPlaceholder = (token: string) => {
    const textarea = contentRef.current;
    if (!textarea) {
      setForm((current) => ({ ...current, content: `${current.content}${token}` }));
      return;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const next = `${form.content.slice(0, start)}${token}${form.content.slice(end)}`;
    setForm((current) => ({ ...current, content: next }));
    requestAnimationFrame(() => {
      textarea.focus();
      textarea.setSelectionRange(start + token.length, start + token.length);
    });
  };

  const submit = async () => {
    if (!form.name.trim() || !form.category.trim() || !form.content.trim()) {
      setError("Preencha nome, categoria e conteúdo do template.");
      return;
    }
    setError("");
    await onSubmit(form);
  };

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title={initial ? "Editar template" : "Novo template"}
      description="Crie um modelo seguro com variáveis controladas para agilizar a emissão."
      className="max-w-4xl"
    >
      <div className="space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Nome do template <span className="text-danger">*</span>
            <input
              className={inputClass}
              value={form.name}
              maxLength={160}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Ex.: Declaração de acompanhamento"
            />
          </label>
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Categoria <span className="text-danger">*</span>
            <input
              className={inputClass}
              value={form.category}
              maxLength={100}
              onChange={(event) => setForm({ ...form, category: event.target.value })}
              placeholder="Ex.: Declaração"
            />
          </label>
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Tipo do documento
            <select
              className={inputClass}
              value={form.document_type}
              onChange={(event) =>
                setForm({
                  ...form,
                  document_type: event.target.value as DocumentTemplatePayload["document_type"],
                })
              }
            >
              {documentTypes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Especialidade
            <input
              className={inputClass}
              value={form.specialty}
              maxLength={120}
              onChange={(event) => setForm({ ...form, specialty: event.target.value })}
              placeholder="Ex.: Psicologia"
            />
          </label>
        </div>

        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          Descrição
          <input
            className={inputClass}
            value={form.description}
            maxLength={500}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            placeholder="Explique quando este modelo deve ser utilizado."
          />
        </label>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_17rem]">
          <label className="block space-y-1.5 text-xs font-semibold text-foreground">
            Conteúdo do template <span className="text-danger">*</span>
            <textarea
              ref={contentRef}
              className={`${textareaClass} min-h-72 font-mono text-xs`}
              value={form.content}
              maxLength={50000}
              onChange={(event) => setForm({ ...form, content: event.target.value })}
              placeholder="Digite o conteúdo. Use Markdown e selecione variáveis ao lado."
            />
            <span className="block text-right text-[10px] font-normal text-muted-foreground">
              {form.content.length.toLocaleString("pt-BR")} / 50.000 caracteres
            </span>
          </label>

          <aside className="max-h-80 overflow-y-auto rounded-xl border border-border bg-secondary/30 p-3">
            <div className="mb-3 flex items-center gap-2 text-xs font-bold text-foreground">
              <Braces className="h-4 w-4 text-primary" /> Variáveis disponíveis
            </div>
            <div className="space-y-4">
              {Object.entries(grouped).map(([group, items]) => (
                <div key={group}>
                  <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                    {group}
                  </p>
                  <div className="space-y-1">
                    {items.map((placeholder) => (
                      <button
                        key={placeholder.key}
                        type="button"
                        onClick={() => insertPlaceholder(placeholder.token)}
                        title={placeholder.description}
                        className="flex w-full items-center gap-2 rounded-md border border-transparent px-2 py-1.5 text-left text-[10px] text-muted-foreground transition hover:border-primary/20 hover:bg-primary/10 hover:text-foreground"
                      >
                        <Plus className="h-3 w-3 shrink-0 text-primary" />
                        <span className="truncate">{placeholder.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </aside>
        </div>

        <details className="rounded-xl border border-border bg-secondary/20 p-4">
          <summary className="cursor-pointer text-xs font-bold text-foreground">
            Cabeçalho, rodapé e identificação
          </summary>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="space-y-1.5 text-xs font-semibold text-foreground">
              Cabeçalho opcional
              <textarea
                className={`${textareaClass} min-h-24`}
                value={form.header_content}
                onChange={(event) => setForm({ ...form, header_content: event.target.value })}
              />
            </label>
            <label className="space-y-1.5 text-xs font-semibold text-foreground">
              Rodapé opcional
              <textarea
                className={`${textareaClass} min-h-24`}
                value={form.footer_content}
                onChange={(event) => setForm({ ...form, footer_content: event.target.value })}
              />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap gap-4 text-xs text-foreground">
            {[
              ["include_professional_identification", "Exibir identificação profissional"],
              ["include_clinic_identification", "Exibir identificação da clínica"],
              ["requires_signature", "Preparar bloco de assinatura"],
            ].map(([key, label]) => (
              <label key={key} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={Boolean(form[key as keyof DocumentTemplatePayload])}
                  onChange={(event) =>
                    setForm({ ...form, [key]: event.target.checked })
                  }
                />
                {label}
              </label>
            ))}
          </div>
        </details>

        {error && (
          <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            type="button"
            size="sm"
            isLoading={submitting}
            leftIcon={<FileText className="h-4 w-4" />}
            onClick={submit}
          >
            {initial ? "Salvar alterações" : "Criar template"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

interface EvolutionTemplateModalProps {
  open: boolean;
  onClose: () => void;
  initial?: EvolutionTemplate | null;
  submitting?: boolean;
  onSubmit: (payload: EvolutionTemplatePayload) => Promise<void>;
}

export function EvolutionTemplateModal({
  open,
  onClose,
  initial,
  submitting,
  onSubmit,
}: EvolutionTemplateModalProps) {
  const [form, setForm] = useState<EvolutionTemplatePayload>({
    name: "",
    description: "",
    category: "",
    specialty: "",
    content: "",
    is_active: true,
  });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    setForm({
      name: initial?.name ?? "",
      description: initial?.description ?? "",
      category: initial?.category ?? "",
      specialty: initial?.specialty ?? "",
      content: initial?.content ?? "",
      is_active: initial?.is_active ?? true,
      sort_order: initial?.sort_order ?? 0,
    });
  }, [initial, open]);

  const submit = async () => {
    if (!form.name.trim() || !form.content.trim()) {
      setError("Preencha o nome e o conteúdo do template.");
      return;
    }
    setError("");
    await onSubmit(form);
  };

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title={initial ? "Editar template de evolução" : "Novo template de evolução"}
      description="Crie um texto-base que poderá ser inserido sem apagar o que já foi digitado."
      className="max-w-2xl"
    >
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Nome <span className="text-danger">*</span>
            <input
              className={inputClass}
              value={form.name}
              maxLength={120}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Ex.: Sessão de terapia individual"
            />
          </label>
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Categoria
            <input
              className={inputClass}
              value={form.category}
              maxLength={100}
              onChange={(event) => setForm({ ...form, category: event.target.value })}
              placeholder="Ex.: Terapia, avaliação"
            />
          </label>
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Especialidade
            <input
              className={inputClass}
              value={form.specialty}
              maxLength={120}
              onChange={(event) => setForm({ ...form, specialty: event.target.value })}
            />
          </label>
          <label className="space-y-1.5 text-xs font-semibold text-foreground">
            Descrição
            <input
              className={inputClass}
              value={form.description}
              maxLength={300}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
          </label>
        </div>
        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          Conteúdo <span className="text-danger">*</span>
          <textarea
            className={`${textareaClass} min-h-64 font-mono text-xs`}
            value={form.content}
            maxLength={50000}
            onChange={(event) => setForm({ ...form, content: event.target.value })}
            placeholder="Digite o texto-base da evolução em Markdown."
          />
        </label>
        <label className="flex items-center gap-2 text-xs text-foreground">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
          />
          Template ativo
        </label>
        {error && (
          <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancelar
          </Button>
          <Button size="sm" isLoading={submitting} onClick={submit}>
            {initial ? "Salvar alterações" : "Criar template"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
