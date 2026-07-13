"use client";

import {
  Calendar,
  History,
  FolderOpen,
  FileSpreadsheet,
  FileDown,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { RecordTab } from "../types";

interface RecordTabsNavProps {
  activeTab: RecordTab;
  onChange: (tab: RecordTab) => void;
}

const tabs = [
  {
    id: "appointments",
    label: "Consultas",
    shortLabel: "Consultas",
    icon: Calendar,
  },
  {
    id: "evolutions",
    label: "Evoluções",
    shortLabel: "Evoluções",
    icon: History,
  },
  {
    id: "documents",
    label: "Arquivos",
    shortLabel: "Arquivos",
    icon: FolderOpen,
  },
  {
    id: "forms",
    label: "Formulários",
    shortLabel: "Formulários",
    icon: FileSpreadsheet,
  },
  {
    id: "exports",
    label: "Exportações",
    shortLabel: "Exportações",
    icon: FileDown,
  },
] satisfies Array<{
  id: RecordTab;
  label: string;
  shortLabel: string;
  icon: typeof History;
}>;

export function RecordTabsNav({ activeTab, onChange }: RecordTabsNavProps) {
  return (
    <nav
      className="flex gap-1 overflow-x-auto border-b border-border px-1"
      aria-label="Seções do prontuário"
    >
      {tabs.map(({ id, label, shortLabel, icon: Icon }) => {
        const active = activeTab === id;
        return (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            className={cn(
              "relative flex min-w-max flex-1 items-center justify-center gap-2 px-3 py-3 text-sm font-semibold transition-all duration-200",
              active
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-muted-foreground hover:text-foreground",
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon
              className={cn(
                "h-4 w-4 transition-colors",
                active ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground",
              )}
            />
            <span className="hidden sm:inline">{label}</span>
            <span className="sm:hidden">{shortLabel}</span>
            <span
              className={cn(
                "absolute inset-x-2 bottom-0 h-0.5 rounded-full transition-all duration-200",
                active
                  ? "bg-emerald-500 opacity-100"
                  : "opacity-0",
              )}
            />
          </button>
        );
      })}
    </nav>
  );
}
