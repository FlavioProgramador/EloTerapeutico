"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FileSpreadsheet, Eye, Plus, Calendar, User, Search, AlertCircle, X, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { SkeletonTable } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { recordWorkspaceService } from "../services/record-workspace.service";
import { toast } from "sonner";

// Definições de formulários clínicos simulados
const AVAILABLE_FORMS = [
  {
    id: "bai",
    name: "Inventário de Ansiedade Beck (BAI)",
    category: "Avaliação Psicométrica",
    questions: [
      { id: "q1", label: "Dormência ou formigamento" },
      { id: "q2", label: "Sensação de calor" },
      { id: "q3", label: "Tremores nas pernas" },
      { id: "q4", label: "Incapaz de relaxar" },
      { id: "q5", label: "Medo de que aconteça o pior" },
    ],
    options: [
      { value: "0", label: "Não incomodou" },
      { value: "1", label: "Levemente" },
      { value: "2", label: "Moderadamente" },
      { value: "3", label: "Gravemente" },
    ],
  },
  {
    id: "bdi",
    name: "Inventário de Depressão Beck (BDI)",
    category: "Avaliação Psicométrica",
    questions: [
      { id: "q1", label: "Tristeza ou desânimo" },
      { id: "q2", label: "Preocupação com o futuro" },
      { id: "q3", label: "Sentimento de fracasso" },
      { id: "q4", label: "Falta de satisfação nas coisas" },
      { id: "q5", label: "Sentimentos de culpa" },
    ],
    options: [
      { value: "0", label: "Ausente" },
      { value: "1", label: "Leve" },
      { value: "2", label: "Moderado" },
      { value: "3", label: "Grave" },
    ],
  },
];

export function FormsTab({ patientId }: { patientId: number }) {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [fillModalOpen, setFillModalOpen] = useState(false);
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [selectedForm, setSelectedForm] = useState<typeof AVAILABLE_FORMS[0] | null>(null);
  const [selectedResponse, setSelectedResponse] = useState<any | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  // Query das respostas de formulário no backend
  const { data: responses = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["records", patientId, "forms", searchTerm],
    queryFn: () => recordWorkspaceService.listForms(patientId, searchTerm),
    enabled: Number.isFinite(patientId) && patientId > 0,
  });

  // Mutação para enviar nova resposta
  const submitMutation = useMutation({
    mutationFn: (payload: any) => recordWorkspaceService.submitForm(patientId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records", patientId, "forms"] });
      toast.success("Formulário preenchido e salvo com sucesso!");
      setFillModalOpen(false);
      setAnswers({});
      setSelectedForm(null);
    },
    onError: (err: any) => {
      toast.error(`Falha ao salvar formulário: ${err.response?.data?.detail || err.message}`);
    },
  });

  const handleOpenFill = (formId: string) => {
    const form = AVAILABLE_FORMS.find((f) => f.id === formId);
    if (form) {
      setSelectedForm(form);
      const initialAnswers: Record<string, string> = {};
      form.questions.forEach((q) => {
        initialAnswers[q.id] = "0"; // Valor padrão
      });
      setAnswers(initialAnswers);
      setFillModalOpen(true);
    }
  };

  const handleSaveAnswers = () => {
    if (!selectedForm) return;
    
    // Calcula a quantidade de respostas
    const answersCount = Object.keys(answers).length;
    
    const payload = {
      form_name: selectedForm.name,
      category: selectedForm.category,
      sent_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      completed_by: "Paciente (Preenchimento assistido)",
      status: "completed",
      answers_count: answersCount,
      form_snapshot: {
        questions: selectedForm.questions,
        options: selectedForm.options,
      },
      answers: answers,
    };
    
    submitMutation.mutate(payload);
  };

  const handleOpenView = (resp: any) => {
    setSelectedResponse(resp);
    setViewModalOpen(true);
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <SkeletonTable rows={5} />
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="flex flex-col items-center justify-center p-8 text-center">
        <AlertCircle className="h-8 w-8 text-destructive mb-2" />
        <h3 className="text-sm font-semibold text-foreground">Erro ao carregar formulários</h3>
        <p className="text-xs text-muted-foreground mt-1">Não foi possível buscar as respostas clínicas.</p>
        <Button size="sm" variant="outline" className="mt-4" onClick={() => refetch()}>
          Tentar novamente
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Barra de Filtros e Busca */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar formulários..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="h-9 w-full rounded-md border border-input bg-background pl-10 pr-4 text-xs ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        {/* Escolha rápida de Formulário */}
        <div className="flex gap-2">
          {AVAILABLE_FORMS.map((form) => (
            <Button
              key={form.id}
              size="sm"
              variant="outline"
              onClick={() => handleOpenFill(form.id)}
              leftIcon={<Plus className="h-3 w-3" />}
              className="border-emerald-600/20 text-emerald-700 hover:bg-emerald-500/10 text-[10px]"
            >
              {form.id.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      {/* Histórico de Respostas */}
      <Card className="overflow-hidden">
        {responses.length === 0 ? (
          <div className="py-12">
            <EmptyState
              icon={<FileSpreadsheet className="h-6 w-6 text-muted-foreground" />}
              title="Nenhum formulário preenchido"
              description={
                searchTerm
                  ? "Tente buscar com outros termos."
                  : "Nenhum questionário ou formulário clínico foi respondido para este paciente."
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Formulário</TableHead>
                  <TableHead>Categoria</TableHead>
                  <TableHead>Preenchido Em</TableHead>
                  <TableHead>Preenchido Por</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[100px] text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {responses.map((resp: any) => {
                  const dateObj = new Date(resp.completed_at || resp.created_at);
                  return (
                    <TableRow key={resp.id}>
                      <TableCell className="font-semibold text-foreground">
                        {resp.form_name}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {resp.category}
                      </TableCell>
                      <TableCell>
                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                          {dateObj.toLocaleDateString("pt-BR")}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                          <User className="h-3.5 w-3.5 text-muted-foreground" />
                          {resp.completed_by || "Paciente"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:text-emerald-300">
                          Concluído
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleOpenView(resp)}
                          className="h-8 w-8 text-emerald-600 hover:bg-emerald-500/10"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      {/* Modal para Responder Formulário */}
      {fillModalOpen && selectedForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Card className="w-full max-w-lg overflow-hidden shadow-xl animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between border-b border-border bg-emerald-500/5 px-6 py-4">
              <div>
                <h3 className="text-sm font-bold text-foreground">{selectedForm.name}</h3>
                <p className="text-[10px] text-muted-foreground">{selectedForm.category}</p>
              </div>
              <button
                onClick={() => setFillModalOpen(false)}
                className="rounded-full p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="max-h-[60vh] overflow-y-auto p-6 space-y-6">
              {selectedForm.questions.map((q) => (
                <div key={q.id} className="space-y-3">
                  <label className="text-xs font-semibold text-foreground">{q.label}</label>
                  <div className="grid grid-cols-4 gap-2">
                    {selectedForm.options.map((opt) => {
                      const active = answers[q.id] === opt.value;
                      return (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt.value }))}
                          className={`rounded-lg border px-3 py-2 text-[10px] font-medium transition-all ${
                            active
                              ? "border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                              : "border-border hover:bg-accent text-muted-foreground"
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 border-t border-border px-6 py-4 bg-muted/40">
              <Button size="sm" variant="ghost" onClick={() => setFillModalOpen(false)}>
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleSaveAnswers}
                isLoading={submitMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                Salvar Formulário
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Modal para Visualizar Respostas do Formulário */}
      {viewModalOpen && selectedResponse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Card className="w-full max-w-lg overflow-hidden shadow-xl animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between border-b border-border bg-emerald-500/5 px-6 py-4">
              <div>
                <h3 className="text-sm font-bold text-foreground">{selectedResponse.form_name}</h3>
                <p className="text-[10px] text-muted-foreground">Preenchido em {new Date(selectedResponse.completed_at).toLocaleDateString("pt-BR")}</p>
              </div>
              <button
                onClick={() => setViewModalOpen(false)}
                className="rounded-full p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="max-h-[60vh] overflow-y-auto p-6 space-y-4">
              {(() => {
                const snapshot = selectedResponse.form_snapshot || {};
                const questions = snapshot.questions || [];
                const options = snapshot.options || [];
                const respAnswers = selectedResponse.answers || {};

                return questions.map((q: any) => {
                  const val = respAnswers[q.id];
                  const matchedOpt = options.find((o: any) => o.value === val);
                  return (
                    <div key={q.id} className="flex justify-between items-center border-b border-border/40 pb-2">
                      <span className="text-xs text-foreground font-medium">{q.label}</span>
                      <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2.5 py-1 text-[10px] font-bold text-emerald-700 dark:text-emerald-300">
                        <Check className="h-3 w-3" />
                        {matchedOpt ? matchedOpt.label : `Opção ${val}`}
                      </span>
                    </div>
                  );
                });
              })()}
            </div>

            <div className="flex justify-end border-t border-border px-6 py-4 bg-muted/40">
              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white" onClick={() => setViewModalOpen(false)}>
                Fechar
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
