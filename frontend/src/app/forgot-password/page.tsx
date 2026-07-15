"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Mail, ArrowLeft, CheckCircle2, Lock } from "lucide-react";
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
  forgotPasswordSchema,
  type ForgotPasswordFormData,
} from "@/features/auth/schemas/auth.schemas";

export default function ForgotPasswordPage() {
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      await authService.requestPasswordReset(data.email);
      setSubmittedEmail(data.email);
      toast.success("Solicitação processada", {
        description:
          "Se o e-mail estiver cadastrado, as instruções foram enviadas.",
      });
    } catch (error: unknown) {
      const axiosError = error as AxiosError<{
        error?: { message?: string };
        detail?: string;
      }>;
      const serverMessage =
        axiosError?.response?.data?.error?.message ||
        axiosError?.response?.data?.detail ||
        "Não foi possível processar a solicitação. Tente novamente mais tarde.";

      toast.error("Ocorreu um erro", {
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

        {submittedEmail ? (
          /* Estado de Sucesso */
          <Card className="border-border/80 bg-card shadow-xs animate-fade-in">
            <CardHeader className="space-y-2 pb-4 text-center">
              <div className="flex justify-center mb-2">
                <CheckCircle2 className="h-12 w-12 text-accent" />
              </div>
              <CardTitle className="text-xl font-bold text-foreground">
                Verifique seu e-mail
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Se a conta{" "}
                <strong className="text-foreground">{submittedEmail}</strong>{" "}
                estiver cadastrada na plataforma, você receberá um e-mail com
                instruções para redefinir sua senha.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-muted-foreground text-center leading-relaxed">
                Por favor, verifique sua caixa de entrada e também a pasta de
                spam. O link expira em poucas horas por motivos de segurança.
              </p>
              <Link href="/login" passHref className="w-full block">
                <Button
                  variant="outline"
                  className="w-full font-semibold"
                  leftIcon={<ArrowLeft className="h-4 w-4" />}
                >
                  Voltar para o Login
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          /* Formulário de Solicitação */
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-xl font-bold text-foreground">
                Esqueceu a senha?
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Insira o seu e-mail de acesso abaixo para receber um link de
                redefinição de senha.
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
                    id="forgot-email"
                    label="E-mail profissional"
                    placeholder="seuemail@exemplo.com"
                    type="email"
                    autoComplete="email"
                    leftIcon={
                      <Mail className="h-4.5 w-4.5 text-muted-foreground" />
                    }
                    error={errors.email?.message}
                    {...register("email")}
                  />
                </div>

                <Button
                  id="forgot-submit"
                  type="submit"
                  className="w-full text-white font-semibold mt-2"
                  isLoading={isSubmitting}
                >
                  Enviar Link de Recuperação
                </Button>

                <div className="pt-2 flex justify-center">
                  <Link
                    href="/login"
                    className="text-xs text-primary hover:underline font-semibold flex items-center gap-1.5"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    Voltar para o Login
                  </Link>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
