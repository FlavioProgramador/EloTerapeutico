"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import type { Patient } from "@/types";

import { useCreateTransaction } from "../hooks/use-financeiro";
import {
  transactionSchema,
  type TransactionFormData,
} from "../schemas/transaction.schemas";

interface Props {
  open: boolean;
  mode: "income" | "expense";
  patients: Patient[];
  onClose: () => void;
}

export function FinanceiroTransactionModal({
  open,
  mode,
  patients,
  onClose,
}: Props) {
  const mutation = useCreateTransaction();
  const today = new Date().toISOString().slice(0, 10);
  const form = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      type: mode,
      category: mode === "income" ? "session" : "other",
      amount: "",
      status: "pending",
      due_date: today,
      payment_method: "uninformed",
      payment_date: "",
      payment_link: "",
      description: "",
      notes: "",
    },
  });
  const status = useWatch({ control: form.control, name: "status" });
  const formType = useWatch({ control: form.control, name: "type" });

  useEffect(() => {
    if (open) {
      form.reset({
        type: mode,
        category: mode === "income" ? "session" : "other",
        amount: "",
        status: "pending",
        due_date: today,
        payment_method: "uninformed",
        payment_date: "",
        payment_link: "",
        description: "",
        patient: undefined,
        appointment: undefined,
        notes: "",
      });
    }
  }, [open, mode, today, form]);

  const submit = form.handleSubmit((data) => {
    mutation.mutate(
      {
        ...data,
        amount: Number(data.amount.replace(",", ".")),
        patient: data.patient ? Number(data.patient) : undefined,
        appointment: data.appointment ? Number(data.appointment) : undefined,
        payment_date:
          data.status === "paid" ? data.payment_date || today : undefined,
      },
      { onSuccess: onClose },
    );
  });

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Nova transação"
      description={
        mode === "income"
          ? "Registre uma receita ou cobrança a receber."
          : "Registre uma despesa ou conta a pagar."
      }
    >
      <form className="space-y-4" onSubmit={submit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Valor (R$)"
            inputMode="decimal"
            placeholder="0,00"
            error={form.formState.errors.amount?.message}
            {...form.register("amount")}
          />
          <Input
            label="Data de vencimento"
            type="date"
            error={form.formState.errors.due_date?.message}
            {...form.register("due_date")}
          />
        </div>

        <label className="block space-y-1.5 text-sm font-semibold">
          Tipo
          <select
            className="h-11 w-full rounded-lg border border-input bg-card px-3"
            {...form.register("type")}
          >
            <option value="income">Receita (A receber)</option>
            <option value="expense">Despesa (A pagar)</option>
          </select>
        </label>

        <label className="block space-y-1.5 text-sm font-semibold">
          Categoria
          <select
            className="h-11 w-full rounded-lg border border-input bg-card px-3"
            {...form.register("category")}
          >
            {formType === "income" && (
              <option value="session">Sessão terapêutica</option>
            )}
            {formType === "income" && (
              <option value="subscription">Mensalidade</option>
            )}
            <option value="material">Material</option>
            <option value="other">Outros</option>
          </select>
        </label>

        {formType === "income" && (
          <label className="block space-y-1.5 text-sm font-semibold">
            Paciente (opcional)
            <select
              className="h-11 w-full rounded-lg border border-input bg-card px-3"
              {...form.register("patient")}
            >
              <option value="">Nenhum</option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.full_name}
                </option>
              ))}
            </select>
          </label>
        )}

        <label className="block space-y-1.5 text-sm font-semibold">
          Meio de pagamento
          <select
            className="h-11 w-full rounded-lg border border-input bg-card px-3"
            {...form.register("payment_method")}
          >
            <option value="uninformed">Não informado</option>
            <option value="pix">PIX</option>
            <option value="boleto">Boleto</option>
            <option value="credit_card">Cartão de crédito</option>
            <option value="debit_card">Cartão de débito</option>
            <option value="cash">Dinheiro</option>
            <option value="bank_transfer">Transferência bancária</option>
            <option value="other">Outro</option>
          </select>
        </label>

        <div>
          <Input
            label="Link pagamento (Opcional)"
            placeholder="https://..."
            error={form.formState.errors.payment_link?.message}
            {...form.register("payment_link")}
          />
          <small className="block text-xs text-muted-foreground mt-1">
            Se informado, será incluído na cobrança via WhatsApp em vez dos
            dados bancários.
          </small>
        </div>

        <label className="flex items-center justify-between rounded-lg border border-border p-3 text-sm">
          <span>
            <strong>Marcar como pago</strong>
            <small className="block text-muted-foreground">
              Registra o lançamento como já quitado.
            </small>
          </span>
          <input
            type="checkbox"
            checked={status === "paid"}
            onChange={(event) => {
              form.setValue(
                "status",
                event.target.checked ? "paid" : "pending",
              );
              if (event.target.checked) form.setValue("payment_date", today);
            }}
          />
        </label>

        {status === "paid" && (
          <div>
            <Input
              label="Data do pagamento (Opcional)"
              type="date"
              error={form.formState.errors.payment_date?.message}
              {...form.register("payment_date")}
            />
            <small className="block text-xs text-muted-foreground mt-1">
              Deixe vazio para usar a data de hoje.
            </small>
          </div>
        )}

        <Textarea
          label="Descrição"
          placeholder="Descrição da transação"
          error={form.formState.errors.description?.message}
          {...form.register("description")}
        />

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={mutation.isPending}>
            Criar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
