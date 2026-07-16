import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/contexts/auth";
import { createCheckout, listPlans, previewCheckout } from "../api";
import { buildCheckoutPayload } from "../checkout/checkout-payload";
import { extractCheckoutError } from "../checkout/checkout-rules";
import type { BillingInterval, CheckoutPreview } from "../types";
import type { CheckoutStep } from "./checkout-controller.types";
import { useCheckoutCustomer } from "./use-checkout-customer";
import { useCheckoutSelection } from "./use-checkout-selection";

export function useCheckoutWizard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const selectedPlanSlug = searchParams.get("plan") || "profissional";
  const requestedInterval: BillingInterval =
    searchParams.get("interval") === "YEARLY" ? "YEARLY" : "MONTHLY";
  const idempotencyKeyRef = useRef("");

  const plansQuery = useQuery({
    queryKey: ["billing", "plans", "checkout"],
    queryFn: listPlans,
    staleTime: 60_000,
  });
  const selection = useCheckoutSelection(
    plansQuery.data ?? [],
    selectedPlanSlug,
    requestedInterval,
  );
  const customer = useCheckoutCustomer();
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState<CheckoutStep>(1);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [result, setResult] = useState<CheckoutPreview | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(
        `/register?next=/checkout?plan=${encodeURIComponent(selectedPlanSlug)}&interval=${selection.interval}`,
      );
    }
  }, [
    authLoading,
    isAuthenticated,
    router,
    selectedPlanSlug,
    selection.interval,
  ]);

  function getIdempotencyKey() {
    if (!idempotencyKeyRef.current) {
      idempotencyKeyRef.current = globalThis.crypto.randomUUID();
    }
    return idempotencyKeyRef.current;
  }

  function createPayload() {
    return buildCheckoutPayload({
      selectedPrice: selection.selectedPrice,
      billingType: customer.billingType,
      cpfCnpj: customer.cpfCnpj,
      name: customer.name,
      phone: customer.phone,
      dueDate: customer.dueDate,
      installmentCount: selection.installmentCount,
      idempotencyKey: getIdempotencyKey(),
    });
  }

  async function handlePreview() {
    const payload = createPayload();
    if (!payload) return;
    setSubmitting(true);
    setError(null);
    try {
      setPreview(await previewCheckout(payload));
      setStep(2);
    } catch (requestError) {
      setError(extractCheckoutError(requestError));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreate() {
    const payload = createPayload();
    if (!payload) return;
    setSubmitting(true);
    setError(null);
    try {
      setResult(await createCheckout(payload));
      setStep(3);
    } catch (requestError) {
      setError(extractCheckoutError(requestError));
    } finally {
      setSubmitting(false);
    }
  }

  return {
    authLoading,
    isAuthenticated,
    plansQuery,
    ...selection,
    ...customer,
    activePreview: preview || result,
    result,
    step,
    setStep,
    error,
    submitting,
    handlePreview,
    handleCreate,
  };
}

export type CheckoutWizardController = ReturnType<typeof useCheckoutWizard>;
