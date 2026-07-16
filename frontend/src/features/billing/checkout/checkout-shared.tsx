import { Check } from "lucide-react";

import type { CheckoutStep } from "../hooks/checkout-controller.types";

export function CheckoutStepIndicator({ step }: { step: CheckoutStep }) {
  return (
    <div className="flex items-center gap-2" aria-label={`Etapa ${step} de 3`}>
      {[1, 2, 3].map((item) => (
        <span
          key={item}
          className={`grid h-8 w-8 place-items-center rounded-full text-xs font-bold ${step >= item ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
        >
          {step > item ? <Check className="h-4 w-4" /> : item}
        </span>
      ))}
    </div>
  );
}

export function CheckoutField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="block space-y-2">
      <span className="text-sm font-semibold">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
        placeholder={placeholder}
      />
    </label>
  );
}

export function CheckoutReviewRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-border bg-muted/30 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <strong className="text-sm text-foreground">{value}</strong>
    </div>
  );
}

export function CheckoutGatewayNotice() {
  return (
    <div className="rounded-2xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm font-semibold text-primary">
      Os pagamentos são processados pelo Asaas. Nenhum dado clínico é enviado ao
      gateway.
    </div>
  );
}

export function CheckoutProtections() {
  return (
    <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <h2 className="text-lg font-bold">Proteções do fluxo</h2>
      <ol className="mt-4 space-y-3 text-sm text-muted-foreground">
        <li>
          1. O backend usa o preço cadastrado, nunca o valor enviado pelo
          navegador.
        </li>
        <li>2. A chave de idempotência evita cobranças duplicadas.</li>
        <li>3. Parcelas são sincronizadas e exibidas individualmente.</li>
        <li>4. Somente o webhook confirmado libera o acesso.</li>
      </ol>
    </div>
  );
}
