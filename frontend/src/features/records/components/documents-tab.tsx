"use client";

import { DragEvent, useEffect, useMemo, useRef, useState, useId } from "react";
import {
  Archive,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  FileImage,
  FilePenLine,
  FilePlus2,
  FileText,
  FileType2,
  Filter,
  MoreHorizontal,
  Paperclip,
  Pencil,
  Search,
  UploadCloud,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { cn } from "@/lib/utils";
import { recordWorkspaceService } from "../services/record-workspace.service";
import type { ClinicalDocument } from "../types";

interface Props {
  patientId?: number;
  documents: ClinicalDocument[];
  loading: boolean;
  uploading: boolean;
  updating: boolean;
  onUpload: (data: FormData) => Promise<void>;
  onUpdate: (id: number, payload: Partial<ClinicalDocument>) => Promise<void>;
  onArchive: (id: number) => Promise<void>;
}

const categories = [
  ["all", "Todas as categorias"],
  ["consent", "Termo de consentimento"],
  ["report", "Relatório"],
  ["referral", "Encaminhamento"],
  ["certificate", "Atestado"],
  ["assessment", "Avaliação"],
  ["scale", "Escala ou teste"],
  ["patient_file", "Documento do paciente"],
  ["other", "Outro"],
] as const;

function fileIcon(contentType: string) {
  if (contentType.startsWith("image/")) return FileImage;
  if (contentType.includes("wordprocessingml")) return FileType2;
  return FileText;
}

function formatSize(size: number) {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`;
  return `${(size / 1024).toFixed(1)} KB`;
}

export function DocumentsTab({
  documents,
  loading,
  uploading,
  updating,
  onUpload,
  onUpdate,
  onArchive,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [editingDocument, setEditingDocument] =
    useState<ClinicalDocument | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(
    documents[0]?.id ?? null,
  );

  const baseId = useId();
  const uploadCategoryId = `${baseId}-upload-category`;
  const uploadDescriptionId = `${baseId}-upload-description`;
  const editCategoryId = `${baseId}-edit-category`;
  const editDescriptionId = `${baseId}-edit-description`;
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [dragging, setDragging] = useState(false);
  const [category, setCategory] = useState("other");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [editCategory, setEditCategory] = useState("other");
  const [editDescription, setEditDescription] = useState("");
  const pageSize = 6;

  useEffect(() => {
    if (!selectedId && documents[0]) setSelectedId(documents[0].id);
    if (
      selectedId &&
      !documents.some((document) => document.id === selectedId)
    ) {
      setSelectedId(documents[0]?.id ?? null);
    }
  }, [documents, selectedId]);

  const filteredDocuments = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");
    return documents.filter((document) => {
      const matchesSearch =
        !term ||
        document.original_name.toLocaleLowerCase("pt-BR").includes(term) ||
        document.description.toLocaleLowerCase("pt-BR").includes(term);
      const matchesCategory =
        categoryFilter === "all" || document.category === categoryFilter;
      return matchesSearch && matchesCategory;
    });
  }, [categoryFilter, documents, search]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredDocuments.length / pageSize),
  );
  const pageDocuments = filteredDocuments.slice(
    (page - 1) * pageSize,
    page * pageSize,
  );
  const selectedDocument =
    documents.find((document) => document.id === selectedId) ?? null;

  useEffect(() => {
    setPage(1);
  }, [categoryFilter, search]);

  const validateFiles = (selected: File[]) => {
    const allowedExtensions = ["pdf", "jpg", "jpeg", "png", "txt", "docx"];
    const valid = selected.filter((file) => {
      const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
      if (!allowedExtensions.includes(extension)) {
        window.alert(`${file.name}: tipo de arquivo não permitido.`);
        return false;
      }
      if (file.size > 10 * 1024 * 1024) {
        window.alert(`${file.name}: o arquivo deve possuir no máximo 10 MB.`);
        return false;
      }
      return true;
    });
    setFiles(valid);
  };

  const upload = async () => {
    if (files.length === 0) return;
    for (const file of files) {
      const data = new FormData();
      data.append("file", file);
      data.append("category", category);
      data.append("description", description);
      await onUpload(data);
    }
    setFiles([]);
    setDescription("");
    setUploadOpen(false);
    if (inputRef.current) inputRef.current.value = "";
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    validateFiles(Array.from(event.dataTransfer.files));
  };

  const openMetadataEditor = (document: ClinicalDocument) => {
    setEditingDocument(document);
    setEditCategory(document.category);
    setEditDescription(document.description);
  };

  const saveMetadata = async () => {
    if (!editingDocument) return;
    await onUpdate(editingDocument.id, {
      category: editCategory,
      description: editDescription,
    });
    setEditingDocument(null);
  };

  if (loading) {
    return (
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_17rem]">
        <div className="h-[34rem] animate-pulse rounded-xl bg-secondary" />
        <div className="h-[34rem] animate-pulse rounded-xl bg-secondary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-sm font-bold text-foreground">
            Documentos clínicos
          </h3>
          <p className="mt-1 text-[10px] text-muted-foreground">
            {documents.length} documento(s) protegido(s) no prontuário.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={() => setUploadOpen(true)}
            leftIcon={<Paperclip className="h-4 w-4" />}
            className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
          >
            Anexar documento
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled
            title="A geração por modelos ainda não está configurada."
            leftIcon={<FilePlus2 className="h-4 w-4" />}
          >
            Gerar documento
          </Button>
        </div>
      </div>

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_17rem]">
        <section className="overflow-hidden rounded-xl border border-border bg-card">
          <div className="flex flex-col gap-2 border-b border-border p-3 sm:flex-row">
            <label className="relative min-w-0 flex-1">
              <span className="sr-only">Buscar documentos</span>
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Buscar documentos..."
                className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-3 text-xs text-foreground outline-none focus:border-emerald-400/50"
              />
            </label>
            <select
              value={categoryFilter}
              onChange={(event) => setCategoryFilter(event.target.value)}
              className="h-9 rounded-md border border-border bg-background px-3 text-xs text-foreground sm:w-52"
              aria-label="Filtrar por categoria"
            >
              {categories.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="grid h-9 w-9 place-items-center rounded-md border border-border bg-background text-muted-foreground hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
              title="Filtros aplicados por nome e categoria"
              aria-label="Filtros adicionais"
            >
              <Filter className="h-3.5 w-3.5" />
            </button>
          </div>

          {documents.length === 0 ? (
            <div className="px-6 py-16 text-center">
              <FileText className="mx-auto h-7 w-7 text-emerald-300" />
              <h4 className="mt-4 text-sm font-bold text-foreground">
                Nenhum documento anexado
              </h4>
              <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-muted-foreground">
                Anexe termos, relatórios, avaliações e outros arquivos clínicos.
              </p>
              <Button
                size="sm"
                className="mt-4"
                onClick={() => setUploadOpen(true)}
              >
                Anexar primeiro documento
              </Button>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="px-6 py-16 text-center">
              <Search className="mx-auto h-6 w-6 text-muted-foreground" />
              <p className="mt-3 text-xs font-semibold text-foreground">
                Nenhum documento encontrado
              </p>
              <button
                type="button"
                onClick={() => {
                  setSearch("");
                  setCategoryFilter("all");
                }}
                className="mt-2 text-[10px] font-semibold text-emerald-300 hover:underline"
              >
                Limpar filtros
              </button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[44rem] text-left text-[10px]">
                  <thead className="bg-background/40 text-muted-foreground">
                    <tr>
                      <th className="px-4 py-2.5 font-semibold">
                        Nome do documento
                      </th>
                      <th className="px-4 py-2.5 font-semibold">Categoria</th>
                      <th className="px-4 py-2.5 font-semibold">Status</th>
                      <th className="px-4 py-2.5 font-semibold">Data</th>
                      <th className="px-4 py-2.5 text-right font-semibold">
                        Ações
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {pageDocuments.map((document) => {
                      const Icon = fileIcon(document.content_type);
                      const selected = document.id === selectedId;
                      return (
                        <tr
                          key={document.id}
                          onClick={() => setSelectedId(document.id)}
                          className={cn(
                            "cursor-pointer transition hover:bg-emerald-500/5",
                            selected && "bg-emerald-500/10",
                          )}
                        >
                          <td className="px-4 py-3">
                            <div className="flex min-w-0 items-center gap-3">
                              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-rose-500/10 text-rose-300">
                                <Icon className="h-4 w-4" />
                              </span>
                              <div className="min-w-0">
                                <strong className="block max-w-xs truncate text-[10px] text-foreground">
                                  {document.original_name}
                                </strong>
                                <small className="mt-1 block text-[9px] text-muted-foreground">
                                  {formatSize(document.size_bytes)} · versão{" "}
                                  {document.version}
                                </small>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {document.category_display}
                          </td>
                          <td className="px-4 py-3">
                            <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2 py-0.5 text-[8px] font-bold text-emerald-300">
                              {document.status_display ?? "Disponível"}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {new Date(document.created_at).toLocaleDateString(
                              "pt-BR",
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex justify-end gap-1">
                              <button
                                type="button"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  recordWorkspaceService.downloadDocument(
                                    document,
                                  );
                                }}
                                className="rounded-md p-1.5 text-sky-300 hover:bg-sky-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                                aria-label={`Baixar documento ${document.original_name}`}
                              >
                                <Download className="h-3.5 w-3.5" />
                              </button>
                              <button
                                type="button"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  openMetadataEditor(document);
                                }}
                                className="rounded-md p-1.5 text-emerald-300 hover:bg-emerald-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                                aria-label={`Editar dados do documento ${document.original_name}`}
                              >
                                <Pencil className="h-3.5 w-3.5" />
                              </button>
                              <button
                                type="button"
                                className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                                aria-label={`Mais ações para ${document.original_name}`}
                              >
                                <MoreHorizontal className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3 text-[9px] text-muted-foreground">
                <span>
                  Mostrando {(page - 1) * pageSize + 1} a{" "}
                  {Math.min(page * pageSize, filteredDocuments.length)} de{" "}
                  {filteredDocuments.length} documento(s)
                </span>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    disabled={page === 1}
                    onClick={() =>
                      setPage((current) => Math.max(1, current - 1))
                    }
                    className="grid h-7 w-7 place-items-center rounded-md border border-border disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                    aria-label="Página anterior"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                  </button>
                  <span className="grid h-7 min-w-7 place-items-center rounded-md border border-emerald-400/30 bg-emerald-500/10 px-2 font-bold text-emerald-300">
                    {page}
                  </span>
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() =>
                      setPage((current) => Math.min(totalPages, current + 1))
                    }
                    className="grid h-7 w-7 place-items-center rounded-md border border-border disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                    aria-label="Próxima página"
                  >
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </footer>
            </>
          )}
        </section>

        <aside className="rounded-xl border border-border bg-card xl:sticky xl:top-4">
          {selectedDocument ? (
            <>
              <header className="border-b border-border p-4">
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-rose-500/10 text-rose-300">
                    <FileText className="h-5 w-5" />
                  </span>
                  <div className="min-w-0">
                    <h3 className="break-words text-xs font-bold text-foreground">
                      {selectedDocument.original_name}
                    </h3>
                    <p className="mt-1 text-[9px] text-muted-foreground">
                      {formatSize(selectedDocument.size_bytes)}
                    </p>
                  </div>
                </div>
              </header>

              <dl className="space-y-3 p-4 text-[10px]">
                <div>
                  <dt className="text-muted-foreground">Categoria</dt>
                  <dd className="mt-1 font-semibold text-foreground">
                    {selectedDocument.category_display}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Status</dt>
                  <dd className="mt-1 text-emerald-300">
                    {selectedDocument.status_display ?? "Disponível"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Data do documento</dt>
                  <dd className="mt-1 font-semibold text-foreground">
                    {new Date(selectedDocument.created_at).toLocaleDateString(
                      "pt-BR",
                    )}
                  </dd>
                </div>
                {selectedDocument.uploaded_by_name && (
                  <div>
                    <dt className="text-muted-foreground">Criado por</dt>
                    <dd className="mt-1 font-semibold text-foreground">
                      {selectedDocument.uploaded_by_name}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-muted-foreground">Versão</dt>
                  <dd className="mt-1 font-semibold text-foreground">
                    {selectedDocument.version}
                  </dd>
                </div>
                {selectedDocument.evolution_date && (
                  <div>
                    <dt className="text-muted-foreground">
                      Evolução vinculada
                    </dt>
                    <dd className="mt-1 font-semibold text-foreground">
                      {new Date(
                        `${selectedDocument.evolution_date}T12:00:00`,
                      ).toLocaleDateString("pt-BR")}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-muted-foreground">Descrição</dt>
                  <dd className="mt-1 leading-4 text-foreground">
                    {selectedDocument.description || "Sem descrição adicional."}
                  </dd>
                </div>
              </dl>

              <div className="grid gap-2 border-t border-border p-4">
                <Button
                  size="sm"
                  onClick={() =>
                    recordWorkspaceService.downloadDocument(selectedDocument)
                  }
                  leftIcon={<Eye className="h-3.5 w-3.5" />}
                  className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
                >
                  Visualizar ou baixar
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => openMetadataEditor(selectedDocument)}
                  leftIcon={<FilePenLine className="h-3.5 w-3.5" />}
                >
                  Editar detalhes
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() =>
                    window.confirm("Arquivar este documento?") &&
                    onArchive(selectedDocument.id)
                  }
                  leftIcon={<Archive className="h-3.5 w-3.5" />}
                  className="text-amber-300 hover:bg-amber-500/10"
                >
                  Arquivar
                </Button>
              </div>
            </>
          ) : (
            <div className="px-5 py-16 text-center">
              <FileText className="mx-auto h-6 w-6 text-muted-foreground" />
              <p className="mt-3 text-xs font-semibold">
                Selecione um documento
              </p>
              <p className="mt-1 text-[10px] text-muted-foreground">
                Os detalhes aparecerão neste painel.
              </p>
            </div>
          )}
        </aside>
      </div>

      <Modal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        title="Anexar documento"
        description="Os arquivos são validados e permanecem acessíveis somente por rotas autenticadas."
        className="max-w-xl"
      >
        <div
          onDragEnter={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cn(
            "rounded-xl border border-dashed p-7 text-center transition",
            dragging
              ? "border-emerald-400 bg-emerald-500/10"
              : "border-emerald-400/30 bg-emerald-500/5",
          )}
        >
          <UploadCloud className="mx-auto h-7 w-7 text-emerald-300" />
          <p className="mt-3 text-xs font-semibold text-foreground">
            Arraste arquivos ou clique para selecionar
          </p>
          <p className="mt-1 text-[10px] text-muted-foreground">
            PDF, JPG, PNG, TXT ou DOCX com até 10 MB por arquivo.
          </p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.txt,.docx"
            className="sr-only"
            onChange={(event) =>
              validateFiles(Array.from(event.target.files ?? []))
            }
          />
          <Button
            size="sm"
            variant="outline"
            className="mt-4"
            onClick={() => inputRef.current?.click()}
          >
            Selecionar arquivos
          </Button>
        </div>

        {files.length > 0 && (
          <div className="mt-3 space-y-2">
            {files.map((file) => (
              <div
                key={`${file.name}-${file.size}`}
                className="flex items-center gap-3 rounded-lg border border-border p-3"
              >
                <FileText className="h-4 w-4 text-emerald-300" />
                <div className="min-w-0 flex-1">
                  <strong className="block truncate text-[10px] text-foreground">
                    {file.name}
                  </strong>
                  <small className="text-[9px] text-muted-foreground">
                    {formatSize(file.size)}
                  </small>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setFiles((current) =>
                      current.filter((item) => item !== file),
                    )
                  }
                  className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                  aria-label={`Remover ${file.name}`}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <label htmlFor={uploadCategoryId} className="text-xs font-semibold text-muted-foreground block">
              Categoria
            </label>
            <select
              id={uploadCategoryId}
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
            >
              {categories.slice(1).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor={uploadDescriptionId} className="text-xs font-semibold text-muted-foreground block">
              Descrição
            </label>
            <input
              id={uploadDescriptionId}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Descrição opcional"
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
            />
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-2 border-t border-border pt-4">
          <Button variant="ghost" onClick={() => setUploadOpen(false)}>
            Cancelar
          </Button>
          <Button
            isLoading={uploading}
            disabled={files.length === 0}
            onClick={upload}
            className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
          >
            Anexar {files.length > 1 ? `${files.length} arquivos` : "arquivo"}
          </Button>
        </div>
      </Modal>

      <Modal
        isOpen={Boolean(editingDocument)}
        onClose={() => setEditingDocument(null)}
        title="Editar detalhes do documento"
        description="Atualize apenas os metadados. O arquivo original permanece preservado."
        className="max-w-lg"
      >
        <div className="space-y-4">
          <div className="space-y-1">
            <label htmlFor={editCategoryId} className="text-xs font-semibold text-muted-foreground block">
              Categoria
            </label>
            <select
              id={editCategoryId}
              value={editCategory}
              onChange={(event) => setEditCategory(event.target.value)}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
            >
              {categories.slice(1).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor={editDescriptionId} className="text-xs font-semibold text-muted-foreground block">
              Descrição
            </label>
            <textarea
              id={editDescriptionId}
              rows={4}
              value={editDescription}
              onChange={(event) => setEditDescription(event.target.value)}
              className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
            />
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2 border-t border-border pt-4">
          <Button variant="ghost" onClick={() => setEditingDocument(null)}>
            Cancelar
          </Button>
          <Button
            isLoading={updating}
            onClick={saveMetadata}
            className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
          >
            Salvar alterações
          </Button>
        </div>
      </Modal>
    </div>
  );
}
