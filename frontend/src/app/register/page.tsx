"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { setCookie } from "cookies-next";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import {
  Mail,
  Lock,
  User,
  Briefcase,
  FileText,
  ArrowRight,
  ArrowLeft,
  UserPlus,
  Check,
  Eye,
  EyeOff,
} from "lucide-react";
import axios from "axios";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  registerSchema,
  type RegisterFormData,
} from "@/features/auth/schemas/auth.schemas";
import { Brand } from "@/features/landing/brand";

type AccessMode = "TRIAL" | "PAID";

interface RegistrationResponse {
  next: string;
  tokens?: {
    access: string;
    refresh: string;
  };
  user?: {
    role?: string;
  };
}

function registrationSelection(): { plan: string; accessMode: AccessMode } {
  if (typeof window === "undefined") return { plan: "", accessMode: "TRIAL" };
  const params = new URLSearchParams(window.location.search);
  const plan =
    params.get("plan") ||
    params.get("plan_slug") ||
    params.get("plan_price_slug") ||
    params.get("plan_price_id") ||
    "";
  const accessMode = params.get("mode")?.toUpperCase() === "PAID" ? "PAID" : "TRIAL";
  return { plan, accessMode };
}

function loginHrefAfterRegister(nextOverride?: string) {
  if (typeof window === "undefined") return "/login";
  const currentParams = new URLSearchParams(window.location.search);
  const selectedPlan = currentParams.get("plan");
  const next = nextOverride || currentParams.get("next") || "/dashboard";
  const loginParams = new URLSearchParams();

  if (selectedPlan) loginParams.set("plan", selectedPlan);
  if (next.startsWith("/") && !next.startsWith("//")) loginParams.set("next", next);

  return `/login${loginParams.size ? `?${loginParams.toString()}` : ""}`;
}

export default function RegisterPage() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const { plan } = registrationSelection();
    if (!plan) router.replace("/planos?reason=plan_required");
  }, [router]);

  const {
    register,
    handleSubmit,
    trigger,
    formState: { errors },
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur",
    defaultValues: {
      role: "therapist",
    },
  });

  const handleNext = async (event: React.FormEvent) => {
    event.preventDefault();
    const step1Fields: (keyof RegisterFormData)[] = [
      "full_name",
      "email",
      "password",
      "confirm_password",
    ];
    const isValid = await trigger(step1Fields);
    if (isValid) setStep(2);
  };

  const onSubmit = async (data: RegisterFormData) => {
    const { plan, accessMode } = registrationSelection();
    if (!plan) {
      router.replace("/planos?reason=plan_required");
      return;
    }

    setIsLoading(true);
    const payload = {
      email: data.email,
      full_name: data.full_name,
      password: data.password,
      password_confirm: data.confirm_password,
      crp: data.crp,
      specialty: data.specialty,
      plan,
      access_mode: accessMode,
    };

    try {
      const response = await api.post<RegistrationResponse>("auth/register/", payload);

      // Store tokens from registration response to auto-login
      const { tokens, user: userData, next: nextUrl } = response.data;
      if (tokens?.access) {
        setCookie("auth_token", tokens.access, {
          maxAge: 30 * 60,
          path: "/",
          sameSite: "lax",
        });
      }
      if (tokens?.refresh) {
        setCookie("auth_refresh_token", tokens.refresh, {
          maxAge: 7 * 24 * 60 * 60,
          path: "/",
          sameSite: "lax",
        });
      }
      if (userData?.role) {
        setCookie("auth_role", userData.role, {
          maxAge: 7 * 24 * 60 * 60,
          path: "/",
          sameSite: "lax",
        });
      }

      toast.success("Cadastro realizado com sucesso!", {
        description:
          accessMode === "TRIAL"
            ? "Seu teste gratuito de 7 dias foi ativado."
            : "Sua conta foi criada com sucesso.",
      });

      // Redirect directly to the next URL (no need to re-login)
      const destination = nextUrl || "/dashboard";
      router.push(destination);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const responseData = error.response?.data;
        const serverErrors = responseData?.error?.details || responseData;

        if (serverErrors && typeof serverErrors === "object") {
          const fieldMap: Record<string, keyof RegisterFormData> = {
            email: "email",
            full_name: "full_name",
            password: "password",
            password_confirm: "confirm_password",
            crp: "crp",
            crp_number: "crp",
            specialty: "specialty",
          };

          let hasStep1Error = false;
          Object.entries(serverErrors).forEach(([key, value]) => {
            const mappedKey = fieldMap[key];
            if (mappedKey) {
              setError(mappedKey, {
                message: Array.isArray(value) ? String(value[0]) : String(value),
              });
              if (["email", "full_name", "password", "password_confirm"].includes(key)) {
                hasStep1Error = true;
              }
            }
          });

          if (serverErrors.plan) {
            toast.error("Erro ao selecionar plano", {
              description: Array.isArray(serverErrors.plan) ? String(serverErrors.plan[0]) : String(serverErrors.plan),
            });
          } else if (hasStep1Error) {
            setStep(1);
            toast.error("Erro no cadastro", {
              description:
                responseData?.error?.message ||
                "Por favor, corrija os erros e tente novamente.",
            });
          } else {
            toast.error("Erro no cadastro", {
              description:
                responseData?.error?.message ||
                "Por favor, corrija os erros e tente novamente.",
            });
          }
        } else {
          toast.error("Erro no cadastro", {
            description: "Ocorreu um erro ao criar sua conta. Tente novamente.",
          });
        }
      } else {
        toast.error("Erro no cadastro", {
          description: "Ocorreu um erro ao criar sua conta. Tente novamente.",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const loginHref = mounted ? loginHrefAfterRegister() : "/login";
  const accessMode = mounted ? registrationSelection().accessMode : "TRIAL";

  return (
    <div className="min-h-screen flex bg-white font-sans overflow-hidden">
      
      {/* Left Column - Form */}
      <div className="w-full lg:w-[45%] xl:w-[40%] p-8 sm:p-12 md:p-16 flex flex-col justify-center relative z-10 overflow-y-auto">
        
        {/* Back Button */}
        <Link
          href="/"
          className="absolute top-8 left-8 sm:top-12 sm:left-12 inline-flex items-center gap-2 text-sm text-gray-400 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Link>

        <div className="max-w-sm w-full mx-auto space-y-10 relative mt-8">
          
          {/* Header */}
          <div className="flex flex-col gap-6">
            <div className="flex-shrink-0 [&_span]:!text-[#F97316] [&_.grid]:!bg-white [&_.grid]:!border-[#F97316]/30 [&_.grid]:!shadow-none [&_.grid]:!w-14 [&_.grid]:!h-14 [&_svg]:!w-8 [&_svg]:!h-8">
              <Brand />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-[#1A2E26] tracking-tight mb-1">
                {step === 1 ? "Crie sua conta" : "Quase lá!"}
              </h1>
              <p className="text-gray-500 text-sm">
                {step === 1
                  ? (accessMode === "TRIAL" ? "Inicie seu teste gratuito de 7 dias." : "Junte-se ao Elo Terapêutico.")
                  : "Complete seu perfil profissional."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className={`h-1.5 flex-1 rounded-full transition-colors ${step >= 1 ? 'bg-[#F97316]' : 'bg-gray-200'}`} />
            <div className={`h-1.5 flex-1 rounded-full transition-colors ${step >= 2 ? 'bg-[#F97316]' : 'bg-gray-200'}`} />
          </div>

          <form onSubmit={step === 1 ? handleNext : handleSubmit(onSubmit)} className="space-y-8" noValidate>
            
            {step === 1 ? (
              <div className="space-y-6">
                <div className="space-y-2 group">
                  <label htmlFor="register-name" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                    Nome Completo
                  </label>
                  <Input
                    id="register-name"
                    placeholder="Seu nome completo"
                    autoComplete="name"
                    error={errors.full_name?.message}
                    leftIcon={<User className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                    {...register("full_name")}
                    className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                  />
                </div>

                <div className="space-y-2 group">
                  <label htmlFor="register-email" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                    E-mail
                  </label>
                  <Input
                    id="register-email"
                    placeholder="seuemail@exemplo.com"
                    type="email"
                    autoComplete="email"
                    error={errors.email?.message}
                    leftIcon={<Mail className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                    {...register("email")}
                    className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                  />
                </div>

                <div className="space-y-2 group">
                  <label htmlFor="register-password" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                    Senha
                  </label>
                  <div className="relative">
                    <Input
                      id="register-password"
                      placeholder="Mínimo de 8 caracteres"
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      error={errors.password?.message}
                      leftIcon={<Lock className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                      {...register("password")}
                      className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base pr-10 transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#F97316] transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-2 group">
                  <label htmlFor="register-confirm-password" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                    Confirmar Senha
                  </label>
                  <div className="relative">
                    <Input
                      id="register-confirm-password"
                      placeholder="Repita a senha"
                      type={showConfirmPassword ? "text" : "password"}
                      autoComplete="new-password"
                      error={errors.confirm_password?.message}
                      leftIcon={<Lock className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                      {...register("confirm_password")}
                      className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base pr-10 transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#F97316] transition-colors"
                    >
                      {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    id="register-next"
                    type="submit"
                    className="w-auto px-10 py-6 hover:bg-[#EA580C] text-white rounded-full font-bold shadow-none transition-all flex items-center gap-2"
                    style={{ backgroundColor: "#F97316" }}
                  >
                    PRÓXIMA ETAPA <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="space-y-2 group">
                  <label htmlFor="register-crp" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                    Registro Profissional
                  </label>
                  <Input
                    id="register-crp"
                    placeholder="Ex: CRP 06/123456"
                    error={errors.crp?.message}
                    leftIcon={<FileText className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                    {...register("crp")}
                    className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                  />
                </div>

                <div className="space-y-2 group">
                  <label htmlFor="register-specialty" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                    Especialidade Principal
                  </label>
                  <Input
                    id="register-specialty"
                    placeholder="Ex: Psicologia Clínica, TCC"
                    error={errors.specialty?.message}
                    leftIcon={<Briefcase className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                    {...register("specialty")}
                    className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                  />
                </div>

                <div className="flex items-center gap-4 pt-4">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="text-gray-400 hover:text-[#F97316] font-semibold text-sm transition-colors flex items-center gap-1"
                  >
                    <ArrowLeft className="h-4 w-4" /> Voltar
                  </button>
                  <Button
                    id="register-submit"
                    type="submit"
                    className="w-auto px-10 py-6 hover:bg-[#EA580C] text-white rounded-full font-bold shadow-none transition-all flex items-center gap-2"
                    style={{ backgroundColor: "#F97316" }}
                    isLoading={isLoading}
                  >
                    {accessMode === "TRIAL" ? "INICIAR TESTE" : "CRIAR CONTA"}
                  </Button>
                </div>
              </div>
            )}
          </form>

          <div className="pt-8 text-sm text-gray-400 font-medium flex items-center gap-2">
            Já possui uma conta? 
            <Link href={loginHref} className="text-[#A855F7] hover:underline" style={{ color: "#F97316" }}>
              Faça login
            </Link>
          </div>
        </div>
      </div>

      {/* Right Column - Illustration */}
      <div className="hidden lg:block lg:w-[55%] xl:w-[60%] relative bg-white">
        <div className="absolute inset-0 overflow-hidden">
          <img 
            src="/register_illustration.jpg" 
            alt="Ambiente Terapêutico de Cadastro" 
            className="w-full h-full object-cover object-[left_center] scale-[1.05] origin-left"
          />
        </div>
      </div>
      
    </div>
  );
}
