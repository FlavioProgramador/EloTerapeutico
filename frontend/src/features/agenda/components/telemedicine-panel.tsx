"use client";

import { useDeferredValue, useMemo, useState } from "react";
import { Ban, Copy, RefreshCw, Send, Video } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  useCreateTelemedicineInvitation,
  useRevokeTelemedicineInvitation,
  useSendTelemedicineInvitation,
  useTelemedicineRooms,
} from "@/features/telemedicine/hooks/use-telemedicine";
import { cn } from "@/lib/utils";
import { SearchInput, StatusBadge, TableShell, Toolbar } from "./agenda-ui";

export function TelemedicinePanel() {
  const [search, setSearch] = useState("");
  const [pendingOnly, setPendingOnly] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const { data: page, isLoading } = useTelemedicineRooms({
    search: deferredSearch || undefined,
    page_size: 100,
  });
  const createInvitation = useCreateTelemedicineInvitation();
  const sendInvitation = useSendTelemedicineInvitation();
  const revokeInvitation = useRevokeTelemedicineInvitation();
  const rooms = (page?.results || []).filter(
    (room) =>
      !pendingOnly ||
      ["pending", "available", "waiting"].includes(room.status),
  );
  const grouped = useMemo(() => {
    const map = new Map<string, typeof rooms>();
    rooms.forEach((room) => {
      const key = new Date(room.appointment_start).toDateString();
      map.set(key, [...(map.get(key) || []), room]);
    });
    return Array.from(map.entries());
  }, [rooms]);

  function createOrRegenerate(roomId: number, hasValidInvitation: boolean) {
    if (
      hasValidInvitation &&
      !window.confirm(
        "O convite atual será revogado imediatamente. Deseja gerar outro?",
      )
    ) {
      return;
    }
    createInvitation.mutate(roomId);
  }

  function sendByEmail(roomId: number, hasValidInvitation: boolean) {
    if (
      hasValidInvitation &&
      !window.confirm(
        "O envio cria um novo convite e revoga o anterior. Deseja continuar?",
      )
    ) {
      return;
    }
    sendInvitation.mutate({ roomId, channel: "email" });
  }

  function revoke(roomId: number) {
    if (
      window.confirm(
        "Revogar este convite impedirá novos acessos do paciente. Continuar?",
      )
    ) {
      revokeInvitation.mutate(roomId);
    }
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
          Aguardando atendimento
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
          <div key={dateKey} className="rounded-xl border border-border bg-card">
            <div className="border-b border-border px-4 py-3 text-sm font-semibold capitalize">
              {new Date(dateKey).toLocaleDateString("pt-BR", {
                weekday: "long",
                day: "2-digit",
                month: "long",
              })}
            </div>
            <div className="divide-y divide-border">
              {items.map((room) => {
                const invitationValid = room.invitation_status.status === "valid";
                const participantState = room.patient_joined_at
                  ? "Paciente já entrou"
                  : invitationValid
                    ? "Convite válido"
                    : "Sem convite válido";
                return (
                  <div
                    key={room.id}
                    className="flex flex-col gap-3 px-4 py-4 lg:flex-row lg:items-center"
                  >
                    <div className="flex min-w-32 items-center gap-3">
                      <span className="grid size-10 place-items-center rounded-full bg-primary/10 font-semibold text-primary">
                        {room.patient_name.charAt(0)}
                      </span>
                      <div>
                        <strong className="block text-sm">
                          {new Date(room.appointment_start).toLocaleTimeString(
                            "pt-BR",
                            { hour: "2-digit", minute: "2-digit" },
                          )}
                        </strong>
                        <span className="text-xs text-muted-foreground">
                          {room.modality === "hybrid" ? "Híbrida" : "Online"}
                        </span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <strong className="block text-sm">{room.patient_name}</strong>
                      <span className="text-xs text-muted-foreground">
                        {room.therapist_name} · {participantState}
                      </span>
                    </div>
                    <StatusBadge status={room.status} />
                    <div className="flex flex-wrap gap-2 lg:justify-end">
                      <Button
                        size="sm"
                        disabled={!room.is_accessible}
                        leftIcon={<Video className="size-3.5" />}
                        onClick={() =>
                          window.open(
                            `/dashboard/agenda/atendimento-online/${room.id}`,
                            "_blank",
                            "noopener,noreferrer",
                          )
                        }
                      >
                        Iniciar
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={!room.is_accessible || sendInvitation.isPending}
                        leftIcon={<Send className="size-3.5" />}
                        onClick={() => sendByEmail(room.id, invitationValid)}
                      >
                        Enviar convite
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={!room.is_accessible || createInvitation.isPending}
                        leftIcon={
                          invitationValid ? (
                            <RefreshCw className="size-3.5" />
                          ) : (
                            <Copy className="size-3.5" />
                          )
                        }
                        onClick={() => createOrRegenerate(room.id, invitationValid)}
                      >
                        {invitationValid ? "Regenerar" : "Gerar e copiar"}
                      </Button>
                      {invitationValid ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={revokeInvitation.isPending}
                          leftIcon={<Ban className="size-3.5" />}
                          onClick={() => revoke(room.id)}
                        >
                          Revogar
                        </Button>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </section>
  );
}
