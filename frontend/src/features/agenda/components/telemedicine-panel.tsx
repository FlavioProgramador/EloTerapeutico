"use client";

import { useDeferredValue, useMemo, useState } from "react";
import { Copy, MoreHorizontal, Video } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTelemedicine, useTelemedicineAction } from "../hooks/use-agenda";
import { SearchInput, StatusBadge, TableShell, Toolbar } from "./agenda-ui";

export function TelemedicinePanel() {
  const [search, setSearch] = useState("");
  const [pendingOnly, setPendingOnly] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const { data: page, isLoading } = useTelemedicine({
    search: deferredSearch || undefined,
    page_size: 100,
  });
  const action = useTelemedicineAction();
  const rooms = (page?.results || []).filter(
    (room) => !pendingOnly || room.status === "pending",
  );
  const grouped = useMemo(() => {
    const map = new Map<string, typeof rooms>();
    rooms.forEach((room) => {
      const key = new Date(room.appointment_start).toDateString();
      map.set(key, [...(map.get(key) || []), room]);
    });
    return Array.from(map.entries());
  }, [rooms]);

  async function copy(value: string, label: string) {
    await navigator.clipboard.writeText(value);
    toast.success(`${label} copiado.`);
  }

  return (
    <section className="space-y-4">
      <Toolbar>
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Buscar paciente, profissional ou tipo..."
        />
        <button
          type="button"
          onClick={() => setPendingOnly((value) => !value)}
          className={cn(
            "h-9 rounded-md border px-3 text-xs font-semibold",
            pendingOnly
              ? "border-primary bg-primary/10 text-primary"
              : "border-border text-muted-foreground",
          )}
        >
          Apenas pendentes
        </button>
        <span className="ml-auto text-xs text-muted-foreground">
          {rooms.length} consulta{rooms.length === 1 ? "" : "s"}
        </span>
      </Toolbar>

      {isLoading ? (
        <TableShell loading empty={false} emptyText="">
          {null}
        </TableShell>
      ) : grouped.length === 0 ? (
        <TableShell
          loading={false}
          empty
          emptyText="Nenhuma consulta online encontrada."
        >
          {null}
        </TableShell>
      ) : (
        grouped.map(([dateKey, items]) => (
          <div
            key={dateKey}
            className="rounded-xl border border-border bg-card"
          >
            <div className="border-b border-border px-4 py-3 text-sm font-semibold capitalize">
              {new Date(dateKey).toLocaleDateString("pt-BR", {
                weekday: "long",
                day: "2-digit",
                month: "long",
              })}
            </div>
            <div className="divide-y divide-border">
              {items.map((room) => (
                <div
                  key={room.id}
                  className="flex flex-col gap-3 px-4 py-4 md:flex-row md:items-center"
                >
                  <div className="flex min-w-32 items-center gap-3">
                    <span className="grid size-10 place-items-center rounded-full bg-primary/10 font-semibold text-primary">
                      {room.patient_name.charAt(0)}
                    </span>
                    <div>
                      <strong className="block text-sm">
                        {new Date(room.appointment_start).toLocaleTimeString(
                          "pt-BR",
                          {
                            hour: "2-digit",
                            minute: "2-digit",
                          },
                        )}
                      </strong>
                      <span className="text-xs text-muted-foreground">
                        Telemedicina
                      </span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <strong className="block text-sm">
                      {room.patient_name}
                    </strong>
                    <span className="text-xs text-muted-foreground">
                      {room.therapist_name}
                    </span>
                  </div>
                  <StatusBadge status={room.status} />
                  <div className="flex flex-wrap justify-end gap-1">
                    <Button
                      size="sm"
                      onClick={() =>
                        action.mutate({ id: room.id, action: "open" })
                      }
                      disabled={!room.is_accessible}
                      leftIcon={<Video className="size-3.5" />}
                    >
                      Abrir
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() =>
                        copy(room.patient_link, "Link do paciente")
                      }
                      aria-label="Copiar link do paciente"
                    >
                      <Copy className="size-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() =>
                        copy(room.professional_link, "Link do profissional")
                      }
                      aria-label="Copiar link do profissional"
                    >
                      <Copy className="size-4 text-primary" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() =>
                        action.mutate({ id: room.id, action: "regenerate" })
                      }
                      aria-label="Regenerar links"
                    >
                      <MoreHorizontal className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </section>
  );
}
