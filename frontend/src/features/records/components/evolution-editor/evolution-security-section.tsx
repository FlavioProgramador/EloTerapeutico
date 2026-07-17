import { LockKeyhole, ShieldCheck } from "lucide-react";

import type { EvolutionEditorController } from "../../hooks/use-evolution-editor-controller";
import { EvolutionAttachmentDropzone } from "../evolution-attachment-dropzone";

export function EvolutionSecuritySection({
  controller,
}: {
  controller: EvolutionEditorController;
}) {
  return (
    <>
      <section>
        <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-secondary/10 p-4">
          <input
            type="checkbox"
            checked={controller.form.confidential}
            onChange={(event) =>
              controller.changeForm("confidential", event.target.checked)
            }
            disabled={controller.busy}
            aria-describedby="evolution-confidential-description"
            className="mt-0.5 size-4 rounded border-border"
          />
          <span>
            <strong className="flex items-center gap-2 text-xs text-foreground">
              <LockKeyhole className="size-3.5 text-muted-foreground" />
              Marcar como confidencial
            </strong>
            <span
              id="evolution-confidential-description"
              className="mt-1 block text-[11px] leading-4 text-muted-foreground"
            >
              Apenas você (autor) e administradores com permissão clínica
              explícita poderão visualizar esta evolução. Secretárias e outros
              profissionais não autorizados não terão acesso.
            </span>
          </span>
        </label>
      </section>

      <section className="space-y-2">
        <label className="text-xs font-semibold text-foreground">Anexos</label>
        <EvolutionAttachmentDropzone
          pending={controller.pendingFiles}
          existing={controller.existingAttachments}
          removedExistingIds={controller.removedAttachmentIds}
          onPendingChange={controller.updatePendingFiles}
          onRemoveExisting={controller.removeExistingAttachment}
          disabled={controller.busy}
        />
        {controller.errors.attachments && (
          <p role="alert" className="text-[11px] text-destructive">
            {controller.errors.attachments}
          </p>
        )}
      </section>

      <div className="flex items-start gap-2 rounded-lg border border-primary/20 bg-primary/5 p-3 text-[11px] text-muted-foreground">
        <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
        O conteúdo é enviado somente ao servidor autenticado, armazenado de
        forma criptografada e registrado em auditoria. Nenhum texto clínico é
        salvo no navegador.
      </div>

      {controller.errors.form && (
        <p
          role="alert"
          aria-live="assertive"
          className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive"
        >
          {controller.errors.form}
        </p>
      )}
    </>
  );
}
