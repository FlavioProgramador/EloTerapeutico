"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
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

type AccessMode = "TRIAL" | "PAID";

interface RegistrationResponse {
  next: string;
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
  const router = useRouter();

  useEffect(() => {
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
      toast.success("Cadastro realizado com sucesso!", {
        description:
          accessMode === "TRIAL"
            ? "Seu teste gratuito de 7 dias foi ativado. Faça login para continuar."
            : "Sua conta foi criada. Faça login para concluir a assinatura.",
      });
      router.push(loginHrefAfterRegister(response.data.next));
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

          if (hasStep1Error) setStep(1);

          toast.error("Erro no cadastro", {
            description:
              responseData?.error?.message ||
              "Por favor, corrija os erros e tente novamente.",
          });
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

  const loginHref = loginHrefAfterRegister();
  const accessMode = typeof window === "undefined" ? "TRIAL" : registrationSelection().accessMode;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background text-foreground font-sans">
      <div className="w-full max-w-md space-y-6">
        <Link
          href="/"
          aria-label="Voltar para a página inicial"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Voltar para o início
        </Link>

        <div className="flex flex-col items-center text-center">
          <div className="h-10 w-10 rounded-md bg-primary flex items-center justify-center mb-3">
            <UserPlus className="h-5 w-5 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Elo Terapêutico
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            {accessMode === "TRIAL"
              ? "Teste gratuito de 7 dias no plano selecionado"
              : "Crie sua conta para concluir a assinatura"}
          </p>
        </div>

        <Card className="border-border/80 bg-card shadow-xs">
          <CardHeader className="space-y-2 pb-4">
            <div className="flex items-center justify-center gap-3 mb-2">
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors duration-200 ${
                  step === 1
                    ? "bg-primary text-primary-foreground"
                    : "bg-primary/20 text-primary"
                }`}
              >
                {step > 1 ? <Check className="h-4 w-4" /> : "1"}
              </div>
              <div
                className={`h-[2px] w-12 transition-colors duration-200 ${
                  step > 1 ? "bg-primary/40" : "bg-border"
                }`}
              />
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors duration-200 ${
                  step === 2
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-muted-foreground"
                }`}
              >
                2
              </div>
            </div>

            <CardTitle className="text-xl font-bold text-foreground text-center">
              {step === 1 ? "Dados de Acesso" : "Informações Profissionais"}
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground text-center">
              {step === 1
                ? "Crie sua credencial de acesso segura para a plataforma"
                : "Complete o perfil profissional para iniciar os atendimentos"}
            </CardDescription>
          </CardHeader>

          <CardContent>
            {step === 1 ? (
              <form onSubmit={handleNext} className="space-y-4" noValidate>
                <Input
                  id="register-name"
                  label="Nome Completo"
                  placeholder="Seu nome completo"
                  autoComplete="name"
                  leftIcon={<User className="h-4.5 w-4.5 text-muted-foreground" />}
                  error={errors.full_name?.message}
                  {...register("full_name")}
                />

                <Input
                  id="register-email"
                  label="E-mail profissional"
                  placeholder="seuemail@exemplo.com"
                  type="email"
                  autoComplete="email"
                  leftIcon={<Mail className="h-4.5 w-4.5 text-muted-foreground" />}
                  error={errors.email?.message}
                  {...register("email")}
                />

                <Input
                  id="register-password"
                  label="Senha"
                  placeholder="Mínimo de 8 caracteres"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  leftIcon={<Lock className="h-4.5 w-4.5 text-muted-foreground" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                      className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                    >
                      {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                    </button>
                  }
                  error={errors.password?.message}
                  {...register("password")}
                />

                <Input
                  id="register-confirm-password"
                  label="Confirmar Senha"
                  placeholder="Repita a senha"
                  type={showConfirmPassword ? "text" : "password"}
                  autoComplete="new-password"
                  leftIcon={<Lock className="h-4.5 w-4.5 text-muted-foreground" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      aria-label={showConfirmPassword ? "Ocultar confirmação" : "Mostrar confirmação"}
                      className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                    </button>
                  }
                  error={errors.confirm_password?.message}
                  {...register("confirm_password")}
                />

                <Button
                  id="register-next"
                  type="submit"
                  className="w-full text-white font-semibold mt-6"
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                >
                  Próxima Etapa
                </Button>
              </form>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
                <Input
                  id="register-crp"
                  label="Registro Profissional (CRP / CRM / Registro)"
                  placeholder="Ex: CRP 06/123456"
                  leftIcon={<FileText className="h-4.5 w-4.5 text-muted-foreground" />}
                  error={errors.crp?.message}
                  {...register("crp")}
                />

                <Input
                  id="register-specialty"
                  label="Especialidade Principal"
                  placeholder="Ex: Psicologia Clínica, TCC, Psicanálise"
                  leftIcon={<Briefcase className="h-4.5 w-4.5 text-muted-foreground" />}
                  error={errors.specialty?.message}
                  {...register("specialty")}
                />

                <div className="flex gap-4 mt-6">
                  <Button
                    id="register-back"
                    type="button"
                    variant="outline"
                    className="w-1/3"
                    onClick={() => setStep(1)}
                    leftIcon={<ArrowLeft className="h-4 w-4" />}
                  >
                    Voltar
                  </Button>

                  <Button
                    id="register-submit"
                    type="submit"
                    className="w-2/3 text-white font-semibold"
                    isLoading={isLoading}
                    rightIcon={<UserPlus className="h-4 w-4" />}
                  >
                    {accessMode === "TRIAL" ? "Iniciar teste" : "Criar conta"}
                  </Button>
                </div>
              </form>
            )}

            <div className="mt-5 text-center text-xs text-muted-foreground">
              Já possui uma conta?{" "}
              <Link
                href={loginHref}
                className="text-primary hover:underline font-semibold"
              >
                Faça login
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
