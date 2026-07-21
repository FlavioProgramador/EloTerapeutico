"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, CheckCircle2, Eye, EyeOff, Lock } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
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
  resetPasswordSchema,
  type ResetPasswordFormData,
} from "@/features/auth/schemas/auth.schemas";
import { authService } from "@/features/auth/services/auth.service";
import { getPublicErrorMessage } from "@/lib/errors/public-error";

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
      toast.error("Link inválido", {
        description:
          "O link de redefinição está incompleto ou expirou. Solicite um novo link.",
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
      toast.success("Senha redefinida", {
        description: "Sua senha foi alterada com sucesso.",
      });
    } catch (error: unknown) {
      toast.error("Não foi possível alterar a senha", {
        description: getPublicErrorMessage(
          error,
          "O link pode ter expirado. Solicite uma nova redefinição.",
        ),
      });
    }
  };

  if (!token || !uid) {
    return (
      <Card className="border-border/80 bg-card shadow-xs">
        <CardHeader className="space-y-1 pb-4 text-center">
          <CardTitle className="text-xl font-bold text-destructive">
            Link inválido
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            O link de redefinição está inválido, expirado ou incompleto.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-center text-xs text-muted-foreground">
            Solicite um novo link de recuperação de senha.
          </p>
          <Link href="/forgot-password" className="block w-full">
            <Button className="w-full font-semibold">
              Solicitar novo link
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (isSuccess) {
    return (
      <Card className="animate-fade-in border-border/80 bg-card shadow-xs">
        <CardHeader className="space-y-2 pb-4 text-center">
          <div className="mb-2 flex justify-center">
            <CheckCircle2
              className="h-12 w-12 text-success"
              aria-hidden="true"
            />
          </div>
          <CardTitle className="text-xl font-bold text-foreground">
            Senha alterada
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Sua senha foi redefinida. Agora você pode entrar com a nova
            credencial.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/login" className="block w-full">
            <Button
              className="w-full font-semibold"
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Acessar painel
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
          Nova senha
        </CardTitle>
        <CardDescription className="text-xs text-muted-foreground">
          Crie uma senha forte seguindo os requisitos informados abaixo do
          campo.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
          noValidate
        >
          <Input
            id="reset-password"
            label="Nova senha"
            placeholder="••••••••"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            leftIcon={
              <Lock
                className="h-4.5 w-4.5 text-muted-foreground"
                aria-hidden="true"
              />
            }
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                className="cursor-pointer text-muted-foreground transition-colors hover:text-foreground"
              >
                {showPassword ? (
                  <EyeOff className="h-4.5 w-4.5" aria-hidden="true" />
                ) : (
                  <Eye className="h-4.5 w-4.5" aria-hidden="true" />
                )}
              </button>
            }
            error={errors.password?.message}
            {...register("password")}
          />

          <Input
            id="reset-confirm-password"
            label="Confirmar nova senha"
            placeholder="••••••••"
            type={showConfirmPassword ? "text" : "password"}
            autoComplete="new-password"
            leftIcon={
              <Lock
                className="h-4.5 w-4.5 text-muted-foreground"
                aria-hidden="true"
              />
            }
            rightIcon={
              <button
                type="button"
                onClick={() => setShowConfirmPassword((current) => !current)}
                aria-label={
                  showConfirmPassword ? "Ocultar senha" : "Mostrar senha"
                }
                className="cursor-pointer text-muted-foreground transition-colors hover:text-foreground"
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4.5 w-4.5" aria-hidden="true" />
                ) : (
                  <Eye className="h-4.5 w-4.5" aria-hidden="true" />
                )}
              </button>
            }
            error={errors.confirm_password?.message}
            {...register("confirm_password")}
          />

          <Button
            id="reset-submit"
            type="submit"
            className="mt-2 w-full font-semibold"
            isLoading={isSubmitting}
          >
            Confirmar nova senha
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function ResetPasswordPage() {
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
