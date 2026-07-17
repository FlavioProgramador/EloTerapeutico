import type { CheckoutWizardController } from "../hooks/use-checkout-wizard";
import {
  formatCheckoutPhone,
  formatCpfCnpj,
  formatCurrency,
} from "./checkout-formatters";
import { CheckoutField } from "./checkout-shared";

export function CheckoutCustomerFields({
  controller,
}: {
  controller: CheckoutWizardController;
}) {
  const price = controller.selectedPrice;
  if (!price) return null;

  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        <CheckoutField
          label="Nome para cobrança"
          value={controller.name}
          onChange={controller.setName}
          placeholder="Seu nome completo"
        />
        <CheckoutField
          label="CPF ou CNPJ"
          value={controller.cpfCnpj}
          onChange={(value) => controller.setCpfCnpj(formatCpfCnpj(value))}
          placeholder="000.000.000-00"
        />
        <CheckoutField
          label="Telefone"
          value={controller.phone}
          onChange={(value) =>
            controller.setPhone(formatCheckoutPhone(value))
          }
          placeholder="(21) 99999-9999"
        />
        <label className="block space-y-2">
          <span className="text-sm font-semibold">Primeiro vencimento</span>
          <input
            type="date"
            value={controller.dueDate}
            onChange={(event) => controller.setDueDate(event.target.value)}
            className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
          />
        </label>
      </div>

      {price.billing_model === "INSTALLMENT" && (
        <label className="block space-y-2">
          <span className="text-sm font-semibold">Quantidade de parcelas</span>
          <select
            value={controller.installmentCount}
            onChange={(event) =>
              controller.setInstallmentCount(Number(event.target.value))
            }
            className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
          >
            {Array.from(
              {
                length:
                  price.max_installments - price.min_installments + 1,
              },
              (_, index) => price.min_installments + index,
            ).map((count) => (
              <option key={count} value={count}>
                {count}x de aproximadamente{" "}
                {formatCurrency(
                  Number(price.total_amount) / count,
                  price.currency,
                )}
              </option>
            ))}
          </select>
        </label>
      )}
    </>
  );
}
