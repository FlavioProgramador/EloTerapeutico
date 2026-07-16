"use client";

import { X } from "lucide-react";
import { useRef } from "react";

import { Button } from "@/components/ui/button";
import { useEvolutionEditorController } from "../hooks/use-evolution-editor-controller";
import { EvolutionContentSection } from "./evolution-editor/evolution-content-section";
import type { EvolutionEditorProps } from "./evolution-editor/evolution-editor.types";
import { EvolutionLinkSection } from "./evolution-editor/evolution-link-section";
import { EvolutionSecuritySection } from "./evolution-editor/evolution-security-section";

export { handleEditorShortcut } from "./evolution-editor/evolution-editor.utils";

export function EvolutionEditor(props: EvolutionEditorProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const templateButtonRef = useRef<HTMLButtonElement>(null);
  const controller = useEvolutionEditorController(props, dialogRef);

  if (!props.open) return null;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-0 backdrop-blur-[2px] sm:p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) controller.requestClose();
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
              {controller.editing ? "Editar Evolução" : "Nova Evolução"}
            </h2>
            <p
              id="evolution-modal-description"
              className="mt-1 text-xs text-muted-foreground"
            >
              {controller.editing
                ? "Atualize os dados permitidos deste registro clínico."
                : "Adicione uma nova evolução ao prontuário do paciente."}
            </p>
          </div>
          <button
            type="button"
            onClick={controller.requestClose}
            disabled={controller.busy}
            aria-label="Fechar modal"
            className="grid size-8 place-items-center rounded-md text-muted-foreground transition hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50"
          >
            <X className="size-4" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="space-y-5">
            <EvolutionLinkSection controller={controller} />
            <EvolutionContentSection
              controller={controller}
              templateButtonRef={templateButtonRef}
            />
            <EvolutionSecuritySection controller={controller} />
          </div>
        </div>

        <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-border bg-card px-5 py-3">
          <Button
            type="button"
            variant="outline"
            onClick={controller.requestClose}
            disabled={controller.busy}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={controller.submit}
            isLoading={controller.submitting}
            disabled={
              controller.busy ||
              !controller.form.content.trim() ||
              !controller.form.sessionDate
            }
          >
            {controller.editing || controller.persistedEvolutionId
              ? "Salvar Alterações"
              : "Adicionar Registro"}
          </Button>
        </footer>
      </div>
    </div>
  );
}
