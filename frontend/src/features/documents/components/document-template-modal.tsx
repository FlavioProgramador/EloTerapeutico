"use client";

import { useEffect, useMemo, useRef, useState, useId } from "react";
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

const documentTypes: Array<{
  value: DocumentTemplatePayload["document_type"];
  label: string;
}> = [
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

  const baseId = useId();
  const nameId = `${baseId}-name`;
  const categoryId = `${baseId}-category`;
  const documentTypeId = `${baseId}-document-type`;
  const specialtyId = `${baseId}-specialty`;
  const descriptionId = `${baseId}-description`;
  const contentId = `${baseId}-content`;
  const headerContentId = `${baseId}-header-content`;
  const footerContentId = `${baseId}-footer-content`;

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
      include_clinic_identification:
        initial?.include_clinic_identification ?? true,
      requires_signature: initial?.requires_signature ?? true,
      status: initial?.status ?? "active",
    });
  }, [initial, open]);

  const grouped = useMemo(() => {
    return placeholders.reduce<Record<string, PlaceholderDefinition[]>>(
      (acc, placeholder) => {
        (acc[placeholder.group] ??= []).push(placeholder);
        return acc;
      },
      {},
    );
  }, [placeholders]);

  const insertPlaceholder = (token: string) => {
    const textarea = contentRef.current;
    if (!textarea) {
      setForm((current) => ({
        ...current,
        content: `${current.content}${token}`,
      }));
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

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;
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
      onClose={() => {
        if (!submitting) onClose();
      }}
      title={initial ? "Editar template" : "Novo template"}
      description="Crie um modelo seguro com variáveis controladas para agilizar a emissão."
      className="max-w-4xl"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <label htmlFor={nameId} className="block text-xs font-semibold text-foreground">
              Nome do template <span className="text-danger">*</span>
            </label>
            <input
              id={nameId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.name}
              maxLength={160}
              onChange={(event) =>
                setForm({ ...form, name: event.target.value })
              }
              placeholder="Ex.: Declaração de acompanhamento"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={categoryId} className="block text-xs font-semibold text-foreground">
              Categoria <span className="text-danger">*</span>
            </label>
            <input
              id={categoryId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.category}
              maxLength={100}
              onChange={(event) =>
                setForm({ ...form, category: event.target.value })
              }
              placeholder="Ex.: Declaração"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={documentTypeId} className="block text-xs font-semibold text-foreground">
              Tipo do documento
            </label>
            <select
              id={documentTypeId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.document_type}
              onChange={(event) =>
                setForm({
                  ...form,
                  document_type: event.target
                    .value as DocumentTemplatePayload["document_type"],
                })
              }
            >
              {documentTypes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label htmlFor={specialtyId} className="block text-xs font-semibold text-foreground">
              Especialidade
            </label>
            <input
              id={specialtyId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.specialty}
              maxLength={120}
              onChange={(event) =>
                setForm({ ...form, specialty: event.target.value })
              }
              placeholder="Ex.: Psicologia"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label htmlFor={descriptionId} className="block text-xs font-semibold text-foreground">
            Descrição
          </label>
          <input
            id={descriptionId}
            disabled={submitting}
            className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
            value={form.description}
            maxLength={500}
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
            placeholder="Explique quando este modelo deve ser utilizado."
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_17rem]">
          <div className="space-y-1.5">
            <label htmlFor={contentId} className="block text-xs font-semibold text-foreground">
              Conteúdo do template <span className="text-danger">*</span>
            </label>
            <textarea
              id={contentId}
              ref={contentRef}
              disabled={submitting}
              className={`${textareaClass} min-h-72 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.content}
              maxLength={50000}
              onChange={(event) =>
                setForm({ ...form, content: event.target.value })
              }
              placeholder="Digite o conteúdo. Use Markdown e selecione variáveis ao lado."
            />
            <span className="block text-right text-[10px] font-normal text-muted-foreground">
              {form.content.length.toLocaleString("pt-BR")} / 50.000 caracteres
            </span>
          </div>

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
                        disabled={submitting}
                        onClick={() => insertPlaceholder(placeholder.token)}
                        title={placeholder.description}
                        className="flex w-full items-center gap-2 rounded-md border border-transparent px-2 py-1.5 text-left text-[10px] text-muted-foreground transition hover:border-primary/20 hover:bg-primary/10 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:opacity-40"
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
          <summary className="cursor-pointer text-xs font-bold text-foreground outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 rounded px-1">
            Cabeçalho, rodapé e identificação
          </summary>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor={headerContentId} className="block text-xs font-semibold text-foreground">
                Cabeçalho opcional
              </label>
              <textarea
                id={headerContentId}
                disabled={submitting}
                className={`${textareaClass} min-h-24 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
                value={form.header_content}
                onChange={(event) =>
                  setForm({ ...form, header_content: event.target.value })
                }
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor={footerContentId} className="block text-xs font-semibold text-foreground">
                Rodapé opcional
              </label>
              <textarea
                id={footerContentId}
                disabled={submitting}
                className={`${textareaClass} min-h-24 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
                value={form.footer_content}
                onChange={(event) =>
                  setForm({ ...form, footer_content: event.target.value })
                }
              />
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-4 text-xs text-foreground">
            {[
              [
                "include_professional_identification",
                "Exibir identificação profissional",
                `${baseId}-include-professional`,
              ],
              [
                "include_clinic_identification",
                "Exibir identificação da clínica",
                `${baseId}-include-clinic`,
              ],
              [
                "requires_signature",
                "Preparar bloco de assinatura",
                `${baseId}-requires-signature`,
              ],
            ].map(([key, label, id]) => (
              <div key={key} className="flex items-center gap-2">
                <input
                  id={id}
                  type="checkbox"
                  disabled={submitting}
                  checked={Boolean(form[key as keyof DocumentTemplatePayload])}
                  onChange={(event) =>
                    setForm({ ...form, [key]: event.target.checked })
                  }
                  className="rounded border-border text-primary focus:ring-primary/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                />
                <label htmlFor={id} className="cursor-pointer">
                  {label}
                </label>
              </div>
            ))}
          </div>
        </details>

        {error && (
          <p
            role="alert"
            className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger"
          >
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={submitting}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            size="sm"
            isLoading={submitting}
            leftIcon={<FileText className="h-4 w-4" />}
          >
            {initial ? "Salvar alterações" : "Criar template"}
          </Button>
        </div>
      </form>
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

  const baseId = useId();
  const nameId = `${baseId}-name`;
  const categoryId = `${baseId}-category`;
  const specialtyId = `${baseId}-specialty`;
  const descriptionId = `${baseId}-description`;
  const contentId = `${baseId}-content`;
  const isActiveId = `${baseId}-is-active`;

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

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;
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
      onClose={() => {
        if (!submitting) onClose();
      }}
      title={
        initial ? "Editar template de evolução" : "Novo template de evolução"
      }
      description="Crie um texto-base que poderá ser inserido sem apagar o que já foi digitado."
      className="max-w-2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <label htmlFor={nameId} className="block text-xs font-semibold text-foreground">
              Nome <span className="text-danger">*</span>
            </label>
            <input
              id={nameId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.name}
              maxLength={120}
              onChange={(event) =>
                setForm({ ...form, name: event.target.value })
              }
              placeholder="Ex.: Sessão de terapia individual"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={categoryId} className="block text-xs font-semibold text-foreground">
              Categoria
            </label>
            <input
              id={categoryId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.category}
              maxLength={100}
              onChange={(event) =>
                setForm({ ...form, category: event.target.value })
              }
              placeholder="Ex.: Terapia, avaliação"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={specialtyId} className="block text-xs font-semibold text-foreground">
              Especialidade
            </label>
            <input
              id={specialtyId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.specialty}
              maxLength={120}
              onChange={(event) =>
                setForm({ ...form, specialty: event.target.value })
              }
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={descriptionId} className="block text-xs font-semibold text-foreground">
              Descrição
            </label>
            <input
              id={descriptionId}
              disabled={submitting}
              className={`${inputClass} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
              value={form.description}
              maxLength={300}
              onChange={(event) =>
                setForm({ ...form, description: event.target.value })
              }
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <label htmlFor={contentId} className="block text-xs font-semibold text-foreground">
            Conteúdo <span className="text-danger">*</span>
          </label>
          <textarea
            id={contentId}
            disabled={submitting}
            className={`${textareaClass} min-h-64 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2`}
            value={form.content}
            maxLength={50000}
            onChange={(event) =>
              setForm({ ...form, content: event.target.value })
            }
            placeholder="Digite o texto-base da evolução em Markdown."
          />
        </div>
        <div className="flex items-center gap-2 text-xs text-foreground">
          <input
            id={isActiveId}
            disabled={submitting}
            type="checkbox"
            checked={form.is_active}
            onChange={(event) =>
              setForm({ ...form, is_active: event.target.checked })
            }
            className="rounded border-border text-primary focus:ring-primary/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
          />
          <label htmlFor={isActiveId} className="cursor-pointer">
            Template ativo
          </label>
        </div>
        {error && (
          <p
            role="alert"
            className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger"
          >
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={submitting}
          >
            Cancelar
          </Button>
          <Button type="submit" size="sm" isLoading={submitting}>
            {initial ? "Salvar alterações" : "Criar template"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
