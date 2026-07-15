"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Download, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { api } from "@/lib/api";
import { QUERY_KEYS } from "@/constants";

interface ImportPreview {
  total: number;
  valid: number;
  duplicates: Array<{ line: number; cpf: string }>;
  errors: Array<{ line: number; errors: Record<string, unknown> }>;
  ready: boolean;
  imported?: number;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function PatientImportModal({ open, onClose }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [loading, setLoading] = useState(false);

  const close = () => {
    setFile(null);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = "";
    onClose();
  };

  const downloadTemplate = () => {
    const content = [
      "full_name,cpf,birth_date,email,phone,gender,status,modality,payer_type",
      "Paciente Exemplo,529.982.247-25,1990-01-15,exemplo@email.com,(21) 99999-9999,N,active,in_person,private",
    ].join("\n");
    const url = URL.createObjectURL(
      new Blob([content], { type: "text/csv;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "modelo-importacao-pacientes.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const send = async (confirm: boolean) => {
    if (!file) return;
    const data = new FormData();
    data.append("file", file);
    data.append("confirm", String(confirm));
    try {
      setLoading(true);
      const response = await api.post<ImportPreview>(
        "patients/import-csv/",
        data,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setPreview(response.data);
      if (confirm && response.data.imported !== undefined) {
        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients });
        await queryClient.invalidateQueries({
          queryKey: ["patients", "dashboard-metrics"],
        });
        toast.success(`${response.data.imported} pacientes importados.`);
        close();
      }
    } catch (error) {
      const message =
        (error as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail || "Não foi possível validar o arquivo.";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={open}
      onClose={close}
      title="Importar pacientes"
      description="Valide o arquivo antes de confirmar. Nenhum registro é criado durante a pré-visualização."
      className="max-w-2xl"
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-dashed border-primary/30 bg-primary/5 p-6 text-center">
          <UploadCloud className="mx-auto h-7 w-7 text-primary" />
          <p className="mt-3 text-sm font-semibold text-foreground">
            Arquivo CSV com até 500 pacientes
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Colunas obrigatórias: full_name, cpf e birth_date.
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setPreview(null);
            }}
          />
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => inputRef.current?.click()}
            >
              Selecionar CSV
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={downloadTemplate}
              leftIcon={<Download className="h-4 w-4" />}
            >
              Baixar modelo
            </Button>
          </div>
          {file && (
            <p className="mt-3 text-xs font-medium text-foreground">
              {file.name}
            </p>
          )}
        </div>

        {preview && (
          <section className="rounded-xl border border-border bg-secondary/25 p-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <strong className="block text-lg text-foreground">
                  {preview.total}
                </strong>
                <span className="text-[10px] text-muted-foreground">
                  Linhas
                </span>
              </div>
              <div>
                <strong className="block text-lg text-primary">
                  {preview.valid}
                </strong>
                <span className="text-[10px] text-muted-foreground">
                  Válidas
                </span>
              </div>
              <div>
                <strong className="block text-lg text-destructive">
                  {preview.errors.length + preview.duplicates.length}
                </strong>
                <span className="text-[10px] text-muted-foreground">
                  Pendências
                </span>
              </div>
            </div>
            {preview.duplicates.length > 0 && (
              <p className="mt-3 text-xs text-destructive">
                CPFs duplicados nas linhas:{" "}
                {preview.duplicates.map((item) => item.line).join(", ")}.
              </p>
            )}
            {preview.errors.length > 0 && (
              <p className="mt-2 text-xs text-destructive">
                Linhas com erro:{" "}
                {preview.errors.map((item) => item.line).join(", ")}.
              </p>
            )}
          </section>
        )}

        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button type="button" variant="ghost" onClick={close}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="outline"
            isLoading={loading && !preview}
            disabled={!file}
            onClick={() => send(false)}
          >
            Validar arquivo
          </Button>
          <Button
            type="button"
            isLoading={loading && Boolean(preview)}
            disabled={!preview?.ready}
            onClick={() => send(true)}
          >
            Confirmar importação
          </Button>
        </div>
      </div>
    </Modal>
  );
}
