"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, LogIn, Eye, EyeOff, Activity } from "lucide-react";
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
    <div className="relative min-h-screen flex items-center justify-center p-4 bg-radial from-slate-900 via-slate-950 to-black overflow-hidden">
      {/* Elementos de design de fundo (Efeito de luz difusa) */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-600/10 blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md z-10 animate-fade-in">
        {/* Logo / Branding */}
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-2xl bg-primary flex items-center justify-center shadow-lg shadow-primary/30 mb-3 animate-pulse">
            <Activity className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
            Elo Terapêutico
          </h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Gestão clínica e prontuário para psicólogos
          </p>
        </div>

        {/* Card de Login */}
        <Card className="glass-effect border-white/10 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-primary via-emerald-500 to-primary" />
          
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-white">Login</CardTitle>
            <CardDescription className="text-slate-400">
              Digite seu e-mail e senha para acessar sua conta
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="E-mail profissional"
                placeholder="seuemail@exemplo.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={errors.email}
                leftIcon={<Mail className="h-5 w-5" />}
                className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500 focus:border-primary/50"
              />

              <Input
                label="Senha"
                placeholder="••••••••"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={errors.password}
                leftIcon={<Lock className="h-5 w-5" />}
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="hover:text-white transition-colors cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                }
                className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500 focus:border-primary/50"
              />

              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 text-slate-400 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="rounded border-white/10 bg-slate-900/50 text-primary focus:ring-primary/20 accent-primary"
                  />
                  Lembrar de mim
                </label>
                <Link
                  href="/forgot-password"
                  className="text-primary hover:text-primary/80 font-medium transition-colors"
                >
                  Esqueceu a senha?
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full text-white font-semibold transition-all duration-300"
                isLoading={isLoading}
                rightIcon={<LogIn className="h-5 w-5" />}
              >
                Entrar no Painel
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-slate-400">
              Não possui uma conta?{" "}
              <Link
                href="/register"
                className="text-primary hover:text-primary/80 font-semibold transition-colors"
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
