"use client";

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Archive,
  BookOpen,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Copy,
  Download,
  Edit3,
  Eye,
  FilePlus2,
  FileText,
  Library,
  Plus,
  RefreshCw,
  Search,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { usePatients } from "@/features/patients/hooks/use-patients";
import { extractApiError, formatDate } from "@/lib/utils";
import { documentsService } from "../services/documents.service";
import {
  useCreateDocumentTemplate,
  useCreateEvolutionTemplate,
  useCreateGeneratedDocument,
  useDocumentLibrary,
  useDocumentTemplates,
  useEvolutionTemplateAction,
  useEvolutionTemplates,
  useGeneratedDocumentAction,
  useGeneratedDocuments,
  useImportLibraryTemplate,
  usePlaceholders,
  useTemplateAction,
  useUpdateDocumentTemplate,
  useUpdateEvolutionTemplate,
} from "../hooks/use-documents";
import type {
  DocumentTemplate,
  DocumentTemplatePayload,
  EvolutionTemplate,
  EvolutionTemplatePayload,
  GeneratedDocument,
} from "../types";
import {
  DocumentTemplateModal,
  EvolutionTemplateModal,
} from "./document-template-modal";
import { GenerateDocumentModal } from "./generate-document-modal";

type Tab = "templates" | "generated" | "evolution";

const fieldClass =
  "h-10 rounded-lg border border-border bg-background px-3 text-xs text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20";

const tabs: Array<{ value: Tab; label: string; icon: typeof FileText }> = [
  { value: "templates", label: "Templates", icon: Library },
  { value: "generated", label: "Documentos gerados", icon: FileText },
  { value: "evolution", label: "Templates de evolução", icon: ClipboardList },
];

function StatusBadge({ status, label }: { status: string; label: string }) {
  const styles: Record<string, string> = {
    active: "border-emerald-400/20 bg-emerald-500/10 text-emerald-300",
    completed: "border-emerald-400/20 bg-emerald-500/10 text-emerald-300",
    draft: "border-amber-400/20 bg-amber-500/10 text-amber-300",
    processing: "border-sky-400/20 bg-sky-500/10 text-sky-300",
    failed: "border-danger/20 bg-danger/10 text-danger",
    cancelled: "border-border bg-secondary text-muted-foreground",
    inactive: "border-border bg-secondary text-muted-foreground",
    archived: "border-border bg-secondary text-muted-foreground",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold ${styles[status] ?? styles.inactive}`}
    >
      {label}
    </span>
  );
}

function LoadingState() {
  return (
    <div role="status" className="space-y-3 rounded-xl border border-border bg-card p-4">
      {[1, 2, 3].map((item) => (
        <div key={item} className="h-14 animate-pulse rounded-lg bg-secondary" />
      ))}
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-danger/20 bg-danger/5 px-6 py-12 text-center">
      <XCircle className="mx-auto h-8 w-8 text-danger" />
      <h3 className="mt-3 text-sm font-bold text-foreground">Não foi possível carregar os dados</h3>
      <p className="mt-1 text-xs text-muted-foreground">Verifique a conexão e tente novamente.</p>
      <Button size="sm" variant="outline" className="mt-4" onClick={onRetry}>
        Tentar novamente
      </Button>
    </div>
  );
}

function EmptyState({
  title,
  description,
  primaryLabel,
  secondaryLabel,
  onPrimary,
  onSecondary,
}: {
  title: string;
  description: string;
  primaryLabel: string;
  secondaryLabel?: string;
  onPrimary: () => void;
  onSecondary?: () => void;
}) {
  return (
    <div className="rounded-xl border border-border bg-card px-6 py-14 text-center">
      <FileText className="mx-auto h-9 w-9 text-muted-foreground" />
      <h3 className="mt-4 text-sm font-bold text-foreground">{title}</h3>
      <p className="mx-auto mt-2 max-w-lg text-xs leading-5 text-muted-foreground">
        {description}
      </p>
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        {secondaryLabel && onSecondary && (
          <Button variant="outline" size="sm" onClick={onSecondary}>
            {secondaryLabel}
          </Button>
        )}
        <Button size="sm" leftIcon={<Plus className="h-4 w-4" />} onClick={onPrimary}>
          {primaryLabel}
        </Button>
      </div>
    </div>
  );
}

export function DocumentsWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tab = (searchParams.get("tab") as Tab) || "templates";
  const libraryOpen = searchParams.get("library") === "true";
  const initialPatientId = Number(searchParams.get("patient") || 0) || undefined;

  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [specialtyFilter, setSpecialtyFilter] = useState("");
  const [page, setPage] = useState(1);
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  const [evolutionModalOpen, setEvolutionModalOpen] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(Boolean(initialPatientId));
  const [editingTemplate, setEditingTemplate] = useState<DocumentTemplate | null>(null);
  const [editingEvolution, setEditingEvolution] = useState<EvolutionTemplate | null>(null);
  const [preview, setPreview] = useState<{
    title: string;
    header_html: string;
    content_html: string;
    footer_html: string;
  } | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<GeneratedDocument | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const commonFilters = useMemo(
    () => ({
      search: search || undefined,
      status: statusFilter || undefined,
      document_type: typeFilter || undefined,
      specialty: specialtyFilter || undefined,
      page,
      page_size: 20,
    }),
    [page, search, specialtyFilter, statusFilter, typeFilter],
  );

  const templatesQuery = useDocumentTemplates(commonFilters);
  const libraryQuery = useDocumentLibrary(commonFilters);
  const generatedQuery = useGeneratedDocuments({
    search: search || undefined,
    status: statusFilter || undefined,
    document_type: typeFilter || undefined,
    patient: initialPatientId,
    page,
    page_size: 20,
  });
  const evolutionQuery = useEvolutionTemplates({
    search: search || undefined,
    status: statusFilter || undefined,
    specialty: specialtyFilter || undefined,
  });
  const placeholdersQuery = usePlaceholders();
  const patientsQuery = usePatients({ status: "active", page_size: 100 });
  const activeTemplatesQuery = useDocumentTemplates({ status: "active", page_size: 100 });

  const createTemplate = useCreateDocumentTemplate();
  const updateTemplate = useUpdateDocumentTemplate();
  const templateAction = useTemplateAction();
  const importLibrary = useImportLibraryTemplate();
  const createGenerated = useCreateGeneratedDocument();
  const generatedAction = useGeneratedDocumentAction();
  const createEvolution = useCreateEvolutionTemplate();
  const updateEvolution = useUpdateEvolutionTemplate();
  const evolutionAction = useEvolutionTemplateAction();

  const navigate = (nextTab: Tab, options?: { library?: boolean }) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", nextTab);
    if (options?.library) params.set("library", "true");
    else params.delete("library");
    params.delete("patient");
    router.replace(`/dashboard/documentos?${params.toString()}`);
    setPage(1);
  };

  const updateSearch = (value: string) => {
    setSearch(value);
    setPage(1);
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set("search", value);
    else params.delete("search");
    router.replace(`/dashboard/documentos?${params.toString()}`);
  };

  const openTemplateEditor = async (template?: DocumentTemplate) => {
    if (!template) {
      setEditingTemplate(null);
      setTemplateModalOpen(true);
      return;
    }
    try {
      const complete = template.content
        ? template
        : await documentsService.getTemplate(template.public_id);
      setEditingTemplate(complete);
      setTemplateModalOpen(true);
    } catch (error) {
      toast.error(extractApiError(error));
    }
  };

  const saveTemplate = async (payload: DocumentTemplatePayload) => {
    if (editingTemplate) {
      await updateTemplate.mutateAsync({ publicId: editingTemplate.public_id, payload });
    } else {
      await createTemplate.mutateAsync(payload);
    }
    setTemplateModalOpen(false);
    setEditingTemplate(null);
  };

  const saveEvolution = async (payload: EvolutionTemplatePayload) => {
    if (editingEvolution) {
      await updateEvolution.mutateAsync({ id: editingEvolution.id, payload });
    } else {
      await createEvolution.mutateAsync(payload);
    }
    setEvolutionModalOpen(false);
    setEditingEvolution(null);
  };

  const showTemplatePreview = async (template: DocumentTemplate, library = false) => {
    setPreviewLoading(true);
    try {
      const result = await documentsService.previewTemplate(
        template.public_id,
        initialPatientId ? { patient_id: initialPatientId } : undefined,
        library,
      );
      setPreview(result);
    } catch (error) {
      toast.error(extractApiError(error));
    } finally {
      setPreviewLoading(false);
    }
  };

  const showDocumentDetail = async (document: GeneratedDocument) => {
    try {
      const detail = await documentsService.getGenerated(document.public_id);
      setSelectedDocument(detail);
    } catch (error) {
      toast.error(extractApiError(error));
    }
  };

  const createDocument = async (
    payload: {
      template_public_id: string;
      patient_id: number;
      title?: string;
      local_emissao?: string;
    },
    generateNow: boolean,
  ) => {
    const created = await createGenerated.mutateAsync(payload);
    if (generateNow) {
      await generatedAction.mutateAsync({ publicId: created.public_id, action: "generate" });
    }
    setGenerateModalOpen(false);
    navigate("generated");
    return created as GeneratedDocument;
  };

  const totalPages = (count: number) => Math.max(1, Math.ceil(count / 20));

  return (
    <div className="space-y-6">
      <header>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground">Documentos</h1>
          <BookOpen className="h-5 w-5 text-primary" />
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Gerencie templates e gere documentos protegidos para pacientes.
        </p>
      </header>

      <nav className="flex overflow-x-auto border-b border-border" aria-label="Seções de documentos">
        {tabs.map((item) => {
          const Icon = item.icon;
          const active = tab === item.value && !libraryOpen;
          return (
            <button
              key={item.value}
              type="button"
              onClick={() => navigate(item.value)}
              aria-current={active ? "page" : undefined}
              className={`relative flex shrink-0 items-center gap-2 px-4 py-3 text-xs font-semibold transition ${
                active ? "text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
              {active && <span className="absolute inset-x-0 bottom-0 h-0.5 bg-primary" />}
            </button>
          );
        })}
      </nav>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative min-w-0 flex-1 lg:max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(event) => updateSearch(event.target.value)}
            placeholder="Buscar por nome, paciente ou número..."
            className={`${fieldClass} w-full pl-9`}
            aria-label="Buscar documentos"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            className={fieldClass}
            value={typeFilter}
            onChange={(event) => {
              setTypeFilter(event.target.value);
              setPage(1);
            }}
            aria-label="Filtrar por tipo"
          >
            <option value="">Todos os tipos</option>
            <option value="declaration">Declaração</option>
            <option value="report">Relatório</option>
            <option value="referral">Encaminhamento</option>
            <option value="certificate">Atestado</option>
            <option value="consent">Consentimento</option>
          </select>
          <select
            className={fieldClass}
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              setPage(1);
            }}
            aria-label="Filtrar por status"
          >
            <option value="">Todos os status</option>
            <option value="active">Ativo</option>
            <option value="inactive">Inativo</option>
            <option value="draft">Rascunho</option>
            <option value="processing">Processando</option>
            <option value="completed">Concluído</option>
            <option value="failed">Falhou</option>
            <option value="archived">Arquivado</option>
          </select>
          {(tab === "templates" || tab === "evolution" || libraryOpen) && (
            <input
              className={`${fieldClass} w-40`}
              value={specialtyFilter}
              onChange={(event) => {
                setSpecialtyFilter(event.target.value);
                setPage(1);
              }}
              placeholder="Especialidade"
              aria-label="Filtrar por especialidade"
            />
          )}
        </div>
      </div>

      {libraryOpen ? (
        <section className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <button
                type="button"
                onClick={() => navigate("templates")}
                className="mb-2 inline-flex items-center gap-1 text-xs font-semibold text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="h-4 w-4" /> Voltar aos templates
              </button>
              <h2 className="text-base font-bold text-foreground">Biblioteca de templates</h2>
              <p className="text-xs text-muted-foreground">
                Modelos prontos para importar e personalizar sem alterar o original global.
              </p>
            </div>
          </div>
          {libraryQuery.isLoading ? (
            <LoadingState />
          ) : libraryQuery.isError ? (
            <ErrorState onRetry={() => libraryQuery.refetch()} />
          ) : libraryQuery.data?.results.length === 0 ? (
            <EmptyState
              title="Nenhum modelo encontrado"
              description="Ajuste os filtros para visualizar outros modelos da biblioteca."
              primaryLabel="Limpar filtros"
              onPrimary={() => {
                setSearch("");
                setStatusFilter("");
                setTypeFilter("");
                setSpecialtyFilter("");
              }}
            />
          ) : (
            <div className="grid gap-3 lg:grid-cols-2">
              {libraryQuery.data?.results.map((template) => (
                <article
                  key={template.public_id}
                  className="rounded-xl border border-border bg-card p-4 transition hover:border-primary/25"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate text-sm font-bold text-foreground">{template.name}</h3>
                      <p className="mt-1 line-clamp-2 text-[11px] leading-5 text-muted-foreground">
                        {template.description || template.content_preview}
                      </p>
                    </div>
                    <span className="shrink-0 rounded-full border border-border px-2 py-0.5 text-[9px] text-muted-foreground">
                      {template.document_type_display}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2 text-[9px] text-muted-foreground">
                    {template.specialty && <span className="rounded bg-secondary px-2 py-1">{template.specialty}</span>}
                    <span className="rounded bg-secondary px-2 py-1">{template.category}</span>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      isLoading={previewLoading}
                      leftIcon={<Eye className="h-4 w-4" />}
                      onClick={() => showTemplatePreview(template, true)}
                    >
                      Visualizar
                    </Button>
                    <Button
                      size="sm"
                      isLoading={importLibrary.isPending}
                      leftIcon={<Download className="h-4 w-4" />}
                      onClick={() => importLibrary.mutate(template.public_id)}
                    >
                      Importar
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : tab === "templates" ? (
        <section className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">Templates de documentos</h2>
              <p className="text-xs text-muted-foreground">
                Crie modelos de declarações, relatórios e encaminhamentos para geração automática.
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Library className="h-4 w-4" />}
                onClick={() => navigate("templates", { library: true })}
              >
                Biblioteca
              </Button>
              <Button
                size="sm"
                leftIcon={<Plus className="h-4 w-4" />}
                onClick={() => openTemplateEditor()}
              >
                Novo template
              </Button>
            </div>
          </div>
          {templatesQuery.isLoading ? (
            <LoadingState />
          ) : templatesQuery.isError ? (
            <ErrorState onRetry={() => templatesQuery.refetch()} />
          ) : templatesQuery.data?.results.length === 0 ? (
            <EmptyState
              title="Nenhum template cadastrado"
              description="Crie um template personalizado ou importe um modelo pronto da biblioteca."
              secondaryLabel="Ver biblioteca"
              primaryLabel="Criar template"
              onSecondary={() => navigate("templates", { library: true })}
              onPrimary={() => openTemplateEditor()}
            />
          ) : (
            <div className="overflow-hidden rounded-xl border border-border bg-card">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[58rem] text-left text-xs">
                  <thead className="border-b border-border bg-secondary/30 text-[10px] uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3">Nome</th>
                      <th className="px-4 py-3">Categoria</th>
                      <th className="px-4 py-3">Especialidade</th>
                      <th className="px-4 py-3">Atualização</th>
                      <th className="px-4 py-3">Uso</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {templatesQuery.data?.results.map((template) => (
                      <tr key={template.public_id} className="hover:bg-secondary/20">
                        <td className="px-4 py-3">
                          <strong className="block text-foreground">{template.name}</strong>
                          <span className="mt-1 block max-w-sm truncate text-[10px] text-muted-foreground">
                            {template.content_preview || template.description}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{template.category}</td>
                        <td className="px-4 py-3 text-muted-foreground">{template.specialty || "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground">{formatDate(template.updated_at)}</td>
                        <td className="px-4 py-3 text-muted-foreground">{template.usage_count}</td>
                        <td className="px-4 py-3">
                          <StatusBadge status={template.status} label={template.status_display} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => showTemplatePreview(template)}
                              className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
                              aria-label={`Visualizar ${template.name}`}
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => openTemplateEditor(template)}
                              className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
                              aria-label={`Editar ${template.name}`}
                            >
                              <Edit3 className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() =>
                                templateAction.mutate({
                                  publicId: template.public_id,
                                  action: "duplicate",
                                })
                              }
                              className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
                              aria-label={`Duplicar ${template.name}`}
                            >
                              <Copy className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() =>
                                templateAction.mutate({
                                  publicId: template.public_id,
                                  action: template.status === "active" ? "deactivate" : "activate",
                                })
                              }
                              className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
                              aria-label={template.status === "active" ? "Inativar template" : "Ativar template"}
                            >
                              {template.status === "active" ? (
                                <XCircle className="h-4 w-4" />
                              ) : (
                                <CheckCircle2 className="h-4 w-4" />
                              )}
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                if (confirm(`Arquivar o template “${template.name}”?`)) {
                                  templateAction.mutate({
                                    publicId: template.public_id,
                                    action: "archive",
                                  });
                                }
                              }}
                              className="rounded-md p-2 text-muted-foreground hover:bg-danger/10 hover:text-danger"
                              aria-label={`Arquivar ${template.name}`}
                            >
                              <Archive className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {(templatesQuery.data?.count ?? 0) > 20 && (
            <Pagination
              page={page}
              totalPages={totalPages(templatesQuery.data?.count ?? 0)}
              onChange={setPage}
            />
          )}
        </section>
      ) : tab === "generated" ? (
        <section className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">Todos os documentos</h2>
              <p className="text-xs text-muted-foreground">
                Acompanhe rascunhos, PDFs concluídos, falhas e documentos arquivados.
              </p>
            </div>
            <Button
              size="sm"
              leftIcon={<FilePlus2 className="h-4 w-4" />}
              onClick={() => setGenerateModalOpen(true)}
            >
              Gerar documento
            </Button>
          </div>
          {generatedQuery.isLoading ? (
            <LoadingState />
          ) : generatedQuery.isError ? (
            <ErrorState onRetry={() => generatedQuery.refetch()} />
          ) : generatedQuery.data?.results.length === 0 ? (
            <EmptyState
              title="Nenhum documento gerado"
              description="Documentos emitidos pelos profissionais aparecerão aqui com histórico e status."
              primaryLabel="Gerar primeiro documento"
              onPrimary={() => setGenerateModalOpen(true)}
            />
          ) : (
            <div className="overflow-hidden rounded-xl border border-border bg-card">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[62rem] text-left text-xs">
                  <thead className="border-b border-border bg-secondary/30 text-[10px] uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3">Documento</th>
                      <th className="px-4 py-3">Paciente</th>
                      <th className="px-4 py-3">Profissional</th>
                      <th className="px-4 py-3">Tipo</th>
                      <th className="px-4 py-3">Emissão</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {generatedQuery.data?.results.map((document) => (
                      <tr key={document.public_id} className="hover:bg-secondary/20">
                        <td className="px-4 py-3">
                          <strong className="block text-foreground">{document.title}</strong>
                          <span className="mt-1 block font-mono text-[10px] text-muted-foreground">
                            {document.document_number}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{document.patient_name}</td>
                        <td className="px-4 py-3 text-muted-foreground">{document.professional_name}</td>
                        <td className="px-4 py-3 text-muted-foreground">{document.document_type_display}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {formatDate(document.generated_at || document.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={document.status} label={document.status_display} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => showDocumentDetail(document)}
                              className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
                              aria-label={`Visualizar ${document.title}`}
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            {(document.status === "draft" || document.status === "failed") && (
                              <button
                                type="button"
                                onClick={() =>
                                  generatedAction.mutate({
                                    publicId: document.public_id,
                                    action: "generate",
                                  })
                                }
                                className="rounded-md p-2 text-primary hover:bg-primary/10"
                                aria-label={`Gerar PDF de ${document.title}`}
                              >
                                <RefreshCw className="h-4 w-4" />
                              </button>
                            )}
                            {document.status === "completed" && (
                              <button
                                type="button"
                                onClick={async () => {
                                  try {
                                    await documentsService.downloadGenerated(
                                      document.public_id,
                                      `${document.document_number}.pdf`,
                                    );
                                  } catch (error) {
                                    toast.error(extractApiError(error));
                                  }
                                }}
                                className="rounded-md p-2 text-emerald-300 hover:bg-emerald-500/10"
                                aria-label={`Baixar ${document.title}`}
                              >
                                <Download className="h-4 w-4" />
                              </button>
                            )}
                            {document.status !== "archived" && (
                              <button
                                type="button"
                                onClick={() => {
                                  if (confirm(`Arquivar o documento “${document.title}”?`)) {
                                    generatedAction.mutate({
                                      publicId: document.public_id,
                                      action: "archive",
                                    });
                                  }
                                }}
                                className="rounded-md p-2 text-muted-foreground hover:bg-danger/10 hover:text-danger"
                                aria-label={`Arquivar ${document.title}`}
                              >
                                <Archive className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {(generatedQuery.data?.count ?? 0) > 20 && (
            <Pagination
              page={page}
              totalPages={totalPages(generatedQuery.data?.count ?? 0)}
              onChange={setPage}
            />
          )}
        </section>
      ) : (
        <section className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">Templates de evolução</h2>
              <p className="text-xs text-muted-foreground">
                Modelos privados para agilizar o preenchimento das evoluções do prontuário.
              </p>
            </div>
            <Button
              size="sm"
              leftIcon={<Plus className="h-4 w-4" />}
              onClick={() => {
                setEditingEvolution(null);
                setEvolutionModalOpen(true);
              }}
            >
              Novo template
            </Button>
          </div>
          {evolutionQuery.isLoading ? (
            <LoadingState />
          ) : evolutionQuery.isError ? (
            <ErrorState onRetry={() => evolutionQuery.refetch()} />
          ) : evolutionQuery.data?.length === 0 ? (
            <EmptyState
              title="Nenhum template de evolução"
              description="Crie textos-base para inserir no editor clínico sem apagar conteúdo já digitado."
              primaryLabel="Criar template"
              onPrimary={() => setEvolutionModalOpen(true)}
            />
          ) : (
            <div className="overflow-hidden rounded-xl border border-border bg-card">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[52rem] text-left text-xs">
                  <thead className="border-b border-border bg-secondary/30 text-[10px] uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3">Nome</th>
                      <th className="px-4 py-3">Categoria</th>
                      <th className="px-4 py-3">Prévia</th>
                      <th className="px-4 py-3">Uso</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {evolutionQuery.data?.map((template) => {
                      const status = template.archived_at
                        ? "archived"
                        : template.is_active
                          ? "active"
                          : "inactive";
                      return (
                        <tr key={template.id} className="hover:bg-secondary/20">
                          <td className="px-4 py-3">
                            <strong className="text-foreground">{template.name}</strong>
                            {template.is_system && (
                              <span className="ml-2 rounded bg-primary/10 px-1.5 py-0.5 text-[8px] font-bold text-primary">
                                SISTEMA
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">{template.category || "—"}</td>
                          <td className="max-w-sm truncate px-4 py-3 text-muted-foreground">
                            {template.content_preview}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">{template.usage_count}</td>
                          <td className="px-4 py-3">
                            <StatusBadge
                              status={status}
                              label={status === "active" ? "Ativo" : status === "archived" ? "Arquivado" : "Inativo"}
                            />
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex justify-end gap-1">
                              <button
                                type="button"
                                onClick={() => {
                                  setEditingEvolution(template);
                                  setEvolutionModalOpen(true);
                                }}
                                disabled={template.is_system}
                                className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-40"
                                aria-label={`Editar ${template.name}`}
                              >
                                <Edit3 className="h-4 w-4" />
                              </button>
                              <button
                                type="button"
                                onClick={() =>
                                  evolutionAction.mutate({ id: template.id, action: "duplicate" })
                                }
                                className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
                                aria-label={`Duplicar ${template.name}`}
                              >
                                <Copy className="h-4 w-4" />
                              </button>
                              {!template.is_system && (
                                <button
                                  type="button"
                                  onClick={() =>
                                    evolutionAction.mutate({
                                      id: template.id,
                                      action: template.is_active ? "deactivate" : "activate",
                                    })
                                  }
                                  className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
                                  aria-label={template.is_active ? "Inativar" : "Ativar"}
                                >
                                  {template.is_active ? (
                                    <XCircle className="h-4 w-4" />
                                  ) : (
                                    <CheckCircle2 className="h-4 w-4" />
                                  )}
                                </button>
                              )}
                              {!template.is_system && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (confirm(`Arquivar o template “${template.name}”?`)) {
                                      evolutionAction.mutate({ id: template.id, action: "archive" });
                                    }
                                  }}
                                  className="rounded-md p-2 text-muted-foreground hover:bg-danger/10 hover:text-danger"
                                  aria-label={`Arquivar ${template.name}`}
                                >
                                  <Archive className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      )}

      <DocumentTemplateModal
        open={templateModalOpen}
        onClose={() => {
          setTemplateModalOpen(false);
          setEditingTemplate(null);
        }}
        initial={editingTemplate}
        placeholders={placeholdersQuery.data ?? []}
        submitting={createTemplate.isPending || updateTemplate.isPending}
        onSubmit={saveTemplate}
      />

      <EvolutionTemplateModal
        open={evolutionModalOpen}
        onClose={() => {
          setEvolutionModalOpen(false);
          setEditingEvolution(null);
        }}
        initial={editingEvolution}
        submitting={createEvolution.isPending || updateEvolution.isPending}
        onSubmit={saveEvolution}
      />

      <GenerateDocumentModal
        open={generateModalOpen}
        onClose={() => setGenerateModalOpen(false)}
        patients={patientsQuery.data?.results ?? []}
        templates={activeTemplatesQuery.data?.results ?? []}
        initialPatientId={initialPatientId}
        submitting={createGenerated.isPending || generatedAction.isPending}
        onCreate={createDocument}
      />

      <Modal
        isOpen={Boolean(preview)}
        onClose={() => setPreview(null)}
        title={preview?.title ?? "Prévia"}
        description="Prévia com dados demonstrativos ou do paciente selecionado."
        className="max-w-3xl"
      >
        <article className="min-h-96 rounded-lg bg-white px-8 py-10 text-slate-900 shadow-inner">
          {preview?.header_html && (
            <header
              className="mb-6 border-b border-slate-200 pb-4 text-sm text-slate-600"
              dangerouslySetInnerHTML={{ __html: preview.header_html }}
            />
          )}
          <div
            className="space-y-3 text-sm leading-7"
            dangerouslySetInnerHTML={{ __html: preview?.content_html ?? "" }}
          />
          {preview?.footer_html && (
            <footer
              className="mt-8 border-t border-slate-200 pt-4 text-xs text-slate-500"
              dangerouslySetInnerHTML={{ __html: preview.footer_html }}
            />
          )}
        </article>
      </Modal>

      <Modal
        isOpen={Boolean(selectedDocument)}
        onClose={() => setSelectedDocument(null)}
        title={selectedDocument?.title ?? "Documento"}
        description={selectedDocument?.document_number}
        className="max-w-3xl"
      >
        <div className="space-y-4">
          <div className="grid gap-3 rounded-xl border border-border bg-secondary/20 p-4 text-xs sm:grid-cols-3">
            <div>
              <span className="text-muted-foreground">Paciente</span>
              <strong className="mt-1 block text-foreground">{selectedDocument?.patient_name}</strong>
            </div>
            <div>
              <span className="text-muted-foreground">Profissional</span>
              <strong className="mt-1 block text-foreground">{selectedDocument?.professional_name}</strong>
            </div>
            <div>
              <span className="text-muted-foreground">Status</span>
              <div className="mt-1">
                {selectedDocument && (
                  <StatusBadge
                    status={selectedDocument.status}
                    label={selectedDocument.status_display}
                  />
                )}
              </div>
            </div>
          </div>
          {selectedDocument?.content ? (
            <article
              className="min-h-72 rounded-lg bg-white px-8 py-10 text-sm leading-7 text-slate-900"
              dangerouslySetInnerHTML={{ __html: selectedDocument.content }}
            />
          ) : (
            <p className="rounded-lg border border-border p-6 text-center text-xs text-muted-foreground">
              Abra novamente após a atualização da listagem para carregar os detalhes completos.
            </p>
          )}
          {selectedDocument?.failure_reason && (
            <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger">
              {selectedDocument.failure_reason}
            </p>
          )}
        </div>
      </Modal>
    </div>
  );
}

function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}) {
  return (
    <div className="flex items-center justify-end gap-2 text-xs text-muted-foreground">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-card disabled:opacity-40"
        aria-label="Página anterior"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      <span>
        Página {page} de {totalPages}
      </span>
      <button
        type="button"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
        className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-card disabled:opacity-40"
        aria-label="Próxima página"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
