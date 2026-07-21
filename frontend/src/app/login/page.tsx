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
    <main className="flex min-h-screen overflow-hidden bg-background font-sans">
      <section className="relative z-10 flex w-full flex-col justify-center overflow-y-auto p-6 sm:p-10 lg:w-[45%] lg:p-14 xl:w-[40%] xl:p-20">
        <Link
          href="/"
          className="absolute left-6 top-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground sm:left-10 sm:top-10"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Voltar
        </Link>

        <div className="mx-auto mt-12 w-full max-w-sm space-y-8">
          <div className="space-y-5">
            <Brand />
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-foreground">
                Bem-vindo de volta
              </h1>
              <p className="mt-2 text-sm text-muted-foreground">
                Acesse sua conta para gerenciar seus atendimentos com segurança.
              </p>
            </div>
          </div>

          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-5"
            noValidate
          >
            <Input
              id="login-email"
              label="E-mail"
              placeholder="seuemail@exemplo.com"
              type="email"
              autoComplete="email"
              error={errors.email?.message}
              leftIcon={
                <Mail className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
              }
              {...register("email")}
            />

            <div className="space-y-2">
              <Input
                id="login-password"
                label="Senha"
                placeholder="••••••••"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                error={errors.password?.message}
                leftIcon={
                  <Lock
                    className="h-5 w-5 text-muted-foreground"
                    aria-hidden="true"
                  />
                }
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="text-muted-foreground transition-colors hover:text-primary"
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
              <div className="flex justify-end">
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
              className="w-full font-bold"
              isLoading={isSubmitting}
            >
              Entrar
            </Button>
          </form>

          <p className="text-sm text-muted-foreground">
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

      <section
        className="relative hidden overflow-hidden border-l border-sidebar-border bg-sidebar lg:block lg:w-[55%] xl:w-[60%]"
        aria-label="Apresentação do Elo Terapêutico"
      >
        <div className="absolute inset-0 bg-sidebar/25" aria-hidden="true" />
        <Image
          src="/login_illustration.svg"
          alt="Ilustração de um ambiente terapêutico acolhedor"
          fill
          priority
          sizes="(min-width: 1280px) 60vw, 55vw"
          className="object-cover object-left"
        />
        <div className="absolute inset-x-10 bottom-10 rounded-xl border border-sidebar-border bg-sidebar-surface/90 p-6 text-sidebar-foreground">
          <p className="text-base font-semibold text-sidebar-foreground">
            Organização clínica com segurança e acolhimento.
          </p>
          <p className="mt-2 text-sm text-sidebar-muted">
            Agenda, pacientes, prontuários e financeiro em um único ambiente.
          </p>
        </div>
      </section>
    </main>
  );
}
