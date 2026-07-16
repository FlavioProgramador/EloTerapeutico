import { ChevronDown, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { EvolutionEditorController } from "../../hooks/use-evolution-editor-controller";
import { ClinicalMarkdownEditor } from "../clinical-markdown-editor";

export function EvolutionContentSection({
  controller,
}: {
  controller: EvolutionEditorController;
}) {
  return (
    <section className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <label className="text-xs font-semibold text-foreground">
          Evolução / Anotações <span className="text-destructive">*</span>
        </label>
        <div className="relative">
          <Button
            ref={controller.templateButtonRef}
            type="button"
            size="sm"
            variant="outline"
            onClick={() =>
              controller.setTemplateMenuOpen((value) => !value)
            }
            disabled={controller.busy}
            leftIcon={<FileText className="size-3.5" />}
            rightIcon={<ChevronDown className="size-3.5" />}
          >
            Usar Template
          </Button>
          {controller.templateMenuOpen && (
            <div className="absolute right-0 top-11 z-20 max-h-64 w-72 overflow-y-auto rounded-lg border border-border bg-popover p-1 shadow-xl">
              {controller.templatesQuery.isLoading ? (
                <p className="px-3 py-4 text-xs text-muted-foreground">
                  Carregando templates...
                </p>
              ) : controller.templatesQuery.isError ? (
                <p className="px-3 py-4 text-xs text-destructive">
                  Falha ao carregar templates.
                </p>
              ) : controller.templatesQuery.data?.length ? (
                controller.templatesQuery.data.map((template) => (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => controller.chooseTemplate(template)}
                    className="w-full rounded-md px-3 py-2 text-left transition hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    <strong className="block text-xs text-foreground">
                      {template.name}
                    </strong>
                    <span className="mt-0.5 block text-[10px] text-muted-foreground">
                      {template.is_system
                        ? "Template da clínica"
                        : "Meu template"}
                    </span>
                  </button>
                ))
              ) : (
                <p className="px-3 py-4 text-xs text-muted-foreground">
                  Nenhum template disponível.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {controller.pendingTemplate && (
        <div className="rounded-lg border border-primary/25 bg-primary/5 p-3">
          <p className="text-xs font-semibold text-foreground">
            Como aplicar “{controller.pendingTemplate.name}”?
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              onClick={() => controller.applyTemplate("replace")}
            >
              Substituir texto
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => controller.applyTemplate("append")}
            >
              Anexar ao final
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => controller.setPendingTemplate(null)}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}

      <ClinicalMarkdownEditor
        value={controller.form.content}
        onChange={(value) => controller.changeForm("content", value)}
        error={controller.errors.content}
        disabled={controller.busy}
      />
      {controller.errors.content && (
        <p
          id="evolution-content-error"
          role="alert"
          className="text-[11px] text-destructive"
        >
          {controller.errors.content}
        </p>
      )}
    </section>
  );
}
