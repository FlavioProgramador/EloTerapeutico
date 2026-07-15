"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import type { FinancialPaymentMethod, FinancialTransaction } from "@/types";

interface Props {
  transaction: FinancialTransaction | null;
  onClose: () => void;
  onConfirm: (data: {
    id: number;
    paymentMethod?: FinancialPaymentMethod;
    paidAt?: string;
  }) => void;
  isPending?: boolean;
}

export function FinanceiroMarkPaidModal({
  transaction,
  onClose,
  onConfirm,
  isPending,
}: Props) {
  const [paidAt, setPaidAt] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<
    FinancialPaymentMethod | ""
  >("");

  useEffect(() => {
    if (transaction) {
      setPaidAt(new Date().toISOString().slice(0, 10)); // Default: today
      setPaymentMethod(transaction.payment_method || "uninformed");
    }
  }, [transaction]);

  if (!transaction) return null;

  return (
    <Modal isOpen={!!transaction} onClose={onClose} title="Confirmar Pagamento">
      <div className="space-y-4 pt-2">
        <div className="space-y-1.5">
          <label className="text-sm font-semibold">Data do pagamento</label>
          <Input
            type="date"
            value={paidAt}
            onChange={(e) => setPaidAt(e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-semibold">Meio de pagamento</label>
          <select
            value={paymentMethod}
            onChange={(e) =>
              setPaymentMethod(e.target.value as FinancialPaymentMethod)
            }
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="uninformed">Selecionar (opcional)</option>
            <option value="pix">PIX</option>
            <option value="boleto">Boleto</option>
            <option value="credit_card">Cartão de Crédito</option>
            <option value="debit_card">Cartão de Débito</option>
            <option value="bank_transfer">Transferência Bancária</option>
            <option value="cash">Dinheiro</option>
            <option value="payment_link">Link de Pag. (WhatsApp)</option>
            <option value="other">Outro</option>
          </select>
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-2">
        <Button variant="outline" onClick={onClose} disabled={isPending}>
          Cancelar
        </Button>
        <Button
          className="bg-blue-500 hover:bg-blue-600 text-white"
          onClick={() =>
            onConfirm({
              id: transaction.id,
              paymentMethod: (paymentMethod ||
                "uninformed") as FinancialPaymentMethod,
              paidAt,
            })
          }
          isLoading={isPending}
        >
          Confirmar
        </Button>
      </div>
    </Modal>
  );
}
