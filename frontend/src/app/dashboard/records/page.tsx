"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, ClipboardList, ChevronRight, User } from "lucide-react";
import { useToast } from "@/contexts/toast";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

interface Patient {
  id: number;
  full_name: string;
  formatted_cpf: string;
  phone: string;
  email: string;
  status: "active" | "inactive";
  age: number;
}

export default function RecordsListPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchPatients = async () => {
    setIsLoading(true);
    try {
      const response = await api.get("patients/");
      const data = Array.isArray(response.data) ? response.data : (response.data as any).results || [];
      // Filtra apenas pacientes ativos por padrão para prontuário clínico
      const activePatients = data.filter((p: any) => p.status === "active");
      setPatients(activePatients);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao carregar prontuários",
        description: "Não foi possível buscar a lista de pacientes ativos.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  const filteredPatients = patients.filter((p) =>
    p.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.formatted_cpf?.includes(searchTerm)
  );

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
        <div className="py-20 text-center flex flex-col items-center gap-2">
          <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-muted-foreground animate-pulse">Carregando prontuários...</span>
        </div>
      ) : filteredPatients.length === 0 ? (
        <Card className="border-border/80 bg-card shadow-xs p-12 text-center flex flex-col items-center justify-center gap-3">
          <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground">
            <ClipboardList className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-sm text-foreground">Nenhum prontuário ativo encontrado</h4>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
              Não existem prontuários de pacientes ativos correspondentes à busca. Apenas pacientes em tratamento ativo são listados aqui.
            </p>
          </div>
        </Card>
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
            {filteredPatients.map((p) => (
              <TableRow key={p.id} className="cursor-pointer" onClick={() => router.push(`/dashboard/records/${p.id}`)}>
                <TableCell className="font-medium text-foreground flex items-center gap-2">
                  <User className="h-4.5 w-4.5 text-primary shrink-0" />
                  <span>{p.full_name}</span>
                </TableCell>
                <TableCell className="text-muted-foreground text-xs">{p.formatted_cpf || "---"}</TableCell>
                <TableCell className="text-muted-foreground text-xs">{p.age} anos</TableCell>
                <TableCell className="text-muted-foreground text-xs">{p.phone}</TableCell>
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
