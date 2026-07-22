"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Eye, EyeOff, Lock, Mail } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/auth";
import {
  loginSchema,
  type LoginFormData,
} from "@/features/auth/schemas/auth.schemas";
import { Brand } from "@/features/landing/brand";
import { getPublicErrorMessage } from "@/lib/errors/public-error";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login({ email: data.email, password: data.password });
      toast.success("Login realizado com sucesso.");
    } catch (error: unknown) {
      toast.error("Falha na autenticação", {
        description: getPublicErrorMessage(
          error,
          "Verifique suas credenciais e tente novamente.",
        ),
      });
    }
  };

  return (
    <main 
      className="flex min-h-screen overflow-hidden bg-[#f9f9f9] font-sans text-[#1a1a1a]"
      style={{
        "--color-background": "hsl(0 0% 98%)",
        "--color-foreground": "hsl(0 0% 10%)",
        "--color-card": "hsl(0 0% 100%)",
        "--color-card-foreground": "hsl(0 0% 10%)",
        "--color-border": "hsl(220 13% 91%)",
        "--color-input": "hsl(220 13% 91%)",
        "--color-text-primary": "hsl(0 0% 10%)",
        "--color-text-muted": "hsl(0 0% 40%)",
        "--color-muted": "hsl(0 0% 96%)",
        "--color-muted-foreground": "hsl(0 0% 40%)",
        "--color-primary": "hsl(31 67% 50%)",
        "--color-primary-hover": "hsl(31 67% 43%)",
        "--color-primary-active": "hsl(31 67% 38%)",
        "--color-primary-soft": "hsl(31 67% 95%)",
        "--color-primary-foreground": "hsl(0 0% 100%)",
        "--color-danger": "hsl(15 59% 45%)",
      } as React.CSSProperties}
    >
      <section className="relative z-10 flex w-full flex-col justify-center overflow-y-auto bg-[#f9f9f9] p-6 sm:p-10 lg:w-[45%] lg:p-14 xl:w-[40%] xl:p-20">
        <div
          className="pointer-events-none absolute -left-24 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-primary/8 blur-3xl"
          aria-hidden="true"
        />
        <Link
          href="/"
          className="absolute left-6 top-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-primary sm:left-10 sm:top-10"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Voltar
        </Link>

        <div className="relative mx-auto mt-12 w-full max-w-sm space-y-8">
          <div className="space-y-5">
            <Brand />
            <div>
              <span className="mb-3 inline-flex rounded-full border border-primary/20 bg-primary-soft px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-primary">
                Área do profissional
              </span>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                Bem-vindo de volta
              </h1>
              <p className="mt-1 max-w-xl text-xs leading-5 text-slate-600">
                Acesse sua conta para gerenciar seus atendimentos com segurança.
              </p>
            </div>
          </div>

          <form
            onSubmit={handleSubmit(onSubmit)}
            className="grid gap-4 mt-6"
            noValidate
          >
            <Input
              id="login-email"
              label="E-mail"
              placeholder="seuemail@exemplo.com"
              type="email"
              autoComplete="email"
              variant="underline"
              error={errors.email?.message}
              leftIcon={
                <Mail className="h-5 w-5" aria-hidden="true" />
              }
              {...register("email")}
            />

            <div className="grid gap-2">
              <Input
                id="login-password"
                label="Senha"
                placeholder="••••••••"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                variant="underline"
                error={errors.password?.message}
                leftIcon={
                  <Lock className="h-5 w-5" aria-hidden="true" />
                }
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="transition-colors hover:text-primary"
                    aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <Eye className="h-5 w-5" aria-hidden="true" />
                    )}
                  </button>
                }
                {...register("password")}
              />
              <div className="mt-2 flex justify-end">
                <Link
                  href="/forgot-password"
                  className="text-xs font-semibold text-primary hover:text-primary-hover hover:underline"
                >
                  Esqueci minha senha
                </Link>
              </div>
            </div>

            <Button
              id="login-submit"
              type="submit"
              className="mt-2 w-full font-bold shadow-lg shadow-primary/20"
              isLoading={isSubmitting}
            >
              Entrar
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            Ainda não possui acesso?{" "}
            <Link
              href="/register"
              className="font-semibold text-primary hover:text-primary-hover hover:underline"
            >
              Cadastre-se
            </Link>
          </p>
        </div>
      </section>

      <aside
        className="relative hidden overflow-hidden bg-[#f9f9f9] lg:block lg:w-[55%] xl:w-[60%]"
        aria-label="Apresentação do Elo Terapêutico"
      >
        <Image
          src="/login_illustration.svg"
          alt="Ilustração de um ambiente terapêutico acolhedor"
          fill
          priority
          sizes="(min-width: 1280px) 60vw, 55vw"
          className="object-cover object-right"
        />

      </aside>
    </main>
  );
}
