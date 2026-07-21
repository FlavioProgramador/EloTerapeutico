"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, CheckCircle2, Lock, Mail } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  forgotPasswordSchema,
  type ForgotPasswordFormData,
} from "@/features/auth/schemas/auth.schemas";
import { authService } from "@/features/auth/services/auth.service";
import { getPublicErrorMessage } from "@/lib/errors/public-error";

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);

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
      setSubmitted(true);
      toast.success("Solicitação processada", {
        description:
          "Se o e-mail estiver cadastrado, as instruções foram enviadas.",
      });
    } catch (error: unknown) {
      toast.error("Não foi possível processar a solicitação", {
        description: getPublicErrorMessage(
          error,
          "Tente novamente mais tarde.",
        ),
      });
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4 font-sans text-foreground">
      <div className="w-full max-w-md space-y-6">
        <div className="flex flex-col items-center text-center">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-primary">
            <Lock
              className="h-5 w-5 text-primary-foreground"
              aria-hidden="true"
            />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Elo Terapêutico
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Gestão clínica e prontuários para profissionais
          </p>
        </div>

        {submitted ? (
          <Card className="animate-fade-in border-border/80 bg-card shadow-xs">
            <CardHeader className="space-y-2 pb-4 text-center">
              <div className="mb-2 flex justify-center">
                <CheckCircle2
                  className="h-12 w-12 text-success"
                  aria-hidden="true"
                />
              </div>
              <CardTitle className="text-xl font-bold text-foreground">
                Verifique seu e-mail
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Se o e-mail informado estiver cadastrado, você receberá as
                instruções para redefinir sua senha.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-center text-xs leading-relaxed text-muted-foreground">
                Verifique sua caixa de entrada e a pasta de spam. O link expira
                após o período de segurança definido pela plataforma.
              </p>
              <Link href="/login" className="block w-full">
                <Button
                  variant="outline"
                  className="w-full font-semibold"
                  leftIcon={<ArrowLeft className="h-4 w-4" />}
                >
                  Voltar para o login
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-xl font-bold text-foreground">
                Esqueceu a senha?
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Insira seu e-mail de acesso para receber as instruções de
                redefinição.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form
                onSubmit={handleSubmit(onSubmit)}
                className="space-y-4"
                noValidate
              >
                <Input
                  id="forgot-email"
                  label="E-mail profissional"
                  placeholder="seuemail@exemplo.com"
                  type="email"
                  autoComplete="email"
                  leftIcon={
                    <Mail
                      className="h-4.5 w-4.5 text-muted-foreground"
                      aria-hidden="true"
                    />
                  }
                  error={errors.email?.message}
                  {...register("email")}
                />

                <Button
                  id="forgot-submit"
                  type="submit"
                  className="mt-2 w-full font-semibold"
                  isLoading={isSubmitting}
                >
                  Enviar link de recuperação
                </Button>

                <div className="flex justify-center pt-2">
                  <Link
                    href="/login"
                    className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
                    Voltar para o login
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
