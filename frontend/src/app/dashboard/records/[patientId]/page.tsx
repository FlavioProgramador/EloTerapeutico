"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ClipboardList,
  History,
  PlusCircle,
  FileText,
  User,
  AlertTriangle,
  Lock,
  LockOpen,
  Calendar,
  Stethoscope,
  ChevronDown,
  ChevronUp,
  Plus,
  Save,
  MessageSquarePlus,
  ExternalLink,
} from "lucide-react";
import { useToast } from "@/contexts/toast";
import { useAuth } from "@/contexts/auth";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";

interface Patient {
  id: number;
  full_name: string;
  age: number;
  phone: string;
  email: string;
  birth_date: string;
  status: string;
}

interface Anamnesis {
  id?: number;
  chief_complaint: string;
  history: string;
  medications: string;
  family_history: string;
  observations: string;
  created_at?: string;
  updated_at?: string;
  created_by?: {
    id: number;
    full_name: string;
    email: string;
  };
}

interface EvolutionListItem {
  id: number;
  session_date: string;
  cid10: string;
  is_locked: boolean;
  locked_at: string | null;
  is_editable: boolean;
  addenda_count: number;
  created_by_name: string;
  created_at: string;
}

interface Addendum {
  id: number;
  reason: string;
  content: string;
  created_by: {
    id: number;
    full_name: string;
    email: string;
  };
  created_at: string;
}

interface EvolutionDetail extends EvolutionListItem {
  content: string;
  addenda: Addendum[];
  created_by: {
    id: number;
    full_name: string;
    email: string;
  };
}

export default function RecordDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const { toast } = useToast();
  const patientId = params.patientId;

  // Abas: anamnesis | timeline | new-evolution
  const [activeTab, setActiveTab] = useState<"anamnesis" | "timeline" | "new-evolution">("timeline");

  // Dados principais
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loadingPatient, setLoadingPatient] = useState(true);
  const [anamnesis, setAnamnesis] = useState<Anamnesis | null>(null);
  const [loadingAnamnesis, setLoadingAnamnesis] = useState(true);
  const [evolutions, setEvolutions] = useState<EvolutionListItem[]>([]);
  const [loadingEvolutions, setLoadingEvolutions] = useState(true);

  // Evoluções expandidas
  const [expandedEvolutions, setExpandedEvolutions] = useState<Record<number, EvolutionDetail>>({});
  const [loadingDetails, setLoadingDetails] = useState<Record<number, boolean>>({});

  // Anamnese Edição
  const [isEditingAnamnesis, setIsEditingAnamnesis] = useState(false);
  const [anamnesisForm, setAnamnesisForm] = useState<Anamnesis>({
    chief_complaint: "",
    history: "",
    medications: "",
    family_history: "",
    observations: "",
  });
  const [submittingAnamnesis, setSubmittingAnamnesis] = useState(false);

  // Nova Evolução
  const [newEvolutionForm, setNewEvolutionForm] = useState({
    content: "",
    cid10: "",
    session_date: new Date().toISOString().split("T")[0],
  });
  const [submittingEvolution, setSubmittingEvolution] = useState(false);

  // Aditivo
  const [isAddendumModalOpen, setIsAddendumModalOpen] = useState(false);
  const [selectedEvolutionForAddendum, setSelectedEvolutionForAddendum] = useState<number | null>(null);
  const [addendumForm, setAddendumForm] = useState({
    reason: "",
    content: "",
  });
  const [submittingAddendum, setSubmittingAddendum] = useState(false);

  // Edição de Evolução (se não bloqueada)
  const [isEditEvolutionModalOpen, setIsEditEvolutionModalOpen] = useState(false);
  const [selectedEvolutionForEdit, setSelectedEvolutionForEdit] = useState<EvolutionDetail | null>(null);
  const [editEvolutionForm, setEditEvolutionForm] = useState({
    content: "",
    cid10: "",
    session_date: "",
  });
  const [submittingEditEvolution, setSubmittingEditEvolution] = useState(false);

  // Carrega Paciente
  const fetchPatient = async () => {
    setLoadingPatient(true);
    try {
      const response = await api.get<Patient>(`patients/${patientId}/`);
      setPatient(response.data);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao buscar paciente",
        description: "Não foi possível carregar os dados cadastrais do paciente.",
        variant: "destructive",
      });
    } finally {
      setLoadingPatient(false);
    }
  };

  // Carrega Anamnese
  const fetchAnamnesis = async () => {
    setLoadingAnamnesis(true);
    try {
      const response = await api.get<Anamnesis>(`records/patients/${patientId}/anamnesis/`);
      setAnamnesis(response.data);
      setAnamnesisForm(response.data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        setAnamnesis(null);
      } else {
        console.error(error);
        toast({
          title: "Erro ao buscar anamnese",
          description: "Falha ao consultar a ficha de anamnese inicial.",
          variant: "destructive",
        });
      }
    } finally {
      setLoadingAnamnesis(false);
    }
  };

  // Carrega Lista de Evoluções
  const fetchEvolutions = async () => {
    setLoadingEvolutions(true);
    try {
      const response = await api.get<EvolutionListItem[]>(`records/evolutions/?patient=${patientId}`);
      setEvolutions(response.data);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao carregar histórico",
        description: "Não foi possível recuperar a lista de evoluções.",
        variant: "destructive",
      });
    } finally {
      setLoadingEvolutions(false);
    }
  };

  useEffect(() => {
    if (patientId) {
      fetchPatient();
      fetchAnamnesis();
      fetchEvolutions();
    }
  }, [patientId]);

  // Função para expandir e carregar detalhes da evolução
  const toggleEvolution = async (id: number) => {
    if (expandedEvolutions[id]) {
      setExpandedEvolutions((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      return;
    }

    setLoadingDetails((prev) => ({ ...prev, [id]: true }));
    try {
      const response = await api.get<EvolutionDetail>(`records/evolutions/${id}/`);
      setExpandedEvolutions((prev) => ({ ...prev, [id]: response.data }));
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao buscar detalhes da evolução",
        description: "Não foi possível carregar as informações clínicas desta sessão.",
        variant: "destructive",
      });
    } finally {
      setLoadingDetails((prev) => ({ ...prev, [id]: false }));
    }
  };

  // Trata submissão da anamnese (Criar ou Atualizar)
  const handleSaveAnamnesis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!anamnesisForm.chief_complaint.trim()) {
      toast({
        title: "Campo obrigatório",
        description: "A queixa principal é obrigatória para salvar a anamnese.",
        variant: "destructive",
      });
      return;
    }

    setSubmittingAnamnesis(true);
    try {
      if (anamnesis) {
        // PUT para atualizar
        const response = await api.put<Anamnesis>(`records/patients/${patientId}/anamnesis/`, {
          chief_complaint: anamnesisForm.chief_complaint,
          history: anamnesisForm.history,
          medications: anamnesisForm.medications,
          family_history: anamnesisForm.family_history,
          observations: anamnesisForm.observations,
        });
        setAnamnesis(response.data);
        toast({
          title: "Anamnese atualizada",
          description: "A ficha de anamnese foi atualizada com sucesso.",
          variant: "success",
        });
      } else {
        // POST para criar
        const response = await api.post<Anamnesis>(`records/patients/${patientId}/anamnesis/`, {
          chief_complaint: anamnesisForm.chief_complaint,
          history: anamnesisForm.history,
          medications: anamnesisForm.medications,
          family_history: anamnesisForm.family_history,
          observations: anamnesisForm.observations,
        });
        setAnamnesis(response.data);
        toast({
          title: "Anamnese criada",
          description: "A ficha de anamnese inicial foi criada com sucesso.",
          variant: "success",
        });
      }
      setIsEditingAnamnesis(false);
    } catch (error) {
      console.error(error);
      toast({
        title: "Falha ao salvar",
        description: "Não foi possível enviar os dados de anamnese.",
        variant: "destructive",
      });
    } finally {
      setSubmittingAnamnesis(false);
    }
  };

  // Trata criação de evolução
  const handleCreateEvolution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEvolutionForm.content.trim()) {
      toast({
        title: "Campo obrigatório",
        description: "O conteúdo clínico da sessão não pode ficar em branco.",
        variant: "destructive",
      });
      return;
    }

    setSubmittingEvolution(true);
    try {
      await api.post("records/evolutions/", {
        patient: Number(patientId),
        content: newEvolutionForm.content,
        cid10: newEvolutionForm.cid10,
        session_date: newEvolutionForm.session_date,
      });

      toast({
        title: "Evolução registrada!",
        description: "A sessão foi criptografada e salva no prontuário eletrônico.",
        variant: "success",
      });

      // Reseta formulário e atualiza a timeline
      setNewEvolutionForm({
        content: "",
        cid10: "",
        session_date: new Date().toISOString().split("T")[0],
      });
      fetchEvolutions();
      setActiveTab("timeline");
    } catch (error: any) {
      console.error(error);
      const serverError = error.response?.data?.session_date;
      if (serverError) {
        toast({
          title: "Duplicidade de Data",
          description: Array.isArray(serverError) ? serverError[0] : String(serverError),
          variant: "destructive",
        });
      } else {
        toast({
          title: "Erro ao registrar sessão",
          description: "Não foi possível salvar a evolução clínica no servidor.",
          variant: "destructive",
        });
      }
    } finally {
      setSubmittingEvolution(false);
    }
  };

  // Trata adição de aditivo
  const handleAddAddendum = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addendumForm.reason.trim() || !addendumForm.content.trim()) {
      toast({
        title: "Campos obrigatórios",
        description: "O preenchimento de justificativa e conteúdo é obrigatório.",
        variant: "destructive",
      });
      return;
    }

    setSubmittingAddendum(true);
    try {
      const response = await api.post<Addendum>(
        `records/evolutions/${selectedEvolutionForAddendum}/addendum/`,
        addendumForm
      );

      toast({
        title: "Aditivo inserido!",
        description: "O aditivo foi indexado com sucesso no prontuário histórico.",
        variant: "success",
      });

      // Atualiza o cache da evolução expandida
      if (selectedEvolutionForAddendum) {
        const cached = expandedEvolutions[selectedEvolutionForAddendum];
        if (cached) {
          setExpandedEvolutions((prev) => ({
            ...prev,
            [selectedEvolutionForAddendum]: {
              ...cached,
              addenda: [...cached.addenda, response.data],
              addenda_count: cached.addenda_count + 1,
            },
          }));
        }
        // Atualiza na lista geral de evoluções
        setEvolutions((prev) =>
          prev.map((item) =>
            item.id === selectedEvolutionForAddendum
              ? { ...item, addenda_count: item.addenda_count + 1 }
              : item
          )
        );
      }

      setIsAddendumModalOpen(false);
      setAddendumForm({ reason: "", content: "" });
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao salvar aditivo",
        description: "Ocorreu uma falha ao anexar o aditivo clínico.",
        variant: "destructive",
      });
    } finally {
      setSubmittingAddendum(false);
    }
  };

  // Trata edição de evolução ainda livre
  const handleEditEvolution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvolutionForEdit) return;
    if (!editEvolutionForm.content.trim()) {
      toast({
        title: "Conteúdo vazio",
        description: "O conteúdo descritivo da evolução é obrigatório.",
        variant: "destructive",
      });
      return;
    }

    setSubmittingEditEvolution(true);
    try {
      const response = await api.put(
        `records/evolutions/${selectedEvolutionForEdit.id}/`,
        editEvolutionForm
      );

      toast({
        title: "Evolução editada!",
        description: "As alterações da evolução clínica foram gravadas.",
        variant: "success",
      });

      // Atualiza lista e caches
      fetchEvolutions();
      setExpandedEvolutions((prev) => {
        const next = { ...prev };
        if (next[selectedEvolutionForEdit.id]) {
          next[selectedEvolutionForEdit.id] = {
            ...next[selectedEvolutionForEdit.id],
            content: editEvolutionForm.content,
            cid10: editEvolutionForm.cid10,
            session_date: editEvolutionForm.session_date,
          };
        }
        return next;
      });

      setIsEditEvolutionModalOpen(false);
      setSelectedEvolutionForEdit(null);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao editar evolução",
        description: "Não foi possível salvar as alterações da sessão.",
        variant: "destructive",
      });
    } finally {
      setSubmittingEditEvolution(false);
    }
  };

  if (loadingPatient) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-3">
        <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-muted-foreground animate-pulse">Carregando dados do paciente...</span>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <div>
          <h3 className="font-bold text-lg">Paciente não encontrado</h3>
          <p className="text-sm text-muted-foreground mt-1">
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
    <div className="space-y-8">
      {/* Voltar */}
      <button
        onClick={() => router.push("/dashboard/records")}
        className="flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
      >
        <ArrowLeft className="h-4.5 w-4.5" />
        Voltar para a lista de prontuários
      </button>

      {/* Header Ficha Clíncia */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-border/40 pb-6">
        <div className="flex items-start gap-4">
          <div className="h-14 w-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 font-bold text-xl uppercase shrink-0">
            {patient.full_name.charAt(0)}
          </div>
          <div className="space-y-1">
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-3">
              Prontuário Clínico: {patient.full_name}
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span>{patient.age} anos</span>
              <span>•</span>
              <span>CPF: {patient.phone ? patient.phone : "---"}</span>
              <span>•</span>
              <span className="inline-flex px-2.5 py-0.5 rounded-full font-semibold border bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
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
          className="border-border text-foreground"
        >
          Ver Ficha do Paciente
        </Button>
      </div>

      {/* Abas */}
      <div className="flex border-b border-border/40 gap-6">
        <button
          onClick={() => {
            setActiveTab("timeline");
            setIsEditingAnamnesis(false);
          }}
          className={`pb-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === "timeline"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <History className="h-4.5 w-4.5" />
          Histórico de Evoluções ({evolutions.length})
        </button>

        <button
          onClick={() => {
            setActiveTab("anamnesis");
            setIsEditingAnamnesis(false);
          }}
          className={`pb-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === "anamnesis"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileText className="h-4.5 w-4.5" />
          Anamnese
        </button>

        <button
          onClick={() => {
            setActiveTab("new-evolution");
            setIsEditingAnamnesis(false);
          }}
          className={`pb-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === "new-evolution"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <PlusCircle className="h-4.5 w-4.5" />
          Nova Evolução
        </button>
      </div>

      {/* Conteúdo das Abas */}
      <div className="space-y-6">
        {/* ABA: HISTÓRICO DE EVOLUÇÕES */}
        {activeTab === "timeline" && (
          <div className="space-y-6 animate-fade-in">
            {loadingEvolutions ? (
              <div className="py-20 text-center flex flex-col items-center gap-3">
                <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-muted-foreground">Carregando histórico...</span>
              </div>
            ) : evolutions.length === 0 ? (
              <Card className="border-border/30 bg-card/65 backdrop-blur-md p-12 text-center flex flex-col items-center justify-center gap-4">
                <div className="h-12 w-12 rounded-full bg-secondary/50 flex items-center justify-center text-muted-foreground">
                  <ClipboardList className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="font-bold text-base text-foreground">Nenhuma sessão registrada</h4>
                  <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                    Este paciente ainda não possui evoluções registradas. Utilize a aba "Nova Evolução" para registrar a primeira sessão.
                  </p>
                </div>
              </Card>
            ) : (
              <div className="relative border-l-2 border-primary/20 pl-6 ml-4 space-y-6">
                {evolutions.map((ev) => {
                  const isExpanded = !!expandedEvolutions[ev.id];
                  const isLoadingDetailsForThis = !!loadingDetails[ev.id];
                  const details = expandedEvolutions[ev.id];

                  return (
                    <div key={ev.id} className="relative group">
                      {/* Indicador de Timeline */}
                      <div className={`absolute -left-[31px] top-1.5 h-4.5 w-4.5 rounded-full border-2 border-background flex items-center justify-center transition-all ${
                        ev.is_locked ? "bg-slate-400" : "bg-emerald-500 animate-pulse"
                      }`} />

                      <div className="bg-card/75 border border-border/40 hover:border-border/80 rounded-xl transition-all shadow-xs overflow-hidden">
                        {/* Cabeçalho do Card */}
                        <div
                          onClick={() => toggleEvolution(ev.id)}
                          className="p-5 flex items-center justify-between gap-4 cursor-pointer select-none"
                        >
                          <div className="space-y-1.5">
                            <div className="flex flex-wrap items-center gap-3">
                              <span className="text-base font-bold text-foreground">
                                Sessão em {new Date(ev.session_date).toLocaleDateString("pt-BR")}
                              </span>
                              {ev.cid10 && (
                                <span className="inline-flex px-2 py-0.5 rounded-sm bg-secondary text-secondary-foreground text-[10px] font-bold tracking-wider uppercase">
                                  CID: {ev.cid10}
                                </span>
                              )}
                              {ev.is_locked ? (
                                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground font-semibold bg-slate-500/10 px-2 py-0.5 rounded-md border border-slate-500/20">
                                  <Lock className="h-3 w-3" /> Bloqueado (LGPD)
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-xs text-emerald-500 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                                  <LockOpen className="h-3 w-3" /> Editável
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Registrado por {ev.created_by_name} em {new Date(ev.created_at).toLocaleString("pt-BR")}
                            </p>
                          </div>

                          <div className="flex items-center gap-4">
                            {ev.addenda_count > 0 && (
                              <span className="text-xs bg-primary/10 text-primary border border-primary/20 px-2.5 py-1 rounded-md font-semibold">
                                {ev.addenda_count} aditivo{ev.addenda_count > 1 ? "s" : ""}
                              </span>
                            )}
                            {isLoadingDetailsForThis ? (
                              <div className="h-5 w-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                            ) : isExpanded ? (
                              <ChevronUp className="h-5 w-5 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="h-5 w-5 text-muted-foreground" />
                            )}
                          </div>
                        </div>

                        {/* Corpo Expandido */}
                        {isExpanded && details && (
                          <div className="border-t border-border/30 bg-secondary/10 p-5 space-y-6 animate-scale-in">
                            {/* Conteúdo Clínico */}
                            <div className="space-y-2">
                              <h5 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                                <Stethoscope className="h-3.5 w-3.5" />
                                Descrição do Caso Clínico
                              </h5>
                              <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed bg-card p-4 rounded-lg border border-border/20 font-medium">
                                {details.content}
                              </p>
                            </div>

                            {/* Aditivos */}
                            {details.addenda.length > 0 && (
                              <div className="space-y-3">
                                <h5 className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
                                  <History className="h-3.5 w-3.5" />
                                  Histórico de Aditivos e Retificações
                                </h5>
                                <div className="space-y-3">
                                  {details.addenda.map((ad) => (
                                    <div key={ad.id} className="p-3.5 rounded-lg border border-primary/20 bg-primary/5 space-y-2">
                                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                                        <span className="font-bold text-primary">Justificativa: {ad.reason}</span>
                                        <span>
                                          Por {ad.created_by.full_name} • {new Date(ad.created_at).toLocaleString("pt-BR")}
                                        </span>
                                      </div>
                                      <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                                        {ad.content}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Ações da Evolução */}
                            <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-border/20 justify-end">
                              {ev.is_locked ? (
                                <Button
                                  size="sm"
                                  variant="glass"
                                  onClick={() => {
                                    setSelectedEvolutionForAddendum(ev.id);
                                    setIsAddendumModalOpen(true);
                                  }}
                                  leftIcon={<MessageSquarePlus className="h-4 w-4" />}
                                  className="border-primary/20 hover:bg-primary/10 text-primary text-xs font-bold cursor-pointer"
                                >
                                  Inserir Aditivo (LGPD)
                                </Button>
                              ) : (
                                <>
                                  {details.is_editable ? (
                                    <Button
                                      size="sm"
                                      variant="glass"
                                      onClick={() => {
                                        setSelectedEvolutionForEdit(details);
                                        setEditEvolutionForm({
                                          content: details.content,
                                          cid10: details.cid10 || "",
                                          session_date: details.session_date,
                                        });
                                        setIsEditEvolutionModalOpen(true);
                                      }}
                                      className="border-primary/30 hover:bg-primary/10 text-primary text-xs font-bold"
                                    >
                                      Editar Conteúdo
                                    </Button>
                                  ) : (
                                    <p className="text-xs text-muted-foreground italic">
                                      Apenas o terapeuta autor ({details.created_by.full_name}) pode modificar esta evolução.
                                    </p>
                                  )}
                                </>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ABA: ANAMNESE */}
        {activeTab === "anamnesis" && (
          <div className="space-y-6 animate-fade-in">
            {loadingAnamnesis ? (
              <div className="py-20 text-center flex flex-col items-center gap-3">
                <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-muted-foreground animate-pulse">Consultando ficha...</span>
              </div>
            ) : !anamnesis && !isEditingAnamnesis ? (
              <Card className="border-border/30 bg-card/65 backdrop-blur-md p-12 text-center flex flex-col items-center justify-center gap-4">
                <div className="h-12 w-12 rounded-full bg-secondary/50 flex items-center justify-center text-muted-foreground">
                  <FileText className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="font-bold text-base text-foreground">Ficha de Anamnese ausente</h4>
                  <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                    Este paciente ainda não possui a avaliação de anamnese inicial. Crie a ficha para iniciar o histórico do paciente.
                  </p>
                </div>
                <Button
                  size="sm"
                  onClick={() => {
                    setAnamnesisForm({
                      chief_complaint: "",
                      history: "",
                      medications: "",
                      family_history: "",
                      observations: "",
                    });
                    setIsEditingAnamnesis(true);
                  }}
                  leftIcon={<Plus className="h-4.5 w-4.5" />}
                  className="text-white font-semibold"
                >
                  Registrar Anamnese
                </Button>
              </Card>
            ) : isEditingAnamnesis ? (
              <form onSubmit={handleSaveAnamnesis} className="space-y-5">
                <Card className="border-border/30 bg-card/65 backdrop-blur-md">
                  <CardHeader className="pb-3 border-b border-border/40">
                    <CardTitle className="text-lg font-bold">
                      {anamnesis ? "Editar Anamnese" : "Nova Ficha de Anamnese"}
                    </CardTitle>
                    <CardDescription>
                      Todos os dados serão salvos com criptografia AES-128 em conformidade com as regras clínicas da LGPD.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-6 space-y-4 mt-3">
                    <Textarea
                      label="Queixa Principal *"
                      placeholder="Principal motivo, sintomas, dores ou demandas clínicas que trouxeram o paciente..."
                      value={anamnesisForm.chief_complaint}
                      onChange={(e) => setAnamnesisForm({ ...anamnesisForm, chief_complaint: e.target.value })}
                      required
                      className="bg-secondary/20 min-h-[120px]"
                    />

                    <Textarea
                      label="Histórico Clínico"
                      placeholder="Diagnósticos prévios, tratamentos anteriores, histórico médico e hospitalizações..."
                      value={anamnesisForm.history}
                      onChange={(e) => setAnamnesisForm({ ...anamnesisForm, history: e.target.value })}
                      className="bg-secondary/20 min-h-[100px]"
                    />

                    <Textarea
                      label="Medicações em Uso"
                      placeholder="Nome dos remédios, dosagens, frequências e finalidades..."
                      value={anamnesisForm.medications}
                      onChange={(e) => setAnamnesisForm({ ...anamnesisForm, medications: e.target.value })}
                      className="bg-secondary/20 min-h-[80px]"
                    />

                    <Textarea
                      label="Histórico Familiar"
                      placeholder="Doenças psiquiátricas, genéticas ou dinâmicas familiares relevantes..."
                      value={anamnesisForm.family_history}
                      onChange={(e) => setAnamnesisForm({ ...anamnesisForm, family_history: e.target.value })}
                      className="bg-secondary/20 min-h-[80px]"
                    />

                    <Textarea
                      label="Observações Gerais"
                      placeholder="Anotações complementares ou percepções preliminares do terapeuta..."
                      value={anamnesisForm.observations}
                      onChange={(e) => setAnamnesisForm({ ...anamnesisForm, observations: e.target.value })}
                      className="bg-secondary/20 min-h-[80px]"
                    />
                  </CardContent>
                </Card>

                <div className="flex gap-3 justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsEditingAnamnesis(false)}
                    className="border-border text-foreground"
                  >
                    Descartar
                  </Button>
                  <Button
                    type="submit"
                    isLoading={submittingAnamnesis}
                    leftIcon={<Save className="h-4.5 w-4.5" />}
                    className="text-white font-semibold"
                  >
                    Gravar Ficha Clinica
                  </Button>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold text-foreground">Ficha Cadastrada</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Registrada por {anamnesis?.created_by?.full_name} em {anamnesis?.created_at ? new Date(anamnesis.created_at).toLocaleDateString("pt-BR") : ""}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setAnamnesisForm(anamnesis!);
                      setIsEditingAnamnesis(true);
                    }}
                    className="text-white font-semibold"
                  >
                    Editar Anamnese
                  </Button>
                </div>

                <div className="grid grid-cols-1 gap-6">
                  <Card className="border-border/30 bg-card/65 backdrop-blur-md">
                    <CardContent className="p-6 space-y-6">
                      <div className="space-y-1.5">
                        <p className="text-xs font-bold text-primary uppercase tracking-wider">Queixa Principal</p>
                        <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{anamnesis?.chief_complaint}</p>
                      </div>
                      
                      <div className="border-t border-border/20 pt-4 space-y-1.5">
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Histórico Clínico</p>
                        <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{anamnesis?.history || "Nenhum histórico clínico registrado."}</p>
                      </div>

                      <div className="border-t border-border/20 pt-4 space-y-1.5">
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Medicações em Uso</p>
                        <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{anamnesis?.medications || "Nenhuma medicação informada."}</p>
                      </div>

                      <div className="border-t border-border/20 pt-4 space-y-1.5">
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Histórico Familiar</p>
                        <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{anamnesis?.family_history || "Nenhum histórico familiar registrado."}</p>
                      </div>

                      <div className="border-t border-border/20 pt-4 space-y-1.5">
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Observações Gerais</p>
                        <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{anamnesis?.observations || "Nenhuma observação geral registrada."}</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ABA: NOVA EVOLUÇÃO */}
        {activeTab === "new-evolution" && (
          <div className="space-y-6 animate-fade-in">
            <Card className="border-border/30 bg-card/65 backdrop-blur-md">
              <CardHeader className="pb-3 border-b border-border/40">
                <CardTitle className="text-lg font-bold">Registrar Evolução de Sessão</CardTitle>
                <CardDescription>
                  Grave as anotações sobre a sessão do paciente. Estes dados clínicos serão criptografados e não podem ser apagados após registro.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 mt-3">
                <form onSubmit={handleCreateEvolution} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Data da Sessão *"
                      type="date"
                      value={newEvolutionForm.session_date}
                      onChange={(e) => setNewEvolutionForm({ ...newEvolutionForm, session_date: e.target.value })}
                      required
                      className="bg-secondary/20"
                    />

                    <Input
                      label="Código CID-10 (opcional)"
                      placeholder="Ex: F41.1"
                      value={newEvolutionForm.cid10}
                      onChange={(e) => setNewEvolutionForm({ ...newEvolutionForm, cid10: e.target.value })}
                      className="bg-secondary/20"
                    />
                  </div>

                  <Textarea
                    label="Conteúdo Clínico da Sessão *"
                    placeholder="Escreva os detalhes, progresso, técnicas aplicadas e percepções sobre a sessão de hoje..."
                    value={newEvolutionForm.content}
                    onChange={(e) => setNewEvolutionForm({ ...newEvolutionForm, content: e.target.value })}
                    required
                    className="bg-secondary/20 min-h-[220px]"
                  />

                  <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setActiveTab("timeline")}
                      className="border-border text-foreground"
                    >
                      Voltar ao Histórico
                    </Button>
                    <Button
                      type="submit"
                      isLoading={submittingEvolution}
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

      {/* MODAL DE ADITIVO (EVOLUTION ADDENDUM) */}
      <Modal
        isOpen={isAddendumModalOpen}
        onClose={() => {
          setIsAddendumModalOpen(false);
          setAddendumForm({ reason: "", content: "" });
        }}
        title="Inserir Aditivo de Evolução"
        description="Em conformidade com a LGPD e resoluções do CFP, prontuários travados não podem ser alterados diretamente. Você pode adicionar aditivos ou retificações ao final do documento."
        className="max-w-lg"
      >
        <form onSubmit={handleAddAddendum} className="space-y-4">
          <Input
            label="Motivo do Aditivo *"
            placeholder="Ex: Correção de informação, detalhe clínico omitido..."
            value={addendumForm.reason}
            onChange={(e) => setAddendumForm({ ...addendumForm, reason: e.target.value })}
            required
            className="bg-secondary/20"
          />

          <Textarea
            label="Conteúdo do Aditivo *"
            placeholder="Digite o texto adicional do prontuário..."
            value={addendumForm.content}
            onChange={(e) => setAddendumForm({ ...addendumForm, content: e.target.value })}
            required
            className="bg-secondary/20 min-h-[140px]"
          />

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsAddendumModalOpen(false);
                setAddendumForm({ reason: "", content: "" });
              }}
              className="border-border text-foreground"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={submittingAddendum}
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
        <form onSubmit={handleEditEvolution} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Data da Sessão *"
              type="date"
              value={editEvolutionForm.session_date}
              onChange={(e) => setEditEvolutionForm({ ...editEvolutionForm, session_date: e.target.value })}
              required
              className="bg-secondary/20"
            />

            <Input
              label="Código CID-10 (opcional)"
              placeholder="Ex: F41.1"
              value={editEvolutionForm.cid10}
              onChange={(e) => setEditEvolutionForm({ ...editEvolutionForm, cid10: e.target.value })}
              className="bg-secondary/20"
            />
          </div>

          <Textarea
            label="Conteúdo Clínico da Sessão *"
            placeholder="Edite os detalhes da sessão de terapia..."
            value={editEvolutionForm.content}
            onChange={(e) => setEditEvolutionForm({ ...editEvolutionForm, content: e.target.value })}
            required
            className="bg-secondary/20 min-h-[180px]"
          />

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsEditEvolutionModalOpen(false);
                setSelectedEvolutionForEdit(null);
              }}
              className="border-border text-foreground"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={submittingEditEvolution}
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
