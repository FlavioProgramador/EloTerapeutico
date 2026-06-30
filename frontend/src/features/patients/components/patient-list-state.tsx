import { Button } from "@/components/ui/button";

export function PatientListError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-10 text-center">
      <p className="text-sm font-semibold text-foreground">Não foi possível carregar a listagem.</p>
      <Button className="mt-4" size="sm" variant="outline" onClick={onRetry}>Tentar novamente</Button>
    </div>
  );
}

export function PatientListEmpty({ onAction, label }: { onAction: () => void; label: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card p-10 text-center">
      <p className="text-sm font-semibold text-foreground">Nenhum paciente encontrado.</p>
      <Button className="mt-4" size="sm" variant="outline" onClick={onAction}>{label}</Button>
    </div>
  );
}
