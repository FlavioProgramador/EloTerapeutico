import { useState } from "react";

import { defaultCheckoutDueDate } from "../checkout/checkout-formatters";
import type { BillingType } from "../types";

export function useCheckoutCustomer() {
  const [billingType, setBillingType] = useState<BillingType>("PIX");
  const [dueDate, setDueDate] = useState(defaultCheckoutDueDate);
  const [cpfCnpj, setCpfCnpj] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");

  return {
    billingType,
    setBillingType,
    dueDate,
    setDueDate,
    cpfCnpj,
    setCpfCnpj,
    name,
    setName,
    phone,
    setPhone,
  };
}
