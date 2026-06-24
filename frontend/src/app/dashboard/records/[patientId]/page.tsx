"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  ArrowLeft,
  ClipboardList,
  History,
  PlusCircle,
  FileText,
  AlertTriangle,
  Lock,
  LockOpen,
  Stethoscope,
  ChevronDown,
  ChevronUp,
  Plus,
  Save,
  MessageSquarePlus,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";

import { usePatient } from "@/features/patients/hooks/use-patients";
import {
  useRecords,
  useRecord,
  useCreateRecord,
  useUpdateRecord,
  useAnamnesis,
  useSaveAnamnesis,
  useCreateAddendum,
} from "@/features/records/hooks/use-records";
import type { EvolutionListItem, EvolutionDetail, Anamnesis } from "@/types";

// Schemas de Validação locais
const anamnesisSchema = z.object({
  chief_complaint: z.string().min(1, "A queixa principal é obrigatória."),
  history: z.string().optional().or(z.literal("")),
  medications: z.string().optional().or(z.literal("")),
  family_history: z.string().optional().or(z.literal("")),
  observations: z.string().optional().or(z.literal("")),
});
type AnamnesisFormData = z.infer<typeof anamnesisSchema>;

const evolutionSchema = z.object({
  content: z.string().min(1, "O conteúdo clínico da sessão não pode ficar em branco."),
  cid10: z.string().max(10, "CID-10 deve ter no máximo 10 caracteres.").optional().or(z.literal("")),
  session_date: z.string().min(1, "Data da sessão é obrigatória."),
});
type EvolutionFormData = z.infer<typeof evolutionSchema>;

const addendumSchema = z.object({
  reason: z.string().min(1, "O motivo do aditivo é obrigatório."),
  content: z.string().min(1, "O conteúdo do aditivo é obrigatório."),
});
type AddendumFormData = z.infer<typeof addendumSchema>;

export default function RecordDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.patientId);

  // Abas: timeline | anamnesis | new-evolution
  const [activeTab, setActiveTab] = useState<"timeline" | "anamnesis" | "new-evolution">("timeline");

  // Evoluções expandidas
  const [expandedEvolutions, setExpandedEvolutions] = useState<Record<number, boolean>>({});
  const [isEditingAnamnesis, setIsEditingAnamnesis] = useState(false);

  // Modais de Ações
  const [isAddendumModalOpen, setIsAddendumModalOpen] = useState(false);
  const [selectedEvolutionForAddendum, setSelectedEvolutionForAddendum] = useState<number | null>(null);

  const [isEditEvolutionModalOpen, setIsEditEvolutionModalOpen] = useState(false);
  const [selectedEvolutionForEdit, setSelectedEvolutionForEdit] = useState<EvolutionListItem | null>(null);

  // TanStack Query
  const { data: patient, isLoading: loadingPatient } = usePatient(patientId);
  const { data: anamnesis, isLoading: loadingAnamnesis, refetch: refetchAnamnesis } = useAnamnesis(patientId);
  const { data: evolutionsList = [], isLoading: loadingEvolutions, refetch: refetchEvolutions } = useRecords({ patient: patientId });

  const saveAnamnesisMutation = useSaveAnamnesis(patientId);
  const createEvolutionMutation = useCreateRecord();
  const updateEvolutionMutation = useUpdateRecord(selectedEvolutionForEdit?.id || 0);
  const createAddendumMutation = useCreateAddendum(selectedEvolutionForAddendum || 0, patientId);

  // React Hook Form
  const anamnesisForm = useForm<AnamnesisFormData>({
    resolver: zodResolver(anamnesisSchema),
    defaultValues: {
      chief_complaint: "",
      history: "",
      medications: "",
      family_history: "",
      observations: "",
    },
  });

  const newEvolutionForm = useForm<EvolutionFormData>({
    resolver: zodResolver(evolutionSchema),
    defaultValues: {
      content: "",
      cid10: "",
      session_date: new Date().toISOString().split("T")[0],
    },
  });

  const editEvolutionForm = useForm<EvolutionFormData>({
    resolver: zodResolver(evolutionSchema),
    defaultValues: {
      content: "",
      cid10: "",
      session_date: "",
    },
  });

  const addendumForm = useForm<AddendumFormData>({
    resolver: zodResolver(addendumSchema),
    defaultValues: {
      reason: "",
      content: "",
    },
  });

  // Preenche formulário de anamnese quando carrega dados
  useEffect(() => {
    if (anamnesis) {
      anamnesisForm.reset({
        chief_complaint: anamnesis.chief_complaint,
        history: anamnesis.history || "",
        medications: anamnesis.medications || "",
        family_history: anamnesis.family_history || "",
        observations: anamnesis.observations || "",
      });
    }
  }, [anamnesis, anamnesisForm]);

  // Expandir / Ocultar evolução
  const toggleEvolution = (id: number) => {
    setExpandedEvolutions((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // Trata submissão da anamnese
  const handleSaveAnamnesisSubmit = async (data: AnamnesisFormData) => {
    const payload: Anamnesis = {
      ...data,
      chief_complaint: data.chief_complaint,
      history: data.history || "",
      medications: data.medications || "",
      family_history: data.family_history || "",
      observations: data.observations || "",
    };

    saveAnamnesisMutation.mutate(
      { data: payload, exists: !!anamnesis },
      {
        onSuccess: () => {
          setIsEditingAnamnesis(false);
          refetchAnamnesis();
        },
      }
    );
  };

  // Trata criação de evolução
  const handleCreateEvolutionSubmit = async (data: EvolutionFormData) => {
    const payload = {
      patient: patientId,
      content: data.content,
      cid10: data.cid10 || undefined,
      session_date: data.session_date,
    };

    createEvolutionMutation.mutate(payload, {
      onSuccess: () => {
        newEvolutionForm.reset();
        refetchEvolutions();
        setActiveTab("timeline");
      },
    });
  };

  // Trata edição de evolução
  const handleEditEvolutionSubmit = async (data: EvolutionFormData) => {
    if (!selectedEvolutionForEdit) return;

    updateEvolutionMutation.mutate(
      {
        content: data.content,
        cid10: data.cid10 || undefined,
        session_date: data.session_date,
      },
      {
        onSuccess: () => {
          setIsEditEvolutionModalOpen(false);
          setSelectedEvolutionForEdit(null);
          refetchEvolutions();
        },
      }
    );
  };

  // Trata criação de aditivo
  const handleAddAddendumSubmit = async (data: AddendumFormData) => {
    if (!selectedEvolutionForAddendum) return;

    createAddendumMutation.mutate(data, {
      onSuccess: () => {
        setIsAddendumModalOpen(false);
        addendumForm.reset();
        refetchEvolutions();
      },
    });
  };

  if (loadingPatient) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-3">
        <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-muted-foreground animate-pulse">Carregando prontuário...</span>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <div>
          <h3 className="font-bold text-sm text-foreground">Paciente não encontrado</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Não foi possível carregar os prontuários. Verifique a URL ou o status do paciente.
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push("/dashboard/records")}>
          Voltar para Prontuários
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Voltar */}
      <button
        onClick={() => router.push("/dashboard/records")}
        className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
      >
        <ArrowLeft className="h-4 w-4" />
        Voltar para a lista de prontuários
      </button>

      {/* Header Ficha Clínica */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-border/40 pb-6">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold text-lg uppercase shrink-0">
            {patient.full_name.charAt(0)}
          </div>
          <div className="space-y-0.5">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-3">
              Prontuário Clínico: {patient.full_name}
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              {patient.age !== undefined && <span>{patient.age} anos</span>}
              <span>•</span>
              <span>Telefone: {patient.phone || "---"}</span>
              <span>•</span>
              <span className="inline-flex px-2 py-0.5 rounded-sm font-semibold border bg-primary/10 text-primary border-primary/20 text-[10px]">
                Prontuário Ativo
              </span>
            </div>
          </div>
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={() => router.push(`/dashboard/patients/${patient.id}`)}
          rightIcon={<ExternalLink className="h-4 w-4" />}
        >
          Ver Ficha Cadastral
        </Button>
      </div>

      {/* Abas */}
      <div className="flex border-b border-border/40 gap-6">
        <button
          onClick={() => {
            setActiveTab("timeline");
            setIsEditingAnamnesis(false);
          }}
          className={`pb-4 text-xs font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === "timeline"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <History className="h-4 w-4" />
          Histórico de Evoluções ({evolutionsList.length})
        </button>

        <button
          onClick={() => {
            setActiveTab("anamnesis");
            setIsEditingAnamnesis(false);
          }}
          className={`pb-4 text-xs font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === "anamnesis"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileText className="h-4 w-4" />
          Anamnese
        </button>

        <button
          onClick={() => {
            setActiveTab("new-evolution");
            setIsEditingAnamnesis(false);
          }}
          className={`pb-4 text-xs font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === "new-evolution"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <PlusCircle className="h-4 w-4" />
          Nova Evolução
        </button>
      </div>

      {/* Conteúdo das Abas */}
      <div className="space-y-6">
        {/* ABA: HISTÓRICO DE EVOLUÇÕES */}
        {activeTab === "timeline" && (
          <div className="space-y-6">
            {loadingEvolutions ? (
              <div className="py-20 text-center flex flex-col items-center gap-2">
                <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-xs text-muted-foreground">Carregando histórico...</span>
              </div>
            ) : evolutionsList.length === 0 ? (
              <Card className="border-border/80 bg-card shadow-xs p-12 text-center flex flex-col items-center justify-center gap-3">
                <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground">
                  <ClipboardList className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-foreground">Nenhuma sessão registrada</h4>
                  <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                    Este paciente ainda não possui evoluções registradas. Utilize a aba "Nova Evolução" para registrar a primeira sessão.
                  </p>
                </div>
              </Card>
            ) : (
              <div className="relative border-l border-border pl-6 ml-4 space-y-4">
                {evolutionsList.map((ev) => {
                  const isExpanded = !!expandedEvolutions[ev.id];
                  return (
                    <EvolutionCard
                      key={ev.id}
                      evolution={ev}
                      isExpanded={isExpanded}
                      onToggle={() => toggleEvolution(ev.id)}
                      onAddAddendum={() => {
                        setSelectedEvolutionForAddendum(ev.id);
                        addendumForm.reset();
                        setIsAddendumModalOpen(true);
                      }}
                      onEdit={(details) => {
                        setSelectedEvolutionForEdit(ev);
                        editEvolutionForm.reset({
                          content: details.content,
                          cid10: details.cid10 || "",
                          session_date: details.session_date,
                        });
                        setIsEditEvolutionModalOpen(true);
                      }}
                    />
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ABA: ANAMNESE */}
        {activeTab === "anamnesis" && (
          <div className="space-y-6">
            {loadingAnamnesis ? (
              <div className="py-20 text-center flex flex-col items-center gap-2">
                <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-xs text-muted-foreground animate-pulse">Carregando anamnese...</span>
              </div>
            ) : !anamnesis && !isEditingAnamnesis ? (
              <Card className="border-border/80 bg-card shadow-xs p-12 text-center flex flex-col items-center justify-center gap-3">
                <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-foreground">Ficha de Anamnese ausente</h4>
                  <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                    Este paciente ainda não possui a avaliação de anamnese inicial. Crie a ficha para iniciar o histórico do paciente.
                  </p>
                </div>
                <Button
                  size="sm"
                  onClick={() => {
                    anamnesisForm.reset({
                      chief_complaint: "",
                      history: "",
                      medications: "",
                      family_history: "",
                      observations: "",
                    });
                    setIsEditingAnamnesis(true);
                  }}
                  leftIcon={<Plus className="h-4 w-4" />}
                  className="text-white font-semibold"
                >
                  Registrar Anamnese
                </Button>
              </Card>
            ) : isEditingAnamnesis ? (
              <form onSubmit={anamnesisForm.handleSubmit(handleSaveAnamnesisSubmit)} className="space-y-4" noValidate>
                <Card className="border-border/80 bg-card shadow-xs">
                  <CardHeader className="pb-3 border-b border-border/40">
                    <CardTitle className="text-base font-bold text-foreground">
                      {anamnesis ? "Editar Anamnese" : "Nova Ficha de Anamnese"}
                    </CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Todos os dados serão salvos com criptografia ponta a ponta em conformidade com as regras do CFP/LGPD.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-5 space-y-4 mt-2">
                    <div className="space-y-1">
                      <Textarea
                        id="anamnesis-chief-complaint"
                        label="Queixa Principal *"
                        placeholder="Principal motivo, sintomas, demandas clínicas que trouxeram o paciente..."
                        aria-invalid={!!anamnesisForm.formState.errors.chief_complaint}
                        aria-describedby={anamnesisForm.formState.errors.chief_complaint ? "anamnesis-chief-error" : undefined}
                        error={anamnesisForm.formState.errors.chief_complaint?.message}
                        className="min-h-[100px]"
                        {...anamnesisForm.register("chief_complaint")}
                      />
                      {anamnesisForm.formState.errors.chief_complaint && (
                        <p id="anamnesis-chief-error" className="text-xs text-destructive animate-fade-in" role="alert">
                          {anamnesisForm.formState.errors.chief_complaint.message}
                        </p>
                      )}
                    </div>

                    <Textarea
                      id="anamnesis-history"
                      label="Histórico Clínico"
                      placeholder="Diagnósticos prévios, tratamentos anteriores, histórico médico..."
                      error={anamnesisForm.formState.errors.history?.message}
                      className="min-h-[90px]"
                      {...anamnesisForm.register("history")}
                    />

                    <Textarea
                      id="anamnesis-medications"
                      label="Medicações em Uso"
                      placeholder="Nome dos remédios, dosagens, frequências e finalidades..."
                      error={anamnesisForm.formState.errors.medications?.message}
                      className="min-h-[80px]"
                      {...anamnesisForm.register("medications")}
                    />

                    <Textarea
                      id="anamnesis-family"
                      label="Histórico Familiar"
                      placeholder="Doenças psiquiátricas, genéticas ou dinâmicas familiares relevantes..."
                      error={anamnesisForm.formState.errors.family_history?.message}
                      className="min-h-[80px]"
                      {...anamnesisForm.register("family_history")}
                    />

                    <Textarea
                      id="anamnesis-observations"
                      label="Observações Gerais"
                      placeholder="Anotações complementares ou percepções preliminares do terapeuta..."
                      error={anamnesisForm.formState.errors.observations?.message}
                      className="min-h-[80px]"
                      {...anamnesisForm.register("observations")}
                    />
                  </CardContent>
                </Card>

                <div className="flex gap-3 justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsEditingAnamnesis(false)}
                  >
                    Descartar
                  </Button>
                  <Button
                    type="submit"
                    isLoading={saveAnamnesisMutation.isPending}
                    leftIcon={<Save className="h-4 w-4" />}
                    className="text-white font-semibold"
                  >
                    Gravar Ficha Clínica
                  </Button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-base font-bold text-foreground">Ficha Cadastrada</h3>
                    <p className="text-[10px] text-muted-foreground">
                      Registrada por {anamnesis?.created_by?.full_name} em {anamnesis?.created_at ? new Date(anamnesis.created_at).toLocaleDateString("pt-BR") : ""}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setIsEditingAnamnesis(true);
                    }}
                    className="text-white font-semibold"
                  >
                    Editar Anamnese
                  </Button>
                </div>

                <Card className="border-border/80 bg-card shadow-xs">
                  <CardContent className="p-5 space-y-4">
                    <div className="space-y-1">
                      <p className="text-[10px] font-bold text-primary uppercase tracking-wider">Queixa Principal</p>
                      <p className="text-xs text-foreground whitespace-pre-wrap leading-relaxed font-medium">{anamnesis?.chief_complaint}</p>
                    </div>
                    
                    <div className="border-t border-border/40 pt-3 space-y-1">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Histórico Clínico</p>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">{anamnesis?.history || "Nenhum histórico clínico registrado."}</p>
                    </div>

                    <div className="border-t border-border/40 pt-3 space-y-1">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Medicações em Uso</p>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">{anamnesis?.medications || "Nenhuma medicação informada."}</p>
                    </div>

                    <div className="border-t border-border/40 pt-3 space-y-1">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Histórico Familiar</p>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">{anamnesis?.family_history || "Nenhum histórico familiar registrado."}</p>
                    </div>

                    <div className="border-t border-border/40 pt-3 space-y-1">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Observações Gerais</p>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">{anamnesis?.observations || "Nenhuma observação geral registrada."}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}

        {/* ABA: NOVA EVOLUÇÃO */}
        {activeTab === "new-evolution" && (
          <div className="space-y-6">
            <Card className="border-border/80 bg-card shadow-xs">
              <CardHeader className="pb-3 border-b border-border/40">
                <CardTitle className="text-base font-bold text-foreground">Registrar Evolução de Sessão</CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  Grave as anotações sobre a sessão do paciente. Estes dados clínicos serão criptografados e não podem ser apagados após o prazo regulatório.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5 mt-2">
                <form onSubmit={newEvolutionForm.handleSubmit(handleCreateEvolutionSubmit)} className="space-y-4" noValidate>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <Input
                        id="new-session-date"
                        label="Data da Sessão *"
                        type="date"
                        aria-invalid={!!newEvolutionForm.formState.errors.session_date}
                        error={newEvolutionForm.formState.errors.session_date?.message}
                        {...newEvolutionForm.register("session_date")}
                      />
                    </div>

                    <div className="space-y-1">
                      <Input
                        id="new-cid"
                        label="Código CID-10 (opcional)"
                        placeholder="Ex: F41.1"
                        error={newEvolutionForm.formState.errors.cid10?.message}
                        {...newEvolutionForm.register("cid10")}
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Textarea
                      id="new-content"
                      label="Conteúdo Clínico da Sessão *"
                      placeholder="Escreva os detalhes, progresso, técnicas aplicadas e percepções sobre a sessão..."
                      aria-invalid={!!newEvolutionForm.formState.errors.content}
                      error={newEvolutionForm.formState.errors.content?.message}
                      className="min-h-[200px]"
                      {...newEvolutionForm.register("content")}
                    />
                  </div>

                  <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setActiveTab("timeline")}
                    >
                      Voltar ao Histórico
                    </Button>
                    <Button
                      type="submit"
                      isLoading={createEvolutionMutation.isPending}
                      className="text-white font-semibold"
                    >
                      Criptografar e Salvar Evolução
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* MODAL DE ADITIVO */}
      <Modal
        isOpen={isAddendumModalOpen}
        onClose={() => {
          setIsAddendumModalOpen(false);
          addendumForm.reset();
        }}
        title="Inserir Aditivo de Evolução"
        description="Em conformidade com a LGPD e resoluções do CFP, prontuários travados não podem ser alterados diretamente. Você pode adicionar aditivos ou retificações ao final do documento."
        className="max-w-lg"
      >
        <form onSubmit={addendumForm.handleSubmit(handleAddAddendumSubmit)} className="space-y-4" noValidate>
          <div className="space-y-1">
            <Input
              id="addendum-reason"
              label="Motivo do Aditivo *"
              placeholder="Ex: Retificação de informação, detalhe clínico omitido..."
              aria-invalid={!!addendumForm.formState.errors.reason}
              error={addendumForm.formState.errors.reason?.message}
              {...addendumForm.register("reason")}
            />
          </div>

          <div className="space-y-1">
            <Textarea
              id="addendum-content"
              label="Conteúdo do Aditivo *"
              placeholder="Digite o texto adicional do prontuário..."
              aria-invalid={!!addendumForm.formState.errors.content}
              error={addendumForm.formState.errors.content?.message}
              className="min-h-[120px]"
              {...addendumForm.register("content")}
            />
          </div>

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsAddendumModalOpen(false);
                addendumForm.reset();
              }}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={createAddendumMutation.isPending}
              className="text-white font-semibold"
            >
              Confirmar Aditivo
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL DE EDIÇÃO DE EVOLUÇÃO (LIVRE - ANTES DE 48H) */}
      <Modal
        isOpen={isEditEvolutionModalOpen}
        onClose={() => {
          setIsEditEvolutionModalOpen(false);
          setSelectedEvolutionForEdit(null);
        }}
        title="Editar Evolução de Sessão"
        description="Esta evolução ainda não atingiu o limite de 48 horas e está desbloqueada para correções diretas."
        className="max-w-xl"
      >
        <form onSubmit={editEvolutionForm.handleSubmit(handleEditEvolutionSubmit)} className="space-y-4" noValidate>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Input
                id="edit-session-date"
                label="Data da Sessão *"
                type="date"
                aria-invalid={!!editEvolutionForm.formState.errors.session_date}
                error={editEvolutionForm.formState.errors.session_date?.message}
                {...editEvolutionForm.register("session_date")}
              />
            </div>

            <div className="space-y-1">
              <Input
                id="edit-cid"
                label="Código CID-10 (opcional)"
                placeholder="Ex: F41.1"
                error={editEvolutionForm.formState.errors.cid10?.message}
                {...editEvolutionForm.register("cid10")}
              />
            </div>
          </div>

          <div className="space-y-1">
            <Textarea
              id="edit-content"
              label="Conteúdo Clínico da Sessão *"
              placeholder="Edite os detalhes da sessão de terapia..."
              aria-invalid={!!editEvolutionForm.formState.errors.content}
              error={editEvolutionForm.formState.errors.content?.message}
              className="min-h-[160px]"
              {...editEvolutionForm.register("content")}
            />
          </div>

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsEditEvolutionModalOpen(false);
                setSelectedEvolutionForEdit(null);
              }}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={updateEvolutionMutation.isPending}
              className="text-white font-semibold"
            >
              Salvar Alterações
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

// Subcomponente para renderizar cada evolução individual da timeline
interface EvolutionCardProps {
  evolution: EvolutionListItem;
  isExpanded: boolean;
  onToggle: () => void;
  onAddAddendum: () => void;
  onEdit: (details: EvolutionDetail) => void;
}

function EvolutionCard({ evolution, isExpanded, onToggle, onAddAddendum, onEdit }: EvolutionCardProps) {
  // Carrega os detalhes via Query apenas quando expandido
  const { data: details, isLoading } = useRecord(isExpanded ? evolution.id : undefined);

  return (
    <div className="relative group">
      {/* Indicador de Timeline */}
      <div className={`absolute -left-[31px] top-2 h-2.5 w-2.5 rounded-full border border-background transition-colors ${
        evolution.is_locked ? "bg-muted-foreground" : "bg-primary animate-pulse"
      }`} />

      <Card className="border-border/80 bg-card shadow-xs overflow-hidden">
        {/* Cabeçalho do Card */}
        <div
          onClick={onToggle}
          className="p-4 flex items-center justify-between gap-4 cursor-pointer select-none hover:bg-secondary/20 transition-colors"
        >
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                Sessão em {new Date(evolution.session_date).toLocaleDateString("pt-BR")}
              </span>
              {evolution.cid10 && (
                <span className="inline-flex px-1.5 py-0.5 rounded-sm bg-secondary text-muted-foreground text-[9px] font-bold uppercase tracking-wider">
                  CID: {evolution.cid10}
                </span>
              )}
              {evolution.is_locked ? (
                <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground font-semibold bg-secondary px-1.5 py-0.5 rounded-sm border border-border">
                  <Lock className="h-3 w-3" /> Bloqueado
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] text-primary font-semibold bg-primary/10 px-1.5 py-0.5 rounded-sm border border-primary/20">
                  <LockOpen className="h-3 w-3" /> Editável
                </span>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground">
              Registrado por {evolution.created_by_name} • {new Date(evolution.created_at).toLocaleDateString("pt-BR")}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {evolution.addenda_count > 0 && (
              <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-sm font-semibold">
                {evolution.addenda_count} aditivo{evolution.addenda_count > 1 ? "s" : ""}
              </span>
            )}
            {isLoading ? (
              <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            ) : isExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>

        {/* Corpo Expandido */}
        {isExpanded && !isLoading && details && (
          <div className="border-t border-border/60 bg-secondary/10 p-4 space-y-4">
            {/* Conteúdo Clínico */}
            <div className="space-y-1.5">
              <h5 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Stethoscope className="h-3.5 w-3.5" />
                Evolução Clínica da Sessão
              </h5>
              <div className="text-xs text-foreground whitespace-pre-wrap leading-relaxed bg-card p-3 rounded-md border border-border/80 font-medium">
                {details.content}
              </div>
            </div>

            {/* Aditivos */}
            {details.addenda.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-[10px] font-semibold text-primary uppercase tracking-wider flex items-center gap-1.5">
                  <History className="h-3.5 w-3.5" />
                  Histórico de Aditivos e Retificações (LGPD)
                </h5>
                <div className="space-y-2">
                  {details.addenda.map((ad) => (
                    <div key={ad.id} className="p-3 rounded-md border border-border bg-card space-y-1">
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                        <span className="font-semibold text-primary">Justificativa: {ad.reason}</span>
                        <span>
                          Por {ad.created_by.full_name} • {new Date(ad.created_at).toLocaleString("pt-BR")}
                        </span>
                      </div>
                      <p className="text-xs text-foreground whitespace-pre-wrap leading-relaxed">
                        {ad.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Ações da Evolução */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border/40 justify-end">
              {evolution.is_locked ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onAddAddendum}
                  leftIcon={<MessageSquarePlus className="h-3.5 w-3.5" />}
                  className="text-xs font-semibold cursor-pointer"
                >
                  Inserir Aditivo
                </Button>
              ) : (
                <>
                  {details.is_editable ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onEdit(details)}
                      className="text-xs font-semibold"
                    >
                      Editar Conteúdo
                    </Button>
                  ) : (
                    <p className="text-[10px] text-muted-foreground italic">
                      Apenas o terapeuta autor ({details.created_by.full_name}) pode modificar esta evolução.
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
