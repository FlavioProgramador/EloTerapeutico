"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, ClipboardList, ChevronRight, User } from "lucide-react";

import { Card } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { SkeletonTable } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

import { usePatients } from "@/features/patients/hooks/use-patients";

export default function RecordsListPage() {
  const router = useRouter();
  
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce da busca
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Busca pacientes ativos usando TanStack Query
  const { data: patientsData, isLoading } = usePatients({
    search: debouncedSearch || undefined,
    status: "active", // Prontuário apenas para pacientes ativos
  });

  const activePatients = patientsData?.results || [];

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Prontuários Eletrônicos
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Acesse anamneses, adicione evoluções clínicas e consulte o histórico de sessões
        </p>
      </div>

      {/* Caixa de Busca */}
      <Card className="border-border/80 bg-card shadow-xs p-4">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-muted-foreground/60" />
          <input
            type="text"
            placeholder="Buscar paciente ativo para ver prontuário..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-9 bg-secondary border border-border/60 rounded-md pl-10 pr-4 text-xs transition focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 placeholder:text-muted-foreground/50 text-foreground"
          />
        </div>
      </Card>

      {/* Tabela de Seleção */}
      {isLoading ? (
        <SkeletonTable rows={5} />
      ) : activePatients.length === 0 ? (
        <EmptyState
          title="Nenhum prontuário ativo encontrado"
          description="Não existem prontuários de pacientes ativos correspondentes à busca. Apenas pacientes em tratamento ativo são listados aqui."
          icon={<ClipboardList className="h-6 w-6 text-muted-foreground" />}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Paciente</TableHead>
              <TableHead>CPF</TableHead>
              <TableHead>Idade</TableHead>
              <TableHead>Telefone</TableHead>
              <TableHead className="text-right">Ação</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {activePatients.map((p) => (
              <TableRow key={p.id} className="cursor-pointer" onClick={() => router.push(`/dashboard/records/${p.id}`)}>
                <TableCell className="font-medium text-foreground flex items-center gap-2">
                  <User className="h-4.5 w-4.5 text-primary shrink-0" />
                  <span>{p.full_name}</span>
                </TableCell>
                <TableCell className="text-muted-foreground text-xs">{p.formatted_cpf || "---"}</TableCell>
                <TableCell className="text-muted-foreground text-xs">{p.age ? `${p.age} anos` : "---"}</TableCell>
                <TableCell className="text-muted-foreground text-xs">{p.phone || "---"}</TableCell>
                <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => router.push(`/dashboard/records/${p.id}`)}
                    rightIcon={<ChevronRight className="h-4 w-4" />}
                    className="hover:bg-primary/5 hover:text-primary text-foreground cursor-pointer"
                  >
                    Acessar Prontuário
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
