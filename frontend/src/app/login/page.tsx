"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Mail, Lock, LogIn, Eye, EyeOff } from "lucide-react";
import { AxiosError } from "axios";
import { useAuth } from "@/contexts/auth";
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
  loginSchema,
  type LoginFormData,
} from "@/features/auth/schemas/auth.schemas";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur", // valida ao sair do campo, não a cada keystroke
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login({ email: data.email, password: data.password });
      toast.success("Bem-vindo de volta!", {
        description: "Login realizado com sucesso.",
      });
      // Redirecionamento feito pelo AuthContext
    } catch (error: unknown) {
      const axiosError = error as AxiosError<{ error?: { message?: string }; detail?: string }>;
      const serverMessage =
        axiosError?.response?.data?.error?.message ||
        axiosError?.response?.data?.detail ||
        "Verifique suas credenciais e tente novamente.";

      toast.error("Falha na autenticação", {
        description: serverMessage,
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background text-foreground font-sans">
      <div className="w-full max-w-md space-y-6">

        {/* Branding */}
        <div className="flex flex-col items-center text-center">
          <div className="h-10 w-10 rounded-md bg-primary flex items-center justify-center mb-3">
            <Lock className="h-5 w-5 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Elo Terapêutico
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Gestão clínica e prontuários para profissionais
          </p>
        </div>

        {/* Card de Login */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-xl font-bold text-foreground">
              Entrar
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              Digite seu e-mail e senha para acessar o painel clínico.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="space-y-4"
              noValidate
            >
              <div className="space-y-1">
                <Input
                  id="login-email"
                  label="E-mail profissional"
                  placeholder="seuemail@exemplo.com"
                  type="email"
                  autoComplete="email"
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? "login-email-error" : undefined}
                  leftIcon={<Mail className="h-4.5 w-4.5 text-muted-foreground" />}
                  error={errors.email?.message}
                  {...register("email")}
                />
                {errors.email && (
                  <p id="login-email-error" className="text-xs text-destructive" role="alert">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <Input
                  id="login-password"
                  label="Senha"
                  placeholder="••••••••"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "login-password-error" : undefined}
                  leftIcon={<Lock className="h-4.5 w-4.5 text-muted-foreground" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                      className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4.5 w-4.5" />
                      ) : (
                        <Eye className="h-4.5 w-4.5" />
                      )}
                    </button>
                  }
                  error={errors.password?.message}
                  {...register("password")}
                />
                {errors.password && (
                  <p id="login-password-error" className="text-xs text-destructive" role="alert">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 text-muted-foreground cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="rounded-xs border-border bg-secondary text-primary focus:ring-ring"
                  />
                  Lembrar de mim
                </label>
                <Link
                  href="/forgot-password"
                  className="text-primary hover:underline font-medium"
                >
                  Esqueceu a senha?
                </Link>
              </div>

              <Button
                id="login-submit"
                type="submit"
                className="w-full text-white font-semibold mt-2"
                isLoading={isSubmitting}
                rightIcon={<LogIn className="h-4 w-4" />}
              >
                Entrar no Painel
              </Button>
            </form>

            <div className="mt-5 text-center text-xs text-muted-foreground">
              Não possui uma conta?{" "}
              <Link
                href="/register"
                className="text-primary hover:underline font-semibold"
              >
                Cadastre-se grátis
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
