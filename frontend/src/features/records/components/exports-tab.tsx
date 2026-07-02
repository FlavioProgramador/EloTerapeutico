"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FileDown, RefreshCw, Download, Calendar, User, FileText, AlertCircle, Play } from "lucide-react";
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

interface ExportsTabProps {
  patientId: number;
}

export function ExportsTab({ patientId }: ExportsTabProps) {
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState("Completo");
  const [selectedPeriod, setSelectedPeriod] = useState("Todo o período");

  // Query das exportações clínicas no backend
  const { data: exports = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["records", patientId, "exports"],
    queryFn: () => recordWorkspaceService.listExports(patientId),
    enabled: Number.isFinite(patientId) && patientId > 0,
  });

  // Polling controlado das exportações: roda a cada 3 segundos apenas se houver algum job PENDING ou PROCESSING
  useEffect(() => {
    const hasActiveJobs = exports.some(
      (job) => job.status === "PENDING" || job.status === "PROCESSING"
    );

    if (!hasActiveJobs) return;

    const interval = setInterval(() => {
      refetch();
    }, 3000);

    return () => clearInterval(interval);
  }, [exports, refetch]);

  // Mutação para solicitar nova exportação
  const createMutation = useMutation({
    mutationFn: () => recordWorkspaceService.createExport(patientId, selectedType, selectedPeriod),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records", patientId, "exports"] });
      toast.success("Solicitação de exportação criada com sucesso! O arquivo está sendo gerado em segundo plano.");
    },
    onError: (err: any) => {
      toast.error(`Falha ao criar exportação: ${err.response?.data?.detail || err.message}`);
    },
  });

  // Mutação para reprocessar exportação falha
  const retryMutation = useMutation({
    mutationFn: (exportId: number) => recordWorkspaceService.retryExport(exportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records", patientId, "exports"] });
      toast.success("O reprocessamento do arquivo foi iniciado em segundo plano.");
    },
    onError: (err: any) => {
      toast.error(`Falha ao reiniciar processamento: ${err.response?.data?.detail || err.message}`);
    },
  });

  const handleDownload = async (job: any) => {
    try {
      toast.info("Iniciando download do prontuário...");
      await recordWorkspaceService.downloadExport(job.id, job.filename);
      toast.success("Download concluído!");
    } catch (err: any) {
      toast.error(`Erro ao fazer download: ${err.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-500/10 px-2 py-0.5 text-[10px] font-medium text-slate-600 dark:text-slate-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-500" />
            Fila (Pendente)
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-700 dark:text-blue-300">
            <RefreshCw className="h-2.5 w-2.5 animate-spin text-blue-600" />
            Processando
          </span>
        );
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:text-emerald-300">
            Concluído
          </span>
        );
      case "FAILED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-700 dark:text-red-300">
            Falhou
          </span>
        );
      case "EXPIRED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-300">
            Expirado
          </span>
        );
      default:
        return <span className="inline-flex items-center rounded-full bg-slate-500/10 px-2 py-0.5 text-[10px] font-medium text-slate-700 dark:text-slate-300">{status}</span>;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "--";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
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
        <h3 className="text-sm font-semibold text-foreground">Erro ao carregar exportações</h3>
        <p className="text-xs text-muted-foreground mt-1">Não foi possível recuperar o histórico de relatórios gerados.</p>
        <Button size="sm" variant="outline" className="mt-4" onClick={() => refetch()}>
          Tentar novamente
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Painel de Solicitação */}
      <Card className="p-5 border border-emerald-500/10 bg-emerald-500/5/10">
        <div className="flex flex-col gap-4 md:flex-row md:items-end justify-between">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 flex-1 max-w-xl">
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Tipo de Exportação</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-xs ring-offset-background"
              >
                <option value="Completo">Prontuário Completo (Evoluções + Fichas)</option>
                <option value="Apenas Evoluções">Apenas Evoluções Clínicas</option>
                <option value="Apenas Documentos">Apenas Arquivos & Anexos</option>
              </select>
            </div>
            
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Período</label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-xs ring-offset-background"
              >
                <option value="Todo o período">Todo o período clínico</option>
                <option value="Últimos 30 dias">Últimos 30 dias</option>
                <option value="Últimos 90 dias">Últimos 90 dias</option>
                <option value="Ano corrente">Ano corrente</option>
              </select>
            </div>
          </div>

          <Button
            size="sm"
            onClick={() => createMutation.mutate()}
            isLoading={createMutation.isPending}
            leftIcon={<Play className="h-4 w-4" />}
            className="bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            Iniciar Exportação
          </Button>
        </div>
      </Card>

      {/* Histórico de Exportações */}
      <Card className="overflow-hidden">
        {exports.length === 0 ? (
          <div className="py-12">
            <EmptyState
              icon={<FileDown className="h-6 w-6 text-muted-foreground" />}
              title="Nenhuma exportação solicitada"
              description="Você pode gerar relatórios em PDF do prontuário e baixá-los a qualquer momento."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Arquivo</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Solicitado Em</TableHead>
                  <TableHead>Tamanho</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[100px] text-right">Ação</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {exports.map((job: any) => {
                  const dateObj = new Date(job.created_at);
                  const isCompleted = job.status === "COMPLETED";
                  const isFailedOrExpired = job.status === "FAILED" || job.status === "EXPIRED";

                  return (
                    <TableRow key={job.id}>
                      <TableCell className="font-semibold text-foreground max-w-xs truncate">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-emerald-600/70 shrink-0" />
                          <span className="truncate" title={job.filename}>{job.filename}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {job.export_type}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col text-xs text-muted-foreground">
                          <span className="flex items-center gap-1 font-medium text-foreground">
                            <Calendar className="h-3 w-3 text-muted-foreground" />
                            {dateObj.toLocaleDateString("pt-BR")}
                          </span>
                          <span className="flex items-center gap-1 mt-0.5">
                            <User className="h-3 w-3 text-muted-foreground" />
                            {job.created_by_name || "Sistema"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatBytes(job.size_bytes)}
                      </TableCell>
                      <TableCell>{getStatusBadge(job.status)}</TableCell>
                      <TableCell className="text-right">
                        {isCompleted ? (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDownload(job)}
                            className="h-8 w-8 text-emerald-600 hover:bg-emerald-500/10"
                            title="Fazer download do arquivo PDF"
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                        ) : isFailedOrExpired ? (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => retryMutation.mutate(job.id)}
                            isLoading={retryMutation.isPending}
                            className="h-8 w-8 text-amber-600 hover:bg-amber-500/10"
                            title="Tentar reprocessar exportação"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        ) : (
                          <span className="text-xs text-muted-foreground">--</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}
