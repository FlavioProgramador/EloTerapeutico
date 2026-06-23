"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, User, Briefcase, FileText, Phone, ArrowRight, ArrowLeft, UserPlus, Activity, Check } from "lucide-react";
import { useToast } from "@/contexts/toast";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function RegisterPage() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const router = useRouter();

  // Estados dos formulários
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    passwordConfirm: "",
    crpNumber: "",
    specialty: "",
    phone: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Limpa erro do campo modificado
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validateStep1 = () => {
    const tempErrors: Record<string, string> = {};
    if (!formData.fullName.trim()) {
      tempErrors.fullName = "Nome completo é obrigatório";
    }
    if (!formData.email.trim()) {
      tempErrors.email = "E-mail é obrigatório";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      tempErrors.email = "Formato de e-mail inválido";
    }
    if (!formData.password) {
      tempErrors.password = "Senha é obrigatória";
    } else if (formData.password.length < 8) {
      tempErrors.password = "A senha deve ter no mínimo 8 caracteres";
    }
    if (formData.password !== formData.passwordConfirm) {
      tempErrors.passwordConfirm = "As senhas não conferem";
    }

    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateStep1()) {
      setStep(2);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validações rápidas para etapa 2
    const tempErrors: Record<string, string> = {};
    if (!formData.crpNumber.trim()) {
      tempErrors.crpNumber = "CRP é obrigatório";
    }
    if (!formData.specialty.trim()) {
      tempErrors.specialty = "Especialidade é obrigatória";
    }
    if (!formData.phone.trim()) {
      tempErrors.phone = "Telefone é obrigatório";
    }

    if (Object.keys(tempErrors).length > 0) {
      setErrors(tempErrors);
      return;
    }

    setIsLoading(true);

    const payload = {
      email: formData.email,
      full_name: formData.fullName,
      password: formData.password,
      password_confirm: formData.passwordConfirm,
      crp_number: formData.crpNumber,
      specialty: formData.specialty,
      phone: formData.phone,
    };

    try {
      await api.post("auth/register/", payload);
      toast({
        title: "Cadastro realizado!",
        description: "Conta criada com sucesso. Faça seu login.",
        variant: "success",
      });
      router.push("/login");
    } catch (error: any) {
      console.error(error);
      const serverErrors = error.response?.data;
      if (serverErrors && typeof serverErrors === "object") {
        const fieldErrors: Record<string, string> = {};
        Object.entries(serverErrors).forEach(([key, value]) => {
          // Mapeia os campos da API para os campos do nosso estado
          const fieldMap: Record<string, string> = {
            email: "email",
            full_name: "fullName",
            password: "password",
            password_confirm: "passwordConfirm",
            crp_number: "crpNumber",
            specialty: "specialty",
            phone: "phone",
          };
          const mappedKey = fieldMap[key] || key;
          fieldErrors[mappedKey] = Array.isArray(value) ? value[0] : String(value);
        });
        setErrors(fieldErrors);
        
        // Se houver algum erro da etapa 1, volta para a etapa 1
        if (fieldErrors.email || fieldErrors.fullName || fieldErrors.password || fieldErrors.passwordConfirm) {
          setStep(1);
        }

        toast({
          title: "Erro no Cadastro",
          description: "Por favor, corrija os erros sinalizados no formulário.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Erro no Cadastro",
          description: "Ocorreu um erro ao criar sua conta. Tente novamente.",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 bg-radial from-slate-900 via-slate-950 to-black overflow-hidden">
      {/* Elementos de design de fundo */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-600/10 blur-[120px] pointer-events-none" />

      <div className="w-full max-w-lg z-10 animate-fade-in">
        {/* Branding */}
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-2xl bg-primary flex items-center justify-center shadow-lg shadow-primary/30 mb-3">
            <Activity className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
            Elo Terapêutico
          </h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Cadastre sua clínica ou perfil profissional em minutos
          </p>
        </div>

        {/* Card de Registro */}
        <Card className="glass-effect border-white/10 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-primary via-emerald-500 to-primary" />
          
          <CardHeader className="space-y-2">
            {/* Indicador de Passos */}
            <div className="flex items-center justify-center gap-3 mb-2">
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                  step === 1
                    ? "bg-primary text-white ring-4 ring-primary/20"
                    : "bg-emerald-500 text-white"
                }`}
              >
                {step > 1 ? <Check className="h-4 w-4" /> : "1"}
              </div>
              <div className={`h-[2px] w-12 transition-all duration-300 ${step > 1 ? "bg-emerald-500" : "bg-slate-700"}`} />
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                  step === 2
                    ? "bg-primary text-white ring-4 ring-primary/20"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                "2"
              </div>
            </div>
            
            <CardTitle className="text-2xl font-bold text-white text-center">
              {step === 1 ? "Dados de Acesso" : "Informações Profissionais"}
            </CardTitle>
            <CardDescription className="text-slate-400 text-center">
              {step === 1
                ? "Crie sua credencial de acesso segura para a plataforma"
                : "Complete o perfil profissional para iniciar os atendimentos"}
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {step === 1 ? (
              <form onSubmit={handleNext} className="space-y-4">
                <Input
                  label="Nome Completo"
                  placeholder="Seu nome completo"
                  value={formData.fullName}
                  onChange={(e) => handleInputChange("fullName", e.target.value)}
                  error={errors.fullName}
                  leftIcon={<User className="h-5 w-5" />}
                  className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500"
                />

                <Input
                  label="E-mail profissional"
                  placeholder="seuemail@exemplo.com"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                  error={errors.email}
                  leftIcon={<Mail className="h-5 w-5" />}
                  className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500"
                />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Senha"
                    placeholder="Mín. 8 caracteres"
                    type="password"
                    value={formData.password}
                    onChange={(e) => handleInputChange("password", e.target.value)}
                    error={errors.password}
                    leftIcon={<Lock className="h-5 w-5" />}
                    className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500"
                  />

                  <Input
                    label="Confirmar Senha"
                    placeholder="Repita a senha"
                    type="password"
                    value={formData.passwordConfirm}
                    onChange={(e) => handleInputChange("passwordConfirm", e.target.value)}
                    error={errors.passwordConfirm}
                    leftIcon={<Lock className="h-5 w-5" />}
                    className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full text-white font-semibold mt-6"
                  rightIcon={<ArrowRight className="h-5 w-5" />}
                >
                  Próxima Etapa
                </Button>
              </form>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  label="Registro Profissional (CRP / CRM / Registro)"
                  placeholder="Ex: CRP 06/123456"
                  value={formData.crpNumber}
                  onChange={(e) => handleInputChange("crpNumber", e.target.value)}
                  error={errors.crpNumber}
                  leftIcon={<FileText className="h-5 w-5" />}
                  className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500"
                />

                <Input
                  label="Especialidade Principal"
                  placeholder="Ex: Psicologia Clínica, TCC, Psicanálise"
                  value={formData.specialty}
                  onChange={(e) => handleInputChange("specialty", e.target.value)}
                  error={errors.specialty}
                  leftIcon={<Briefcase className="h-5 w-5" />}
                  className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500"
                />

                <Input
                  label="Telefone / WhatsApp"
                  placeholder="Ex: (11) 99999-9999"
                  value={formData.phone}
                  onChange={(e) => handleInputChange("phone", e.target.value)}
                  error={errors.phone}
                  leftIcon={<Phone className="h-5 w-5" />}
                  className="bg-slate-900/50 border-white/5 text-white placeholder:text-slate-500"
                />

                <div className="flex gap-4 mt-6">
                  <Button
                    type="button"
                    variant="outline"
                    className="w-1/3 text-white border-white/10 hover:bg-white/5"
                    onClick={() => setStep(1)}
                    leftIcon={<ArrowLeft className="h-5 w-5" />}
                  >
                    Voltar
                  </Button>
                  
                  <Button
                    type="submit"
                    className="w-2/3 text-white font-semibold"
                    isLoading={isLoading}
                    rightIcon={<UserPlus className="h-5 w-5" />}
                  >
                    Finalizar Cadastro
                  </Button>
                </div>
              </form>
            )}

            <div className="mt-6 text-center text-sm text-slate-400">
              Já possui uma conta?{" "}
              <Link
                href="/login"
                className="text-primary hover:text-primary/80 font-semibold transition-colors"
              >
                Faça login
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
