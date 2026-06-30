import {
  Archive,
  CalendarPlus,
  Eye,
  FileText,
  MoreHorizontal,
  Pencil,
  RotateCcw,
} from "lucide-react";
import { useRouter } from "next/navigation";

import type { PatientListItem } from "./patient-list-item";

interface Props {
  patient: PatientListItem;
  canManage: boolean;
  canAccessRecords: boolean;
  onArchive: () => void;
  onRestore: () => void;
}

export function PatientActionsMenu({
  patient,
  canManage,
  canAccessRecords,
  onArchive,
  onRestore,
}: Props) {
  const router = useRouter();
  const item =
    "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-xs hover:bg-secondary";

  return (
    <details className="relative">
      <summary
        aria-label={`Ações de ${patient.display_name}`}
        className="grid h-9 w-9 cursor-pointer list-none place-items-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 [&::-webkit-details-marker]:hidden"
      >
        <MoreHorizontal className="h-4 w-4" />
      </summary>
      <div className="absolute right-0 z-30 mt-1 w-52 rounded-lg border border-border bg-popover p-1 text-popover-foreground shadow-lg">
        <button
          type="button"
          className={item}
          onClick={() => router.push(`/dashboard/patients/${patient.id}`)}
        >
          <Eye className="h-4 w-4" /> Visualizar
        </button>
        {canManage && (
          <button
            type="button"
            className={item}
            onClick={() =>
              router.push(`/dashboard/patients/${patient.id}?edit=true`)
            }
          >
            <Pencil className="h-4 w-4" /> Editar cadastro
          </button>
        )}
        {canAccessRecords && (
          <button
            type="button"
            className={item}
            onClick={() => router.push(`/dashboard/records/${patient.id}`)}
          >
            <FileText className="h-4 w-4" /> Abrir prontuário
          </button>
        )}
        <button
          type="button"
          className={item}
          onClick={() => router.push(`/dashboard/agenda?patient=${patient.id}`)}
        >
          <CalendarPlus className="h-4 w-4" /> Agendar sessão
        </button>
        {canManage && patient.status !== "archived" && (
          <button
            type="button"
            className={`${item} text-destructive hover:bg-destructive/10`}
            onClick={onArchive}
          >
            <Archive className="h-4 w-4" /> Arquivar
          </button>
        )}
        {canManage && patient.status === "archived" && (
          <button type="button" className={item} onClick={onRestore}>
            <RotateCcw className="h-4 w-4" /> Restaurar
          </button>
        )}
      </div>
    </details>
  );
}
