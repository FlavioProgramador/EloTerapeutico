"use client";

import { useRef, useState } from "react";
import {
  FileText,
  ImageIcon,
  LoaderCircle,
  Trash2,
  UploadCloud,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type {
  EvolutionAttachment,
  PendingEvolutionAttachment,
} from "../evolution-modal.types";

const MAX_FILE_BYTES = 10 * 1024 * 1024;
const MAX_FILES = 10;
const ALLOWED = new Map([
  ["image/jpeg", [".jpg", ".jpeg"]],
  ["image/png", [".png"]],
  ["image/gif", [".gif"]],
  ["image/webp", [".webp"]],
  ["application/pdf", [".pdf"]],
]);

interface EvolutionAttachmentDropzoneProps {
  pending: PendingEvolutionAttachment[];
  existing: EvolutionAttachment[];
  removedExistingIds: number[];
  onPendingChange: (files: PendingEvolutionAttachment[]) => void;
  onRemoveExisting: (id: number) => void;
  disabled?: boolean;
}

export function EvolutionAttachmentDropzone({
  pending,
  existing,
  removedExistingIds,
  onPendingChange,
  onRemoveExisting,
  disabled,
}: EvolutionAttachmentDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const visibleExisting = existing.filter(
    (item) => !removedExistingIds.includes(item.id),
  );

  const addFiles = (selected: FileList | File[]) => {
    const available = Math.max(
      0,
      MAX_FILES - visibleExisting.length - pending.length,
    );
    const additions = Array.from(selected)
      .slice(0, available)
      .map(validateFile);
    onPendingChange([...pending, ...additions]);
  };

  return (
    <div className="space-y-3">
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.gif,.webp,.pdf"
        className="sr-only"
        onChange={(event) => {
          if (event.target.files) addFiles(event.target.files);
          event.target.value = "";
        }}
        disabled={disabled}
      />
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          if (!disabled) addFiles(event.dataTransfer.files);
        }}
        className={cn(
          "flex min-h-28 w-full flex-col items-center justify-center rounded-lg border border-dashed border-border bg-secondary/10 px-4 py-5 text-center transition",
          "hover:border-primary/60 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
          dragging && "border-primary bg-primary/10",
          disabled && "cursor-not-allowed opacity-60",
        )}
        aria-label="Selecionar anexos da evolução"
      >
        <UploadCloud className="size-7 text-muted-foreground" />
        <strong className="mt-2 text-xs text-foreground">
          Arraste arquivos ou clique para selecionar
        </strong>
        <span className="mt-1 text-[11px] text-muted-foreground">
          JPG, PNG, GIF, WebP ou PDF (máx. 10 MB)
        </span>
      </button>

      {(visibleExisting.length > 0 || pending.length > 0) && (
        <div className="space-y-2" aria-live="polite">
          {visibleExisting.map((item) => (
            <AttachmentRow
              key={`existing-${item.id}`}
              name={item.original_name}
              type={item.content_type}
              size={item.size_bytes}
              onRemove={() => onRemoveExisting(item.id)}
              disabled={disabled}
            />
          ))}
          {pending.map((item) => (
            <AttachmentRow
              key={item.id}
              name={item.file.name}
              type={item.file.type}
              size={item.file.size}
              progress={item.progress}
              error={item.error}
              onRemove={() =>
                onPendingChange(
                  pending.filter((candidate) => candidate.id !== item.id),
                )
              }
              disabled={disabled}
            />
          ))}
        </div>
      )}
      <p className="text-[11px] text-muted-foreground">
        {visibleExisting.length + pending.length} de {MAX_FILES} arquivos
        selecionados.
      </p>
    </div>
  );
}

function validateFile(file: File): PendingEvolutionAttachment {
  const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
  const allowedExtensions = ALLOWED.get(file.type);
  let error: string | undefined;
  if (!allowedExtensions?.includes(extension)) {
    error = "Tipo ou extensão não permitidos.";
  } else if (file.size <= 0) {
    error = "O arquivo está vazio.";
  } else if (file.size > MAX_FILE_BYTES) {
    error = "O arquivo excede 10 MB.";
  }
  return {
    id: `${Date.now()}-${crypto.randomUUID()}`,
    file,
    progress: 0,
    error,
  };
}

function AttachmentRow({
  name,
  type,
  size,
  progress,
  error,
  onRemove,
  disabled,
}: {
  name: string;
  type: string;
  size: number;
  progress?: number;
  error?: string;
  onRemove: () => void;
  disabled?: boolean;
}) {
  const isImage = type.startsWith("image/");
  const uploading = progress !== undefined && progress > 0 && progress < 100;
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border border-border bg-background p-2.5",
        error && "border-destructive/50 bg-destructive/5",
      )}
    >
      <span className="grid size-10 shrink-0 place-items-center overflow-hidden rounded-md bg-secondary text-muted-foreground">
        {isImage ? (
          <ImageIcon className="size-5" />
        ) : (
          <FileText className="size-5" />
        )}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-semibold text-foreground">{name}</p>
        <p className="mt-0.5 text-[11px] text-muted-foreground">
          {formatBytes(size)} · {type || "tipo desconhecido"}
        </p>
        {uploading && (
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
        {error && <p className="mt-1 text-[11px] text-destructive">{error}</p>}
      </div>
      {uploading ? (
        <LoaderCircle className="size-4 animate-spin text-primary" />
      ) : (
        <Button
          type="button"
          size="icon"
          variant="ghost"
          onClick={onRemove}
          disabled={disabled}
          aria-label={`Remover ${name}`}
        >
          <Trash2 className="size-4" />
        </Button>
      )}
    </div>
  );
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}
