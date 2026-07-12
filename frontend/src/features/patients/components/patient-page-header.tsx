import { BookOpen, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";

export function PatientPageHeader({ onNew }: { onNew: () => void }) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Pacientes</h1>
          <BookOpen className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
        </div>
        <p className="mt-1 text-sm text-muted-foreground">Gerencie os pacientes da clínica</p>
      </div>
      <Button size="default" onClick={onNew} leftIcon={<Plus className="h-4 w-4" />}>
        Novo paciente
      </Button>
    </header>
  );
}
