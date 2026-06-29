"use client";

import { useRef, useState } from "react";
import { Archive, Download, FileText, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { recordWorkspaceService } from "../services/record-workspace.service";
import type { ClinicalDocument } from "../types";

interface Props {
  documents: ClinicalDocument[];
  loading: boolean;
  uploading: boolean;
  onUpload: (data: FormData) => Promise<void>;
  onArchive: (id: number) => Promise<void>;
}

const categories = [
  ["consent", "Termo de consentimento"], ["report", "Relatório"],
  ["referral", "Encaminhamento"], ["certificate", "Atestado"],
  ["assessment", "Avaliação"], ["scale", "Escala ou teste"],
  ["patient_file", "Documento do paciente"], ["other", "Outro"],
] as const;

export function DocumentsTab({ documents, loading, uploading, onUpload, onArchive }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [category, setCategory] = useState("other");
  const [description, setDescription] = useState("");

  const upload = async (file?: File) => {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      window.alert("O arquivo deve possuir no máximo 10 MB.");
      return;
    }
    const data = new FormData();
    data.append("file", file);
    data.append("category", category);
    data.append("description", description);
    await onUpload(data);
    setDescription("");
    if (inputRef.current) inputRef.current.value = "";
  };

  if (loading) return <div className="h-[30rem] animate-pulse rounded-xl bg-secondary" />;

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-dashed border-primary/30 bg-primary/5 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <UploadCloud className="mt-0.5 h-5 w-5 text-primary" />
            <div><h3 className="text-sm font-bold">Anexar documento</h3><p className="mt-1 text-xs text-muted-foreground">PDF, JPG, PNG, TXT ou DOCX com até 10 MB.</p></div>
          </div>
          <div className="grid gap-2 sm:grid-cols-[12rem_16rem_auto]">
            <select value={category} onChange={(event) => setCategory(event.target.value)} className="h-9 rounded-md border border-border bg-background px-3 text-xs">
              {categories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Descrição opcional" className="h-9 rounded-md border border-border bg-background px-3 text-xs" />
            <input ref={inputRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.txt,.docx" className="sr-only" onChange={(event) => upload(event.target.files?.[0])} />
            <Button size="sm" isLoading={uploading} onClick={() => inputRef.current?.click()}>Selecionar arquivo</Button>
          </div>
        </div>
      </section>

      {documents.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-14 text-center"><FileText className="mx-auto h-6 w-6 text-muted-foreground" /><p className="mt-3 text-xs font-semibold">Nenhum documento anexado</p></div>
      ) : (
        <section className="overflow-hidden rounded-xl border border-border bg-card">
          {documents.map((document) => (
            <article key={document.id} className="grid gap-3 border-b border-border px-4 py-3 last:border-0 md:grid-cols-[minmax(0,1fr)_12rem_7rem] md:items-center">
              <div className="flex min-w-0 items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 text-primary"><FileText className="h-4 w-4" /></span><div className="min-w-0"><strong className="block truncate text-xs">{document.original_name}</strong><small className="mt-1 block text-[9px] text-muted-foreground">{document.category_display} · versão {document.version}</small></div></div>
              <span className="text-[10px] text-muted-foreground">{(document.size_bytes / 1024).toFixed(1)} KB</span>
              <div className="flex justify-end gap-1">
                <button type="button" onClick={() => recordWorkspaceService.downloadDocument(document)} className="rounded-md p-2 text-muted-foreground hover:bg-secondary" aria-label="Baixar"><Download className="h-4 w-4" /></button>
                <button type="button" onClick={() => window.confirm("Arquivar este documento?") && onArchive(document.id)} className="rounded-md p-2 text-muted-foreground hover:bg-secondary" aria-label="Arquivar"><Archive className="h-4 w-4" /></button>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
