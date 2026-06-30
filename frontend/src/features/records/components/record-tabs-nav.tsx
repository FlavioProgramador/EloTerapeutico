"use client";

import { FileText, FolderOpen, History, Target } from "lucide-react";

import { cn } from "@/lib/utils";
import type { RecordTab } from "../types";

interface RecordTabsNavProps {
  activeTab: RecordTab;
  onChange: (tab: RecordTab) => void;
}

const tabs = [
  {
    id: "evolutions",
    label: "Histórico de evoluções",
    shortLabel: "Evoluções",
    icon: History,
  },
  {
    id: "anamnesis",
    label: "Anamnese",
    shortLabel: "Anamnese",
    icon: FileText,
  },
  {
    id: "goals",
    label: "Plano terapêutico",
    shortLabel: "Plano",
    icon: Target,
  },
  {
    id: "documents",
    label: "Documentos",
    shortLabel: "Documentos",
    icon: FolderOpen,
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
      className="flex gap-1 overflow-x-auto border-b border-emerald-400/15 px-1"
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
              "relative flex min-w-max flex-1 items-center justify-center gap-2 px-3 py-3 text-[11px] font-semibold transition",
              active
                ? "text-emerald-300"
                : "text-muted-foreground hover:text-foreground",
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon
              className={cn(
                "h-3.5 w-3.5",
                active ? "text-emerald-300" : "text-muted-foreground",
              )}
            />
            <span className="hidden sm:inline">{label}</span>
            <span className="sm:hidden">{shortLabel}</span>
            <span
              className={cn(
                "absolute inset-x-2 bottom-0 h-0.5 rounded-full transition-all",
                active
                  ? "bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-100"
                  : "opacity-0",
              )}
            />
          </button>
        );
      })}
    </nav>
  );
}
