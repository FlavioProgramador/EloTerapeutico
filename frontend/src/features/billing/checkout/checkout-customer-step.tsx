import type { CheckoutWizardController } from "../hooks/use-checkout-wizard";
import { CheckoutCustomerFields } from "./checkout-customer-fields";
import { CheckoutPaymentMethods } from "./checkout-payment-methods";
import { CheckoutPlanOptions } from "./checkout-plan-options";

export function CheckoutCustomerStep({
  controller,
}: {
  controller: CheckoutWizardController;
}) {
  return (
    <div className="mt-8 space-y-7">
      <CheckoutPlanOptions controller={controller} />
      <CheckoutCustomerFields controller={controller} />
      <CheckoutPaymentMethods controller={controller} />
    </div>
  );
}
