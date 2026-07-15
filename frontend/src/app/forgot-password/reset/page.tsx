"use client";

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Lock, Eye, EyeOff, CheckCircle2, ArrowRight } from "lucide-react";
import { AxiosError } from "axios";
import { authService } from "@/features/auth/services/auth.service";
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
  resetPasswordSchema,
  type ResetPasswordFormData,
} from "@/features/auth/schemas/auth.schemas";

function ResetPasswordForm() {
  const searchParams = useSearchParams();

  const token = searchParams.get("token");
  const uid = searchParams.get("uid");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token || !uid) {
      toast.error("Parâmetros inválidos", {
        description:
          "O link de redefinição de senha está incompleto ou inválido.",
      });
      return;
    }

    try {
      await authService.confirmPasswordReset({
        token,
        uidb64: uid,
        new_password: data.password,
        new_password_confirm: data.confirm_password,
      });

      setIsSuccess(true);
      toast.success("Senha redefinida!", {
        description: "Sua senha foi alterada com sucesso.",
      });
    } catch (error: unknown) {
      const axiosError = error as AxiosError<{
        error?: { message?: string };
        detail?: string;
        token?: string[];
      }>;
      const serverMessage =
        axiosError?.response?.data?.error?.message ||
        axiosError?.response?.data?.detail ||
        (axiosError?.response?.data?.token
          ? axiosError.response.data.token[0]
          : null) ||
        "Erro ao redefinir a senha. O link pode ter expirado.";

      toast.error("Falha ao alterar senha", {
        description: serverMessage,
      });
    }
  };

  if (!token || !uid) {
    return (
      <Card className="border-border/80 bg-card shadow-xs">
        <CardHeader className="space-y-1 pb-4 text-center">
          <CardTitle className="text-xl font-bold text-destructive">
            Link Inválido
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            O link de redefinição de senha que você acessou é inválido, está
            expirado ou incompleto.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-xs text-muted-foreground text-center">
            Por favor, solicite um novo link de recuperação de senha.
          </p>
          <Link href="/forgot-password" passHref className="w-full block">
            <Button className="w-full text-white font-semibold">
              Solicitar Novo Link
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (isSuccess) {
    return (
      <Card className="border-border/80 bg-card shadow-xs animate-fade-in">
        <CardHeader className="space-y-2 pb-4 text-center">
          <div className="flex justify-center mb-2">
            <CheckCircle2 className="h-12 w-12 text-accent" />
          </div>
          <CardTitle className="text-xl font-bold text-foreground">
            Senha Alterada!
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Sua senha foi redefinida com sucesso. Agora você já pode entrar no
            sistema com a nova credencial.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/login" passHref className="w-full block">
            <Button
              className="w-full text-white font-semibold"
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Acessar Painel
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="space-y-1 pb-4">
        <CardTitle className="text-xl font-bold text-foreground">
          Nova Senha
        </CardTitle>
        <CardDescription className="text-xs text-muted-foreground">
          Crie uma senha forte com pelo menos 8 caracteres, contendo letra
          maiúscula e número.
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
              id="reset-password"
              label="Nova senha"
              placeholder="••••••••"
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
          </div>

          <div className="space-y-1">
            <Input
              id="reset-confirm-password"
              label="Confirmar nova senha"
              placeholder="••••••••"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              leftIcon={<Lock className="h-4.5 w-4.5 text-muted-foreground" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={
                    showConfirmPassword ? "Ocultar senha" : "Mostrar senha"
                  }
                  className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4.5 w-4.5" />
                  ) : (
                    <Eye className="h-4.5 w-4.5" />
                  )}
                </button>
              }
              error={errors.confirm_password?.message}
              {...register("confirm_password")}
            />
          </div>

          <Button
            id="reset-submit"
            type="submit"
            className="w-full text-white font-semibold mt-2"
            isLoading={isSubmitting}
          >
            Confirmar Nova Senha
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function ResetPasswordPage() {
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

        <Suspense
          fallback={
            <Card className="border-border/80 bg-card shadow-xs">
              <CardContent className="p-6 text-center text-sm text-muted-foreground">
                Carregando formulário de redefinição...
              </CardContent>
            </Card>
          }
        >
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
