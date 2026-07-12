"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  Mail,
  Phone,
  ShieldCheck,
  User,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { persistAuthRole, persistAuthTokens } from "@/lib/auth-session";
import { registerSchema, type RegisterFormData } from "@/features/auth/schemas/auth.schemas";
import { listPlans } from "@/features/billing/api";
import type { Plan, PlanPrice } from "@/features/billing/types";
import { Brand } from "@/features/landing/brand";

const SELECTION_KEY = "elo:registration-selection";

type AccessMode = "TRIAL" | "PAID";
type BillingCycle = "MONTHLY" | "YEARLY";
type PaymentMode = "RECURRING" | "ONE_TIME" | "INSTALLMENT";

interface RegistrationSelection {
  plan: string;
  price: string;
  accessMode: AccessMode;
  billingCycle?: BillingCycle;
  paymentMode?: PaymentMode;
}

interface RegistrationResponse {
  next: string;
  tokens?: { access: string; refresh: string };
  user?: { role?: string };
}

function readSelection(): RegistrationSelection {
  if (typeof window === "undefined") {
    return { plan: "", price: "", accessMode: "TRIAL" };
  }
  const params = new URLSearchParams(window.location.search);
  const querySelection: RegistrationSelection = {
    plan: params.get("plan") || params.get("plan_slug") || "",
    price: params.get("price") || params.get("plan_price_slug") || params.get("plan_price_id") || "",
    accessMode: params.get("mode")?.toUpperCase() === "PAID" ? "PAID" : "TRIAL",
    billingCycle: (params.get("billing_cycle") || params.get("interval") || "").toUpperCase() as BillingCycle || undefined,
    paymentMode: (params.get("payment_mode") || "").toUpperCase() as PaymentMode || undefined,
  };
  if (querySelection.plan || querySelection.price) {
    sessionStorage.setItem(SELECTION_KEY, JSON.stringify(querySelection));
    return querySelection;
  }
  try {
    const stored = sessionStorage.getItem(SELECTION_KEY);
    return stored ? JSON.parse(stored) as RegistrationSelection : querySelection;
  } catch {
    return querySelection;
  }
}

function currency(value: string, currencyCode = "BRL") {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currencyCode,
  }).format(Number(value));
}

function findPrice(plans: Plan[], selection: RegistrationSelection): { plan?: Plan; price?: PlanPrice } {
  const selectedPlan = plans.find((plan) => plan.slug === selection.plan)
    || plans.find((plan) => plan.prices.some((price) => String(price.id) === selection.price || price.slug === selection.price));
  if (!selectedPlan) return {};
  const selectedPrice = selectedPlan.prices.find((price) => String(price.id) === selection.price || price.slug === selection.price)
    || selectedPlan.prices.find((price) => {
      const intervalMatches = !selection.billingCycle || price.billing_interval === selection.billingCycle;
      const modeMatches = !selection.paymentMode || price.billing_model === selection.paymentMode;
      return intervalMatches && modeMatches && price.available;
    })
    || selectedPlan.prices.find((price) => price.available);
  return { plan: selectedPlan, price: selectedPrice };
}

export default function RegisterPage() {
  const router = useRouter();
  const [selection, setSelection] = useState<RegistrationSelection>({ plan: "", price: "", accessMode: "TRIAL" });
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    setSelection(readSelection());
    void listPlans().then(setPlans).catch(() => setPlans([]));
  }, []);

  const selected = useMemo(() => findPrice(plans, selection), [plans, selection]);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      role: "therapist",
      terms_accepted: false,
      privacy_accepted: false,
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    const payload = {
      email: data.email,
      full_name: data.full_name,
      phone: data.phone || "",
      password: data.password,
      password_confirm: data.confirm_password,
      crp: data.crp || "",
      specialty: data.specialty || "",
      terms_accepted: data.terms_accepted,
      privacy_accepted: data.privacy_accepted,
      plan: selection.plan || undefined,
      plan_price_slug: selection.price || undefined,
      billing_cycle: selection.billingCycle,
      payment_mode: selection.paymentMode,
      access_mode: selection.accessMode,
    };

    try {
      const response = await api.post<RegistrationResponse>("auth/register/", payload);
      if (response.data.tokens?.access) {
        persistAuthTokens(response.data.tokens.access, response.data.tokens.refresh);
      }
      if (response.data.user?.role) persistAuthRole(response.data.user.role);
      sessionStorage.removeItem(SELECTION_KEY);
      toast.success("Conta criada com sucesso", {
        description: selection.accessMode === "TRIAL" && selection.plan
          ? "Seu teste gratuito de 7 dias foi iniciado."
          : selection.plan
            ? "Agora conclua o pagamento para liberar as ferramentas."
            : "Escolha um plano para continuar.",
      });
      router.replace(response.data.next || "/planos");
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const responseData = error.response?.data;
        const serverErrors = responseData?.error?.details || responseData;
        if (serverErrors && typeof serverErrors === "object") {
          const fieldMap: Record<string, keyof RegisterFormData> = {
            email: "email",
            full_name: "full_name",
            phone: "phone",
            password: "password",
            password_confirm: "confirm_password",
            crp: "crp",
            crp_number: "crp",
            specialty: "specialty",
            terms_accepted: "terms_accepted",
            privacy_accepted: "privacy_accepted",
          };
          for (const [key, value] of Object.entries(serverErrors)) {
            const field = fieldMap[key];
            if (field) {
              setError(field, { message: Array.isArray(value) ? String(value[0]) : String(value) });
            }
          }
        }
        toast.error("Não foi possível criar sua conta", {
          description: responseData?.error?.message || responseData?.detail || "Revise os dados e tente novamente.",
        });
      } else {
        toast.error("Não foi possível criar sua conta");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const loginParams = new URLSearchParams();
  if (selection.plan) loginParams.set("plan", selection.plan);
  if (selection.price) loginParams.set("price", selection.price);
  const loginHref = `/login${loginParams.size ? `?${loginParams.toString()}` : ""}`;

  return (
    <main className="min-h-screen bg-white text-[#1A2E26] lg:grid lg:grid-cols-[minmax(0,1fr)_420px]">
      <section className="relative flex min-h-screen items-center px-6 py-20 sm:px-10 lg:px-16">
        <Link href="/" className="absolute left-6 top-7 inline-flex items-center gap-2 text-sm font-semibold text-gray-500 transition hover:text-[#F97316] sm:left-10">
          <ArrowLeft className="h-4 w-4" /> Voltar para a página inicial
        </Link>

        <div className="mx-auto w-full max-w-xl">
          <Brand />
          <div className="mt-8">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F97316]">Crie sua conta</p>
            <h1 className="mt-3 text-4xl font-extrabold tracking-tight">Comece com segurança e sem surpresas.</h1>
            <p className="mt-3 text-sm leading-6 text-gray-500">A conta é criada primeiro. O acesso às ferramentas só é liberado com assinatura ativa ou teste gratuito válido.</p>
          </div>

          <form className="mt-9 grid gap-5" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Input label="Nome completo" leftIcon={<User className="h-4 w-4" />} error={errors.full_name?.message} autoComplete="name" {...register("full_name")} />
            <div className="grid gap-5 sm:grid-cols-2">
              <Input label="E-mail" type="email" leftIcon={<Mail className="h-4 w-4" />} error={errors.email?.message} autoComplete="email" {...register("email")} />
              <Input label="Telefone" leftIcon={<Phone className="h-4 w-4" />} error={errors.phone?.message} autoComplete="tel" {...register("phone")} />
            </div>
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="relative">
                <Input label="Senha" type={showPassword ? "text" : "password"} error={errors.password?.message} autoComplete="new-password" {...register("password")} />
                <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-9 text-gray-400 hover:text-[#F97316]" aria-label="Mostrar ou ocultar senha">
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="relative">
                <Input label="Confirmar senha" type={showConfirmPassword ? "text" : "password"} error={errors.confirm_password?.message} autoComplete="new-password" {...register("confirm_password")} />
                <button type="button" onClick={() => setShowConfirmPassword((value) => !value)} className="absolute right-3 top-9 text-gray-400 hover:text-[#F97316]" aria-label="Mostrar ou ocultar confirmação de senha">
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Input label="Registro profissional" placeholder="Ex.: 06/123456" error={errors.crp?.message} {...register("crp")} />
              <Input label="Especialidade" placeholder="Ex.: Psicologia clínica" error={errors.specialty?.message} {...register("specialty")} />
            </div>

            <div className="space-y-3 rounded-2xl border border-gray-200 bg-gray-50 p-4 text-sm">
              <label className="flex items-start gap-3">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-[#F97316]" {...register("terms_accepted")} />
                <span>Aceito os <Link href="/termos-de-uso" className="font-bold text-[#F97316] hover:underline">Termos de Uso</Link>.</span>
              </label>
              {errors.terms_accepted && <p className="text-xs text-red-600">{errors.terms_accepted.message}</p>}
              <label className="flex items-start gap-3">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-[#F97316]" {...register("privacy_accepted")} />
                <span>Aceito a <Link href="/politica-de-privacidade" className="font-bold text-[#F97316] hover:underline">Política de Privacidade</Link>.</span>
              </label>
              {errors.privacy_accepted && <p className="text-xs text-red-600">{errors.privacy_accepted.message}</p>}
            </div>

            <Button type="submit" isLoading={isLoading} className="mt-2 h-12 rounded-xl bg-[#F97316] font-bold text-white hover:bg-[#EA580C]">
              {selection.plan ? (selection.accessMode === "TRIAL" ? "Iniciar teste gratuito" : "Criar conta e ir ao checkout") : "Criar conta e escolher plano"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>

          <p className="mt-7 text-sm text-gray-500">Já possui conta? <Link href={loginHref} className="font-bold text-[#F97316] hover:underline">Entrar</Link></p>
        </div>
      </section>

      <aside className="hidden border-l border-gray-100 bg-[#F7FAF8] p-8 lg:flex lg:flex-col lg:justify-center">
        <div className="rounded-3xl border border-[#1A2E26]/10 bg-white p-7 shadow-sm">
          <ShieldCheck className="h-9 w-9 text-[#2F855A]" />
          <h2 className="mt-5 text-xl font-extrabold">Resumo da contratação</h2>
          {selected.plan && selected.price ? (
            <div className="mt-5 space-y-4">
              <div>
                <p className="text-sm text-gray-500">Plano</p>
                <p className="text-lg font-bold">{selected.plan.name}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-gray-50 p-3"><span className="text-gray-500">Ciclo</span><strong className="mt-1 block">{selected.price.billing_interval === "YEARLY" ? "Anual" : "Mensal"}</strong></div>
                <div className="rounded-xl bg-gray-50 p-3"><span className="text-gray-500">Modalidade</span><strong className="mt-1 block">{selected.price.billing_model === "INSTALLMENT" ? "Parcelado" : selected.price.billing_model === "ONE_TIME" ? "À vista" : "Recorrente"}</strong></div>
              </div>
              <div className="rounded-2xl bg-[#FFF7ED] p-4">
                <p className="text-sm text-gray-500">Valor total</p>
                <p className="mt-1 text-2xl font-extrabold text-[#F97316]">{currency(selected.price.total_amount, selected.price.currency)}</p>
                {selected.price.billing_model === "INSTALLMENT" && <p className="mt-1 text-xs text-gray-600">Até {selected.price.max_installments} parcelas, conforme o checkout.</p>}
              </div>
              {selection.accessMode === "TRIAL" && <div className="flex gap-3 rounded-2xl bg-[#ECFDF5] p-4 text-sm text-[#166534]"><CheckCircle2 className="h-5 w-5 shrink-0" /> 7 dias gratuitos. O teste não reinicia ao trocar de plano.</div>}
            </div>
          ) : (
            <div className="mt-5 rounded-2xl bg-gray-50 p-5 text-sm text-gray-600">Nenhum plano selecionado. Sua conta será criada e você será direcionado para comparar os planos.</div>
          )}
          <Link href="/planos" className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-[#F97316] hover:underline">Alterar ou escolher plano <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </aside>
    </main>
  );
}
