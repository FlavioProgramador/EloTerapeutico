"use client";

import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  FlaskConical,
  Loader2,
  Power,
  Save,
  Send,
  ShieldCheck,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import {
  communicationChannelLabel,
  communicationConnectionStatusLabel,
} from "./communications.utils";
import {
  useRemoveCommunicationChannel,
  useSendCommunicationChannelTest,
  useTestCommunicationChannelConnection,
  useToggleCommunicationChannel,
  useUpdateCommunicationChannel,
} from "./use-communications";
import type {
  ChannelConfigurationField,
  CommunicationChannelConfig,
  UpdateChannelConfigurationPayload,
} from "./types";

const steps = [
  "Provedor",
  "Credenciais",
  "Remetente",
  "Preferências",
  "Teste",
  "Ativação",
];

const senderFields = new Set([
  "sender",
  "sender_name",
  "sender_email",
  "reply_to",
  "phone_number",
]);

const preferenceFields = new Set([
  "signature",
  "tracking_enabled",
  "desktop_enabled",
  "sound_enabled",
  "duration_seconds",
  "open_in_web",
  "country_code",
  "timeout",
  "monthly_limit",
  "default_language",
  "api_version",
]);

function humanError(error: unknown): string {
  const response = (error as { response?: { data?: unknown } })?.response?.data;

  if (typeof response === "string") return response;

  if (response && typeof response === "object") {
    const values = Object.values(response as Record<string, unknown>).flatMap(
      (value) => (Array.isArray(value) ? value : [value]),
    );
    const message = values.find((value) => typeof value === "string");
    if (typeof message === "string") return message;
  }

  return "Não foi possível concluir a operação. Revise os campos e tente novamente.";
}

function initialMetadata(
  config: CommunicationChannelConfig,
  providerId: string,
) {
  const providers = config.available_providers ?? [];
  const provider = providers.find((item) => item.id === providerId);
  const defaults = Object.fromEntries(
    (provider?.fields ?? [])
      .filter((field) => !field.secret && field.default !== undefined)
      .map((field) => [
        field.name,
        field.default as string | number | boolean,
      ]),
  );

  return { ...defaults, ...(config.metadata ?? {}) };
}

interface ChannelConfigurationModalProps {
  channel: CommunicationChannelConfig;
  onClose: () => void;
}

export function ChannelConfigurationModal({
  channel,
  onClose,
}: ChannelConfigurationModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [currentChannel, setCurrentChannel] = useState(channel);
  const availableProviders = currentChannel.available_providers ?? [];
  const initialProvider =
    currentChannel.provider || availableProviders[0]?.id || "";
  const [step, setStep] = useState(0);
  const [providerId, setProviderId] = useState(initialProvider);
  const [metadata, setMetadata] = useState<
    Record<string, string | number | boolean>
  >(() => initialMetadata(currentChannel, initialProvider));
  const [secrets, setSecrets] = useState<Record<string, string>>({});
  const [testDestination, setTestDestination] = useState("");
  const [manualTestUrl, setManualTestUrl] = useState<string | null>(null);

  const updateChannel = useUpdateCommunicationChannel();
  const testConnection = useTestCommunicationChannelConnection();
  const sendTest = useSendCommunicationChannelTest();
  const toggleChannel = useToggleCommunicationChannel();
  const removeChannel = useRemoveCommunicationChannel();

  const provider = useMemo(
    () => availableProviders.find((item) => item.id === providerId),
    [availableProviders, providerId],
  );

  const pending =
    updateChannel.isPending ||
    testConnection.isPending ||
    sendTest.isPending ||
    toggleChannel.isPending ||
    removeChannel.isPending;

  const technicalFields = (provider?.fields ?? []).filter(
    (field) =>
      !field.secret &&
      !senderFields.has(field.name) &&
      !preferenceFields.has(field.name),
  );
  const credentialFields = (provider?.fields ?? []).filter(
    (field) => field.secret,
  );
  const senderConfigurationFields = (provider?.fields ?? []).filter(
    (field) => !field.secret && senderFields.has(field.name),
  );
  const preferenceConfigurationFields = (provider?.fields ?? []).filter(
    (field) => !field.secret && preferenceFields.has(field.name),
  );

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) {
        onClose();
      }

      if (event.key !== "Tab" || !panelRef.current) return;

      const focusableItems = panelRef.current.querySelectorAll<HTMLElement>(
        "button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex]:not([tabindex='-1'])",
      );

      if (!focusableItems.length) return;

      const first = focusableItems[0];
      const last = focusableItems[focusableItems.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    const focusTimer = window.setTimeout(() => {
      panelRef.current
        ?.querySelector<HTMLElement>("button:not(:disabled)")
        ?.focus();
    }, 0);

    return () => {
      window.clearTimeout(focusTimer);
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, pending]);

  function selectProvider(nextProvider: string) {
    setProviderId(nextProvider);
    setMetadata(initialMetadata(currentChannel, nextProvider));
    setSecrets({});
    setManualTestUrl(null);
  }

  function updateField(
    field: ChannelConfigurationField,
    value: string | number | boolean,
  ) {
    if (field.secret) {
      setSecrets((current) => ({ ...current, [field.name]: String(value) }));
      return;
    }

    setMetadata((current) => ({ ...current, [field.name]: value }));
  }

  async function save(saveAsDraft: boolean, showToast = true) {
    if (!providerId) {
      toast.error("Selecione um provedor.");
      return null;
    }

    const providerChanged = Boolean(
      currentChannel.provider && currentChannel.provider !== providerId,
    );
    const confirmed =
      !providerChanged ||
      !currentChannel.is_active ||
      window.confirm(
        "Trocar o provedor desativará o canal atual. Deseja continuar?",
      );

    if (!confirmed) return null;

    const payload: UpdateChannelConfigurationPayload = {
      provider: providerId,
      metadata,
      secrets: Object.fromEntries(
        Object.entries(secrets).filter(
          ([, value]) => String(value).trim() !== "",
        ),
      ),
      sender: String(metadata.sender_email || metadata.sender || ""),
      public_identifier: String(
        metadata.phone_number_id || metadata.account_sid || "",
      ),
      save_as_draft: saveAsDraft,
      confirm_provider_change: providerChanged && currentChannel.is_active,
    };

    try {
      const result = await updateChannel.mutateAsync({
        channel: currentChannel.channel,
        payload,
      });
      setCurrentChannel(result);

      if (showToast) {
        toast.success(
          saveAsDraft
            ? "Configuração salva como rascunho."
            : "Configuração salva. Agora valide a conexão.",
        );
      }

      return result;
    } catch (error) {
      toast.error(humanError(error));
      return null;
    }
  }

  async function handleTestConnection() {
    const saved = await save(false, false);
    if (!saved) return;

    try {
      const result = await testConnection.mutateAsync(currentChannel.channel);
      setCurrentChannel(result);
      toast.success("Conexão validada com sucesso.");
    } catch (error) {
      toast.error(humanError(error));
    }
  }

  async function handleSendTest() {
    const saved = await save(false, false);
    if (!saved) return;

    try {
      const result = await sendTest.mutateAsync({
        channel: currentChannel.channel,
        destination: testDestination || undefined,
      });
      setCurrentChannel(result.channel);
      const manualUrl = result.test.metadata.manual_url;
      setManualTestUrl(manualUrl || null);
      toast.success(
        manualUrl
          ? "Link de teste preparado. O envio continua manual."
          : "Mensagem de teste processada.",
      );
    } catch (error) {
      toast.error(humanError(error));
    }
  }

  async function handleToggle() {
    try {
      const result = await toggleChannel.mutateAsync({
        channel: currentChannel.channel,
        active: !currentChannel.is_active,
      });
      setCurrentChannel(result);
      toast.success(
        currentChannel.is_active ? "Canal desativado." : "Canal ativado.",
      );
    } catch (error) {
      toast.error(humanError(error));
    }
  }

  async function handleRemove() {
    if (
      !window.confirm(
        "Remover esta configuração? As credenciais armazenadas serão apagadas.",
      )
    ) {
      return;
    }

    try {
      await removeChannel.mutateAsync(currentChannel.channel);
      toast.success("Configuração removida.");
      onClose();
    } catch (error) {
      toast.error(humanError(error));
    }
  }

  function renderField(field: ChannelConfigurationField) {
    const configuredSecret =
      field.secret && Boolean(currentChannel.credential_state?.[field.name]);
    const currentValue = field.secret
      ? (secrets[field.name] ?? "")
      : (metadata[field.name] ?? field.default ?? "");
    const commonClass =
      "h-11 w-full rounded-xl border border-input bg-background px-3 text-sm text-foreground outline-none focus:border-primary";

    return (
      <label
        key={field.name}
        className="grid gap-2 text-xs font-semibold text-foreground"
      >
        <span>
          {field.label}
          {field.required && <span className="ml-1 text-danger">*</span>}
        </span>

        {field.kind === "boolean" ? (
          <span className="flex h-11 items-center gap-3 rounded-xl border border-input bg-background px-3">
            <input
              type="checkbox"
              checked={Boolean(currentValue)}
              disabled={field.read_only || pending}
              onChange={(event) => updateField(field, event.target.checked)}
            />
            <span className="font-normal text-muted-foreground">
              {Boolean(currentValue) ? "Ativado" : "Desativado"}
            </span>
          </span>
        ) : field.kind === "textarea" ? (
          <textarea
            className="min-h-28 rounded-xl border border-input bg-background p-3 text-sm font-normal outline-none focus:border-primary"
            value={String(currentValue)}
            disabled={field.read_only || pending}
            placeholder={field.placeholder}
            onChange={(event) => updateField(field, event.target.value)}
          />
        ) : (
          <input
            className={commonClass}
            type={
              field.kind === "number"
                ? "number"
                : field.kind === "password"
                  ? "password"
                  : field.kind === "email"
                    ? "email"
                    : field.kind === "tel"
                      ? "tel"
                      : field.kind === "url"
                        ? "url"
                        : "text"
            }
            value={String(currentValue)}
            disabled={field.read_only || pending}
            placeholder={
              configuredSecret
                ? "Segredo já configurado — deixe vazio para manter"
                : field.placeholder
            }
            onChange={(event) =>
              updateField(
                field,
                field.kind === "number"
                  ? Number(event.target.value)
                  : event.target.value,
              )
            }
          />
        )}

        {configuredSecret && (
          <span className="text-[10px] font-normal text-success">
            Credencial armazenada de forma criptografada.
          </span>
        )}
      </label>
    );
  }

  if (typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-[120] flex justify-end" role="presentation">
      <button
        type="button"
        className="absolute inset-0 bg-black/65 backdrop-blur-[1px]"
        aria-label="Fechar configuração do canal"
        onClick={() => {
          if (!pending) onClose();
        }}
      />

      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="channel-configuration-title"
        className="relative flex h-dvh w-full max-w-3xl flex-col border-l border-border bg-card shadow-2xl"
      >
        <header className="flex items-start justify-between border-b border-border px-5 py-4 sm:px-7">
          <div>
            <p className="text-xs font-bold text-primary">
              Configuração de canal
            </p>
            <h2
              id="channel-configuration-title"
              className="mt-1 text-xl font-bold text-foreground"
            >
              {communicationChannelLabel[currentChannel.channel]}
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Credenciais nunca são retornadas pela API; somente o estado de
              configuração é exibido.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={pending}
            className="rounded-lg p-2 text-muted-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Fechar"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="overflow-x-auto border-b border-border px-5 py-4 sm:px-7">
          <ol className="flex min-w-[650px] items-center gap-2">
            {steps.map((label, index) => (
              <li key={label} className="flex flex-1 items-center gap-2">
                <button
                  type="button"
                  onClick={() => setStep(index)}
                  disabled={pending}
                  className={cn(
                    "grid h-8 w-8 shrink-0 place-items-center rounded-full border text-xs font-bold",
                    step === index
                      ? "border-primary bg-primary text-primary-foreground"
                      : index < step
                        ? "border-success bg-success/10 text-success"
                        : "border-border bg-background text-muted-foreground",
                  )}
                >
                  {index < step ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    index + 1
                  )}
                </button>
                <span
                  className={cn(
                    "text-[10px] font-semibold",
                    step === index
                      ? "text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  {label}
                </span>
                {index < steps.length - 1 && (
                  <span className="h-px flex-1 bg-border" />
                )}
              </li>
            ))}
          </ol>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-5 sm:p-7">
          {step === 0 && (
            <section>
              <h3 className="text-sm font-bold">Selecione o provedor</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Escolha como este canal será conectado ao Elo Terapêutico.
              </p>

              <div className="mt-5 grid gap-3">
                {availableProviders.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => selectProvider(item.id)}
                    disabled={pending}
                    className={cn(
                      "rounded-xl border p-4 text-left transition",
                      providerId === item.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/40",
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-bold">{item.label}</span>
                      {providerId === item.id && (
                        <CheckCircle2 className="h-5 w-5 text-primary" />
                      )}
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                      {item.description}
                    </p>
                  </button>
                ))}

                {availableProviders.length === 0 && (
                  <div className="rounded-xl border border-warning/30 bg-warning/5 p-4 text-xs text-muted-foreground">
                    O catálogo de provedores não foi carregado. Atualize a página
                    e confirme que o backend está na versão mais recente.
                  </div>
                )}
              </div>

              {provider && (
                <div className="mt-5 rounded-xl border border-primary/20 bg-primary/5 p-4 text-xs text-muted-foreground">
                  <ShieldCheck className="mr-2 inline h-4 w-4 text-primary" />
                  {provider.instructions}
                </div>
              )}
            </section>
          )}

          {step === 1 && (
            <section>
              <h3 className="text-sm font-bold">
                Credenciais e identificação técnica
              </h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Segredos vazios preservam o valor armazenado anteriormente.
              </p>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {technicalFields.map(renderField)}
                {credentialFields.map(renderField)}
                {technicalFields.length + credentialFields.length === 0 && (
                  <p className="text-xs text-muted-foreground sm:col-span-2">
                    Este provedor não exige credenciais externas.
                  </p>
                )}
              </div>
            </section>
          )}

          {step === 2 && (
            <section>
              <h3 className="text-sm font-bold">Remetente</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Defina apenas identificadores administrativos e neutros.
              </p>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {senderConfigurationFields.map(renderField)}
                {senderConfigurationFields.length === 0 && (
                  <p className="text-xs text-muted-foreground sm:col-span-2">
                    O remetente é definido automaticamente para este canal.
                  </p>
                )}
              </div>
            </section>
          )}

          {step === 3 && (
            <section>
              <h3 className="text-sm font-bold">Preferências do canal</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                As preferências do paciente e o opt-out continuam sendo
                validados antes de cada envio.
              </p>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {preferenceConfigurationFields.map(renderField)}
                {preferenceConfigurationFields.length === 0 && (
                  <p className="text-xs text-muted-foreground sm:col-span-2">
                    Não há preferências adicionais para este provedor.
                  </p>
                )}
              </div>
            </section>
          )}

          {step === 4 && (
            <section>
              <h3 className="text-sm font-bold">Teste da integração</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Primeiro valide a conexão. Depois envie uma mensagem controlada
                para seu próprio contato ou um destino informado.
              </p>

              <div className="mt-5 rounded-xl border border-border bg-secondary/30 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-bold">Estado atual</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {
                        communicationConnectionStatusLabel[
                          currentChannel.connection_status
                        ]
                      }
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={pending}
                  >
                    {testConnection.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <FlaskConical className="mr-2 h-4 w-4" />
                    )}
                    Testar conexão
                  </Button>
                </div>
              </div>

              <label className="mt-5 grid gap-2 text-xs font-semibold">
                Destino da mensagem de teste
                <input
                  className="h-11 rounded-xl border border-input bg-background px-3 text-sm font-normal"
                  value={testDestination}
                  disabled={pending}
                  onChange={(event) => setTestDestination(event.target.value)}
                  placeholder="Vazio usa seu e-mail ou telefone cadastrado"
                />
              </label>

              <Button
                type="button"
                className="mt-4"
                onClick={handleSendTest}
                disabled={pending}
              >
                {sendTest.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Send className="mr-2 h-4 w-4" />
                )}
                Enviar mensagem de teste
              </Button>

              {manualTestUrl && (
                <a
                  href={manualTestUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 flex items-center gap-2 rounded-xl border border-success/20 bg-success/10 p-4 text-xs font-bold text-success"
                >
                  <ExternalLink className="h-4 w-4" />
                  Abrir WhatsApp para concluir o teste manual
                </a>
              )}

              {currentChannel.last_error && (
                <div className="mt-5 rounded-xl border border-danger/20 bg-danger/5 p-4 text-xs text-danger">
                  <AlertTriangle className="mr-2 inline h-4 w-4" />
                  {currentChannel.last_error.message}
                </div>
              )}
            </section>
          )}

          {step === 5 && (
            <section>
              <h3 className="text-sm font-bold">Ativação</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Somente configurações validadas podem ser ativadas.
              </p>

              <div className="mt-5 grid gap-3 rounded-xl border border-border bg-secondary/30 p-5 text-xs">
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">Provedor</span>
                  <b>{provider?.label || "Não selecionado"}</b>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">Configuração</span>
                  <b>
                    {
                      communicationConnectionStatusLabel[
                        currentChannel.connection_status
                      ]
                    }
                  </b>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">Operação</span>
                  <b>{currentChannel.is_active ? "Ativo" : "Inativo"}</b>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    Última validação
                  </span>
                  <b>
                    {currentChannel.last_validated_at
                      ? new Date(
                          currentChannel.last_validated_at,
                        ).toLocaleString("pt-BR")
                      : "Ainda não validado"}
                  </b>
                </div>
              </div>

              <Button
                type="button"
                className="mt-5"
                onClick={handleToggle}
                disabled={
                  pending ||
                  (!currentChannel.is_active &&
                    currentChannel.connection_status !== "configured")
                }
              >
                <Power className="mr-2 h-4 w-4" />
                {currentChannel.is_active
                  ? "Desativar canal"
                  : "Ativar canal"}
              </Button>
            </section>
          )}
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-4 sm:px-7">
          <div>
            {!["in_app", "whatsapp_manual"].includes(
              currentChannel.channel,
            ) && (
              <Button
                type="button"
                variant="outline"
                className="border-danger/30 text-danger hover:bg-danger/5"
                onClick={handleRemove}
                disabled={pending}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Remover configuração
              </Button>
            )}
          </div>

          <div className="flex flex-wrap justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => save(true)}
              disabled={pending}
            >
              <Save className="mr-2 h-4 w-4" />
              Salvar rascunho
            </Button>

            {step > 0 && (
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep((current) => current - 1)}
                disabled={pending}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Voltar
              </Button>
            )}

            {step < steps.length - 1 ? (
              <Button
                type="button"
                onClick={() => setStep((current) => current + 1)}
                disabled={pending}
              >
                Continuar
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button
                type="button"
                onClick={() => save(false)}
                disabled={pending}
              >
                {updateChannel.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Salvar
              </Button>
            )}
          </div>
        </footer>
      </div>
    </div>,
    document.body,
  );
}
