"use client";

import { useEffect, useRef, useState } from "react";
import {
  ControlBar,
  GridLayout,
  ParticipantTile,
  RoomAudioRenderer,
  RoomContext,
  useConnectionState,
  useParticipants,
  useTracks,
} from "@livekit/components-react";
import {
  ConnectionState,
  ExternalE2EEKeyProvider,
  Room,
  RoomEvent,
  Track,
} from "livekit-client";
import { Expand, Loader2, ShieldCheck, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import type {
  TelemedicineCredentials,
  TelemedicineDeviceChoices,
} from "../types";

interface TelemedicineSessionProps {
  credentials: TelemedicineCredentials;
  choices: TelemedicineDeviceChoices;
  onDisconnected: () => void;
  onError: (message: string) => void;
  onFinish?: () => Promise<void>;
}

export function TelemedicineSession({
  credentials,
  choices,
  onDisconnected,
  onError,
  onFinish,
}: TelemedicineSessionProps) {
  const [room, setRoom] = useState<Room | null>(null);
  const [connecting, setConnecting] = useState(true);
  const [finishing, setFinishing] = useState(false);
  const disconnectHandled = useRef(false);

  useEffect(() => {
    let active = true;
    const keyProvider = new ExternalE2EEKeyProvider();
    const worker = new Worker("/livekit-client.e2ee.worker.js");
    const nextRoom = new Room({
      adaptiveStream: true,
      dynacast: true,
      disconnectOnPageLeave: true,
      encryption: { keyProvider, worker },
    });

    const handleDisconnected = () => {
      if (!disconnectHandled.current) {
        disconnectHandled.current = true;
        onDisconnected();
      }
    };
    const handleEncryptionError = () => {
      onError("Não foi possível manter a chamada com criptografia ponta a ponta.");
    };

    nextRoom.on(RoomEvent.Disconnected, handleDisconnected);
    nextRoom.on(RoomEvent.EncryptionError, handleEncryptionError);

    async function connect() {
      try {
        if (!credentials.e2ee_enabled || !credentials.e2ee_key) {
          throw new Error("E2EE_REQUIRED");
        }
        await keyProvider.setKey(credentials.e2ee_key);
        await nextRoom.setE2EEEnabled(true);
        await nextRoom.connect(credentials.server_url, credentials.token, {
          autoSubscribe: true,
        });
        await nextRoom.localParticipant.setMicrophoneEnabled(
          choices.audioEnabled,
          choices.audioDeviceId ? { deviceId: choices.audioDeviceId } : undefined,
        );
        await nextRoom.localParticipant.setCameraEnabled(
          choices.videoEnabled,
          choices.videoDeviceId ? { deviceId: choices.videoDeviceId } : undefined,
        );
        if (active) {
          setRoom(nextRoom);
          setConnecting(false);
        }
      } catch {
        if (active) {
          setConnecting(false);
          onError("Não foi possível iniciar a chamada com segurança.");
        }
        await nextRoom.disconnect();
      }
    }

    void connect();

    return () => {
      active = false;
      nextRoom.off(RoomEvent.Disconnected, handleDisconnected);
      nextRoom.off(RoomEvent.EncryptionError, handleEncryptionError);
      for (const publication of nextRoom.localParticipant.trackPublications.values()) {
        publication.track?.stop();
      }
      void nextRoom.disconnect();
      worker.terminate();
      setRoom(null);
    };
  }, [choices, credentials, onDisconnected, onError]);

  if (connecting || !room) {
    return (
      <div className="grid min-h-[420px] place-items-center rounded-2xl border border-border bg-card">
        <div className="text-center">
          <Loader2 className="mx-auto size-7 animate-spin text-primary" />
          <p className="mt-3 text-sm font-medium">Preparando conexão protegida...</p>
        </div>
      </div>
    );
  }

  return (
    <RoomContext.Provider value={room}>
      <div className="flex min-h-[70vh] flex-col overflow-hidden rounded-2xl border border-border bg-neutral-950 text-white shadow-2xl">
        <SessionHeader
          onFinish={
            onFinish
              ? async () => {
                  setFinishing(true);
                  try {
                    await onFinish();
                    await room.disconnect();
                  } finally {
                    setFinishing(false);
                  }
                }
              : undefined
          }
          finishing={finishing}
        />
        <SessionStage />
        <RoomAudioRenderer />
        <div className="border-t border-white/10 bg-black/40 p-3">
          <ControlBar
            controls={{
              microphone: true,
              camera: true,
              screenShare: false,
              chat: false,
              leave: true,
            }}
            variation="minimal"
          />
        </div>
      </div>
    </RoomContext.Provider>
  );
}

function SessionHeader({
  onFinish,
  finishing,
}: {
  onFinish?: () => Promise<void>;
  finishing: boolean;
}) {
  const state = useConnectionState();
  const participants = useParticipants();

  const labels: Record<ConnectionState, string> = {
    [ConnectionState.Disconnected]: "Desconectado",
    [ConnectionState.Connecting]: "Conectando",
    [ConnectionState.Connected]: "Conectado",
    [ConnectionState.Reconnecting]: "Reconectando",
    [ConnectionState.SignalReconnecting]: "Reconectando sinal",
  };

  return (
    <header className="flex flex-wrap items-center gap-3 border-b border-white/10 bg-black/40 px-4 py-3">
      <span className="inline-flex items-center gap-2 text-xs font-semibold">
        <ShieldCheck className="size-4 text-emerald-400" />
        E2EE ativa
      </span>
      <span className="inline-flex items-center gap-2 text-xs text-white/70">
        <span className="size-2 rounded-full bg-emerald-400" />
        {labels[state] || "Conectando"}
      </span>
      <span className="inline-flex items-center gap-2 text-xs text-white/70">
        <Users className="size-4" />
        {participants.length} de 2 participantes
      </span>
      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          onClick={() => document.documentElement.requestFullscreen?.()}
          className="grid size-9 place-items-center rounded-lg border border-white/15 text-white/80 hover:bg-white/10"
          aria-label="Abrir em tela cheia"
        >
          <Expand className="size-4" />
        </button>
        {onFinish ? (
          <Button
            size="sm"
            variant="destructive"
            disabled={finishing}
            onClick={onFinish}
          >
            {finishing ? "Encerrando..." : "Encerrar atendimento"}
          </Button>
        ) : null}
      </div>
    </header>
  );
}

function SessionStage() {
  const tracks = useTracks(
    [{ source: Track.Source.Camera, withPlaceholder: true }],
    { onlySubscribed: false },
  );
  const participants = useParticipants();

  return (
    <main className="relative min-h-0 flex-1 p-3">
      {participants.length < 2 ? (
        <div className="absolute inset-x-4 top-4 z-10 rounded-xl border border-white/10 bg-black/60 px-4 py-3 text-center text-sm text-white/80 backdrop-blur">
          Aguardando o outro participante entrar no atendimento.
        </div>
      ) : null}
      <GridLayout tracks={tracks} className="h-full min-h-[420px]">
        <ParticipantTile />
      </GridLayout>
    </main>
  );
}
