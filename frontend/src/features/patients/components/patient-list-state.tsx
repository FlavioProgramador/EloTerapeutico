import { Search, UsersRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export function PatientListError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-10 text-center">
      <p className="text-sm font-semibold text-foreground">Não foi possível carregar a listagem.</p>
      <Button className="mt-4" size="sm" variant="outline" onClick={onRetry}>Tentar novamente</Button>
    </div>
  );
}

export function PatientListEmpty({
  onAction,
  label,
  isFiltered,
}: {
  onAction: () => void;
  label: string;
  isFiltered?: boolean;
}) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card">
      <EmptyState
        icon={
          isFiltered ? (
            <Search className="h-6 w-6 text-muted-foreground" />
          ) : (
            <UsersRound className="h-6 w-6 text-muted-foreground" />
          )
        }
        title={isFiltered ? "Nenhum paciente encontrado" : "Sua lista de pacientes está vazia"}
        description={
          isFiltered
            ? "Não encontramos resultados para os filtros aplicados. Tente ajustar sua busca ou limpar os filtros."
            : "Comece cadastrando seu primeiro paciente para gerenciar prontuários, agenda e muito mais."
        }
        action={
          <Button size="sm" variant="outline" onClick={onAction}>
            {label}
          </Button>
        }
      />
    </div>
  );
}
