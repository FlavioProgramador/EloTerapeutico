"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Mail, Lock, LogIn, Eye, EyeOff, ArrowLeft } from "lucide-react";
import { AxiosError } from "axios";
import { useAuth } from "@/contexts/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  loginSchema,
  type LoginFormData,
} from "@/features/auth/schemas/auth.schemas";
import { Brand } from "@/features/landing/brand";

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
      toast.success("Bem-vindo de volta!", {
        description: "Login realizado com sucesso.",
      });
    } catch (error: unknown) {
      const axiosError = error as AxiosError<Record<string, unknown>>;
      const data = axiosError?.response?.data;

      let serverMessage = "Verifique suas credenciais e tente novamente.";
      if (data) {
        if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
          serverMessage = String(data.non_field_errors[0]);
        } else if (typeof (data.error as Record<string, unknown>)?.message === "string") {
          serverMessage = (data.error as Record<string, unknown>).message as string;
        } else if (typeof data.detail === "string") {
          serverMessage = data.detail;
        }
      }

      toast.error("Falha na autenticação", {
        description: serverMessage,
      });
    }
  };

  return (
    <div className="min-h-screen flex bg-[#F9F9F9] font-sans overflow-hidden">
      
      {/* Left Column - Form */}
      <div className="w-full lg:w-[45%] xl:w-[40%] p-8 sm:p-12 md:p-24 flex flex-col justify-center relative z-10">
        
        {/* Back Button */}
        <Link
          href="/"
          className="absolute top-8 left-8 sm:top-12 sm:left-12 inline-flex items-center gap-2 text-sm text-gray-400 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Link>

        <div className="max-w-sm w-full mx-auto space-y-10 relative mt-8">
          
          {/* Header */}
          <div className="flex flex-col gap-6">
            <div className="flex-shrink-0 [&_span]:!text-[#F97316] [&_.grid]:!bg-white [&_.grid]:!border-[#F97316]/30 [&_.grid]:!shadow-none [&_.grid]:!w-14 [&_.grid]:!h-14 [&_svg]:!w-8 [&_svg]:!h-8">
              <Brand />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-[#1A2E26] tracking-tight mb-1">
                Bem-vindo(a) de volta!
              </h1>
              <p className="text-gray-500 text-sm">
                Acesse sua conta para gerenciar seus atendimentos.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8" noValidate>
            
            <div className="space-y-6">
              <div className="space-y-2 group">
                <label htmlFor="login-email" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                  E-mail
                </label>
                <Input
                  id="login-email"
                  placeholder="seuemail@exemplo.com"
                  type="email"
                  autoComplete="email"
                  error={errors.email?.message}
                  leftIcon={<Mail className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                  {...register("email")}
                  className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 pr-2 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                />
              </div>

              <div className="space-y-2 group">
                <label htmlFor="login-password" className="text-xs font-bold text-gray-400 uppercase tracking-wider group-focus-within:text-[#F97316] transition-colors duration-300">
                  Senha
                </label>
                <div className="relative">
                  <Input
                    id="login-password"
                    placeholder="••••••••"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    error={errors.password?.message}
                    leftIcon={<Lock className="h-5 w-5 text-gray-400 group-focus-within:text-[#F97316] transition-colors duration-300" />}
                    {...register("password")}
                    className="bg-transparent focus:bg-[#F97316]/[0.03] border-0 border-b-2 focus:border-b-[3px] border-gray-200 rounded-none !pl-10 shadow-none !outline-none focus:!outline-none focus-visible:!outline-none focus:!ring-0 focus-visible:!ring-0 focus:border-[#F97316] text-[#1A2E26] font-medium text-base pr-10 transition-all duration-300 [&:-webkit-autofill]:shadow-[0_0_0_30px_white_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#1A2E26]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#F97316] transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <Button
                id="login-submit"
                type="submit"
                className="w-auto px-10 py-6 hover:bg-[#EA580C] text-white rounded-full font-bold shadow-none transition-all"
                style={{ backgroundColor: "#F97316" }} /* Overriding with Brand Orange */
                isLoading={isSubmitting}
              >
                ENTRAR
              </Button>
            </div>
          </form>

          <div className="pt-8 text-sm text-gray-400 font-medium flex items-center gap-2">
            Ainda não possui acesso? 
            <Link href="/planos" className="text-[#A855F7] hover:underline" style={{ color: "#F97316" }}>
              Cadastre-se
            </Link>
          </div>
        </div>
      </div>

      {/* Right Column - Illustration */}
      <div className="hidden lg:block lg:w-[55%] xl:w-[60%] relative bg-[#F9F9F9]">
        {/* The massive curved container (now using the image's native white background curves) */}
        <div className="absolute inset-0 overflow-hidden">
          <img 
            src="/login_illustration_final.jpg" 
            alt="Ambiente Terapêutico" 
            className="w-full h-full object-cover object-[left_center] scale-[1.05] origin-left"
          />
        </div>
      </div>
      
    </div>
  );
}
