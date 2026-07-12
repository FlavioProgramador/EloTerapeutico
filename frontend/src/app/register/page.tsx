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
  Lock,
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
  const rawBillingCycle = (params.get("billing_cycle") || params.get("interval") || "").toUpperCase();
  const rawPaymentMode = (params.get("payment_mode") || "").toUpperCase();
  const querySelection: RegistrationSelection = {
    plan: params.get("plan") || params.get("plan_slug") || "",
    price: params.get("price") || params.get("plan_price_slug") || params.get("plan_price_id") || "",
    accessMode: params.get("mode")?.toUpperCase() === "PAID" ? "PAID" : "TRIAL",
    billingCycle: rawBillingCycle ? rawBillingCycle as BillingCycle : undefined,
    paymentMode: rawPaymentMode ? rawPaymentMode as PaymentMode : undefined,
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

function registrationSelection(): RegistrationSelection {
  return readSelection();
}

function loginHrefAfterRegister(): string {
  const current = registrationSelection();
  const params = new URLSearchParams();
  if (current.plan) params.set("plan", current.plan);
  if (current.price) params.set("price", current.price);
  return `/login${params.size ? `?${params.toString()}` : ""}`;
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
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setSelection(registrationSelection());
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

  const loginHref = mounted ? loginHrefAfterRegister() : "/login";
  const accessMode = mounted ? registrationSelection().accessMode : "TRIAL";

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
      access_mode: accessMode,
    };

    try {
      const response = await api.post<RegistrationResponse>("auth/register/", payload);
      if (response.data.tokens?.access) {
        persistAuthTokens(response.data.tokens.access, response.data.tokens.refresh);
      }
      if (response.data.user?.role) persistAuthRole(response.data.user.role);
      sessionStorage.removeItem(SELECTION_KEY);
      toast.success("Conta criada com sucesso", {
        description: accessMode === "TRIAL" && selection.plan
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

  return (
    <main className="min-h-screen flex bg-[#F9F9F9] font-sans text-[#1A2E26] overflow-hidden">
      {/* Left Column - Form */}
      <div className="w-full lg:w-[45%] xl:w-[40%] flex flex-col justify-center px-6 sm:px-10 lg:px-16 z-10 bg-[#F9F9F9] overflow-y-auto py-12">


        <div className="mx-auto w-full max-w-xl mt-12 lg:mt-0">
          <div className="inline-block flex-shrink-0 [&_span]:!text-[#F97316] [&_.grid]:!bg-white [&_.grid]:!border-[#F97316]/30 [&_.grid]:!shadow-none [&_.grid]:!w-14 [&_.grid]:!h-14 [&_svg]:!w-8 [&_svg]:!h-8 hover:opacity-80 transition-opacity">
            <Brand />
          </div>
          <div className="mt-8">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F97316]">Crie sua conta</p>
            <h1 className="mt-3 text-4xl font-extrabold tracking-tight text-[#1A2E26]">Comece com segurança e sem surpresas.</h1>
            <p className="mt-3 text-sm leading-6 text-gray-500">A conta é criada primeiro. O acesso às ferramentas só é liberado com assinatura ativa ou teste gratuito válido.</p>
          </div>

          <form className="mt-9 grid gap-5" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="space-y-2 group">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">Nome completo</label>
              <Input type="text" error={errors.full_name?.message} autoComplete="name" leftIcon={<User className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />} {...register("full_name")} className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300" />
            </div>
            
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2 group">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">E-mail</label>
                <Input type="email" error={errors.email?.message} autoComplete="email" leftIcon={<Mail className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />} {...register("email")} className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300" />
              </div>
              <div className="space-y-2 group">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">Telefone</label>
                <Input type="tel" error={errors.phone?.message} autoComplete="tel" leftIcon={<Phone className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />} {...register("phone")} className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300" />
              </div>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2 group">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">Senha</label>
                <div className="relative">
                  <Input type={showPassword ? "text" : "password"} error={errors.password?.message} autoComplete="new-password" leftIcon={<Lock className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />} {...register("password")} className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base pr-10 transition-all duration-300" />
                  <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#F97316] transition-colors"><span className="sr-only">Mostrar ou ocultar senha</span>{showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}</button>
                </div>
              </div>
              <div className="space-y-2 group">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">Confirmar Senha</label>
                <div className="relative">
                  <Input type={showConfirmPassword ? "text" : "password"} error={errors.confirm_password?.message} autoComplete="new-password" leftIcon={<Lock className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />} {...register("confirm_password")} className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base pr-10 transition-all duration-300" />
                  <button type="button" onClick={() => setShowConfirmPassword((value) => !value)} className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#F97316] transition-colors"><span className="sr-only">Mostrar ou ocultar confirmação de senha</span>{showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}</button>
                </div>
              </div>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2 group">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">Registro profissional</label>
                <Input placeholder="Ex.: 06/123456" error={errors.crp?.message} {...register("crp")} className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300" />
              </div>
              <div className="space-y-2 group">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">Especialidade</label>
                <Input placeholder="Ex.: Psicologia clínica" error={errors.specialty?.message} {...register("specialty")} className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300" />
              </div>
            </div>

            <div className="space-y-3 rounded-2xl border border-gray-200 bg-gray-50 p-4 text-sm mt-2">
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-[#F97316] rounded border-gray-300 cursor-pointer" {...register("terms_accepted")} />
                <span className="text-gray-600 font-medium">Aceito os <Link href="/termos-de-uso" className="font-bold text-[#F97316] hover:underline">Termos de Uso</Link>.</span>
              </label>
              {errors.terms_accepted && <p className="text-xs text-red-600 font-medium">{errors.terms_accepted.message}</p>}
              
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-[#F97316] rounded border-gray-300 cursor-pointer" {...register("privacy_accepted")} />
                <span className="text-gray-600 font-medium">Aceito a <Link href="/politica-de-privacidade" className="font-bold text-[#F97316] hover:underline">Política de Privacidade</Link>.</span>
              </label>
              {errors.privacy_accepted && <p className="text-xs text-red-600 font-medium">{errors.privacy_accepted.message}</p>}
            </div>

            <Button type="submit" isLoading={isLoading} className="mt-4 h-12 rounded-full bg-[#F97316] font-bold text-white hover:bg-[#EA580C] shadow-none transition-all">
              {selection.plan ? (accessMode === "TRIAL" ? "Iniciar teste gratuito" : "Criar conta e ir ao checkout") : "Criar conta e escolher plano"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>

          <p className="mt-8 text-sm text-gray-500 font-medium">Já possui conta? <Link href={loginHref} className="font-bold text-[#F97316] hover:underline">Entrar</Link></p>
        </div>
      </div>

      {/* Right Column - Illustration & Floating Summary */}
      <aside className="hidden lg:block lg:w-[55%] xl:w-[60%] relative bg-[#F9F9F9] overflow-hidden">
        {/* Background Illustration */}
        <div className="absolute inset-0">
          <img 
            src="/register_illustration.jpg" 
            alt="Ambiente Terapêutico" 
            className="w-full h-full object-cover object-[left_center] scale-[1.05] origin-left"
          />
        </div>

        {/* Floating Resumo da Contratação (Glassmorphism) */}
        <div className="absolute bottom-8 right-8 z-10 w-96 rounded-3xl border border-white/40 bg-white/60 backdrop-blur-xl p-7 shadow-2xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#2F855A]/10">
              <ShieldCheck className="h-6 w-6 text-[#2F855A]" />
            </div>
            <h2 className="text-lg font-extrabold text-gray-900">Resumo da contratação</h2>
          </div>
          
          {selected.plan && selected.price ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Plano Selecionado</p>
                <p className="text-xl font-extrabold text-gray-900">{selected.plan.name}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-white/50 p-3 border border-white/30">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Ciclo</span>
                  <strong className="mt-1 block text-gray-900">{selected.price.billing_interval === "YEARLY" ? "Anual" : "Mensal"}</strong>
                </div>
                <div className="rounded-xl bg-white/50 p-3 border border-white/30">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Modalidade</span>
                  <strong className="mt-1 block text-gray-900">{selected.price.billing_model === "INSTALLMENT" ? "Parcelado" : selected.price.billing_model === "ONE_TIME" ? "À vista" : "Recorrente"}</strong>
                </div>
              </div>
              <div className="rounded-2xl bg-[#F97316]/10 p-4 border border-[#F97316]/20">
                <p className="text-xs font-bold uppercase tracking-wider text-[#F97316]">Valor total</p>
                <p className="mt-1 text-3xl font-extrabold text-[#F97316]">{currency(selected.price.total_amount, selected.price.currency)}</p>
                {selected.price.billing_model === "INSTALLMENT" && <p className="mt-1 text-xs text-[#F97316]/70">Até {selected.price.max_installments} parcelas, conforme o checkout.</p>}
              </div>
              {accessMode === "TRIAL" && (
                <div className="flex items-center gap-3 rounded-2xl bg-[#ECFDF5]/80 p-3 text-sm text-[#166534] border border-[#2F855A]/20">
                  <CheckCircle2 className="h-5 w-5 shrink-0" />
                  <span className="font-medium leading-tight">7 dias gratuitos incluídos.</span>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-2xl bg-white/50 p-5 text-sm text-gray-600 border border-white/30 font-medium">
              Nenhum plano selecionado. Sua conta será criada e você será direcionado para comparar os planos disponíveis.
            </div>
          )}
          <Link href="/planos" className="mt-5 flex items-center justify-center gap-2 text-sm font-bold text-[#F97316] hover:text-[#EA580C] hover:underline transition-colors w-full rounded-xl p-2 hover:bg-[#F97316]/5">
            Alterar ou escolher plano <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </aside>
    </main>
  );
}
