"use client";

import { useRef } from "react";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Redo2,
  Undo2,
} from "lucide-react";

import { cn } from "@/lib/utils";

interface ClinicalMarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
  maxLength?: number;
}

export function ClinicalMarkdownEditor({
  value,
  onChange,
  error,
  disabled,
  maxLength = 50_000,
}: ClinicalMarkdownEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const replaceSelection = (
    before: string,
    after = before,
    linePrefix = false,
  ) => {
    const element = textareaRef.current;
    if (!element || disabled) return;
    const start = element.selectionStart;
    const end = element.selectionEnd;
    const selected = value.slice(start, end);
    let replacement: string;

    if (linePrefix) {
      const lines = (selected || "Item").split("\n");
      replacement = lines
        .map((line, index) => before.replace("{n}", String(index + 1)) + line)
        .join("\n");
    } else {
      replacement = `${before}${selected || "texto"}${after}`;
    }

    const next = `${value.slice(0, start)}${replacement}${value.slice(end)}`;
    onChange(next.slice(0, maxLength));
    requestAnimationFrame(() => {
      element.focus();
      const selectionStart = start + before.length;
      const selectionEnd = start + replacement.length - after.length;
      element.setSelectionRange(selectionStart, selectionEnd);
    });
  };

  const nativeCommand = (command: "undo" | "redo") => {
    textareaRef.current?.focus();
    document.execCommand(command);
  };

  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border bg-background",
        error ? "border-destructive" : "border-border",
        disabled && "opacity-70",
      )}
    >
      <div
        className="flex min-h-10 items-center gap-0.5 overflow-x-auto border-b border-border px-2"
        role="toolbar"
        aria-label="Formatação da evolução"
      >
        <ToolButton label="Negrito" onClick={() => replaceSelection("**")}>
          <Bold className="size-4" />
        </ToolButton>
        <ToolButton label="Itálico" onClick={() => replaceSelection("*")}>
          <Italic className="size-4" />
        </ToolButton>
        <span className="mx-1 h-5 w-px shrink-0 bg-border" />
        <ToolButton
          label="Lista com marcadores"
          onClick={() => replaceSelection("- ", "", true)}
        >
          <List className="size-4" />
        </ToolButton>
        <ToolButton
          label="Lista numerada"
          onClick={() => replaceSelection("{n}. ", "", true)}
        >
          <ListOrdered className="size-4" />
        </ToolButton>
        <span className="mx-1 h-5 w-px shrink-0 bg-border" />
        <ToolButton label="Desfazer" onClick={() => nativeCommand("undo")}>
          <Undo2 className="size-4" />
        </ToolButton>
        <ToolButton label="Refazer" onClick={() => nativeCommand("redo")}>
          <Redo2 className="size-4" />
        </ToolButton>
      </div>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value.slice(0, maxLength))}
        disabled={disabled}
        rows={11}
        required
        aria-invalid={Boolean(error)}
        aria-describedby={error ? "evolution-content-error" : undefined}
        placeholder="Registre a evolução clínica, intervenções e observações relevantes..."
        className="min-h-64 w-full resize-y bg-transparent p-4 text-sm leading-6 text-foreground outline-none placeholder:text-muted-foreground/70"
      />
      <div className="flex items-center justify-between border-t border-border px-3 py-2 text-[11px] text-muted-foreground">
        <span>Markdown seguro: negrito, itálico e listas.</span>
        <span>{value.length.toLocaleString("pt-BR")} / {maxLength.toLocaleString("pt-BR")}</span>
      </div>
    </div>
  );
}

function ToolButton({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className="grid size-8 shrink-0 place-items-center rounded-md text-muted-foreground transition hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
    >
      {children}
    </button>
  );
}
