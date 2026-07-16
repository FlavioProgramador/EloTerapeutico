import { CreditCard, FileText, Loader2, QrCode } from "lucide-react";

import type { CheckoutWizardController } from "../hooks/use-checkout-wizard";
import type { BillingType } from "../types";
import { billingTypeLabels } from "./checkout.constants";
import { CheckoutGatewayNotice } from "./checkout-shared";

export function CheckoutPaymentMethods({
  controller,
}: {
  controller: CheckoutWizardController;
}) {
  return (
    <>
      <div>
        <span className="text-sm font-semibold">Forma de pagamento</span>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {(["PIX", "BOLETO", "CREDIT_CARD"] as BillingType[]).map(
            (item) => {
              const disabled = item === "CREDIT_CARD";
              const Icon =
                item === "PIX"
                  ? QrCode
                  : item === "BOLETO"
                    ? FileText
                    : CreditCard;
              return (
                <button
                  key={item}
                  type="button"
                  disabled={disabled}
                  onClick={() => controller.setBillingType(item)}
                  className={`rounded-2xl border p-4 text-left text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55 ${controller.billingType === item ? "border-primary bg-primary/10 text-primary" : "border-border bg-background hover:bg-muted"}`}
                >
                  <Icon className="mb-2 h-5 w-5" />
                  {billingTypeLabels[item]}
                  {disabled && (
                    <small className="mt-1 block text-xs font-medium text-muted-foreground">
                      Exige checkout/tokenização oficial
                    </small>
                  )}
                </button>
              );
            },
          )}
        </div>
      </div>

      <CheckoutGatewayNotice />
      <button
        type="button"
        onClick={controller.handlePreview}
        disabled={controller.submitting || !controller.cpfCnpj}
        className="inline-flex w-full items-center justify-center rounded-2xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground shadow-sm transition hover:opacity-90 disabled:opacity-60 md:w-auto"
      >
        {controller.submitting && (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        )}
        Revisar contratação
      </button>
    </>
  );
}
