"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, LogIn, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/contexts/auth";
import { useToast } from "@/contexts/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const { login } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  const validateForm = () => {
    const tempErrors: { email?: string; password?: string } = {};
    if (!email) {
      tempErrors.email = "E-mail é obrigatório";
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      tempErrors.email = "Formato de e-mail inválido";
    }
    
    if (!password) {
      tempErrors.password = "Senha é obrigatória";
    } else if (password.length < 6) {
      tempErrors.password = "A senha deve ter pelo menos 6 caracteres";
    }

    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      await login({ email, password });
      toast({
        title: "Bem-vindo de volta!",
        description: "Login realizado com sucesso.",
        variant: "success",
      });
      router.push("/dashboard");
    } catch (error: any) {
      console.error(error);
      const errorData = error.response?.data?.error;
      const errorMessage =
        errorData?.message ||
        errorData?.details?.non_field_errors?.[0] ||
        "Não foi possível realizar o login. Verifique suas credenciais.";
      
      toast({
        title: "Falha na Autenticação",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background text-foreground font-sans">
      <div className="w-full max-w-md space-y-6">
        
        {/* Logo / Branding */}
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
            <CardTitle className="text-xl font-bold text-foreground">Login</CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              Digite seu e-mail e senha para acessar o painel clínico.
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="E-mail profissional"
                placeholder="seuemail@exemplo.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={errors.email}
                leftIcon={<Mail className="h-4.5 w-4.5 text-muted-foreground" />}
              />

              <Input
                label="Senha"
                placeholder="••••••••"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={errors.password}
                leftIcon={<Lock className="h-4.5 w-4.5 text-muted-foreground" />}
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                  </button>
                }
              />

              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 text-muted-foreground cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="rounded-xs border-border bg-secondary text-primary focus:ring-ring"
                  />
                  Lembrar de mim
                </label>
                <Link
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    alert("Redefinição de senha em desenvolvimento.");
                  }}
                  className="text-primary hover:underline font-medium"
                >
                  Esqueceu a senha?
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full text-white font-semibold mt-2"
                isLoading={isLoading}
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
