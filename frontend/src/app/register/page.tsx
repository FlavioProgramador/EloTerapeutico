"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, User, Briefcase, FileText, Phone, ArrowRight, ArrowLeft, UserPlus, Check, Eye, EyeOff } from "lucide-react";
import { useToast } from "@/contexts/toast";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function RegisterPage() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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
      const errorData = error.response?.data?.error;
      const serverErrors = errorData?.details || error.response?.data;
      
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

        const toastMessage = errorData?.message || "Por favor, corrija os erros sinalizados no formulário.";

        toast({
          title: "Erro no Cadastro",
          description: toastMessage,
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
    <div className="min-h-screen flex items-center justify-center p-4 bg-background text-foreground font-sans">
      <div className="w-full max-w-md space-y-6">
        
        {/* Branding */}
        <div className="flex flex-col items-center text-center">
          <div className="h-10 w-10 rounded-md bg-primary flex items-center justify-center mb-3">
            <UserPlus className="h-5 w-5 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Elo Terapêutico
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Cadastre sua clínica ou perfil profissional em minutos
          </p>
        </div>

        {/* Card de Registro */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardHeader className="space-y-2 pb-4">
            
            {/* Indicador de Passos */}
            <div className="flex items-center justify-center gap-3 mb-2">
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors duration-200 ${
                  step === 1
                    ? "bg-primary text-primary-foreground"
                    : "bg-primary/20 text-primary"
                }`}
              >
                {step > 1 ? <Check className="h-4 w-4" /> : "1"}
              </div>
              <div className={`h-[2px] w-12 transition-colors duration-200 ${step > 1 ? "bg-primary/40" : "bg-border"}`} />
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors duration-200 ${
                  step === 2
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-muted-foreground"
                }`}
              >
                2
              </div>
            </div>
            
            <CardTitle className="text-xl font-bold text-foreground text-center">
              {step === 1 ? "Dados de Acesso" : "Informações Profissionais"}
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground text-center">
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
                  leftIcon={<User className="h-4.5 w-4.5 text-muted-foreground" />}
                />

                <Input
                  label="E-mail profissional"
                  placeholder="seuemail@exemplo.com"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                  error={errors.email}
                  leftIcon={<Mail className="h-4.5 w-4.5 text-muted-foreground" />}
                />

                <Input
                  label="Senha"
                  placeholder="Mínimo de 8 caracteres"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange("password", e.target.value)}
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

                <Input
                  label="Confirmar Senha"
                  placeholder="Repita a senha"
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.passwordConfirm}
                  onChange={(e) => handleInputChange("passwordConfirm", e.target.value)}
                  error={errors.passwordConfirm}
                  leftIcon={<Lock className="h-4.5 w-4.5 text-muted-foreground" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                    </button>
                  }
                />

                <Button
                  type="submit"
                  className="w-full text-white font-semibold mt-6"
                  rightIcon={<ArrowRight className="h-4 w-4" />}
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
                  leftIcon={<FileText className="h-4.5 w-4.5 text-muted-foreground" />}
                />

                <Input
                  label="Especialidade Principal"
                  placeholder="Ex: Psicologia Clínica, TCC, Psicanálise"
                  value={formData.specialty}
                  onChange={(e) => handleInputChange("specialty", e.target.value)}
                  error={errors.specialty}
                  leftIcon={<Briefcase className="h-4.5 w-4.5 text-muted-foreground" />}
                />

                <Input
                  label="Telefone / WhatsApp"
                  placeholder="Ex: (11) 99999-9999"
                  value={formData.phone}
                  onChange={(e) => handleInputChange("phone", e.target.value)}
                  error={errors.phone}
                  leftIcon={<Phone className="h-4.5 w-4.5 text-muted-foreground" />}
                />

                <div className="flex gap-4 mt-6">
                  <Button
                    type="button"
                    variant="outline"
                    className="w-1/3"
                    onClick={() => setStep(1)}
                    leftIcon={<ArrowLeft className="h-4 w-4" />}
                  >
                    Voltar
                  </Button>
                  
                  <Button
                    type="submit"
                    className="w-2/3 text-white font-semibold"
                    isLoading={isLoading}
                    rightIcon={<UserPlus className="h-4 w-4" />}
                  >
                    Criar Conta
                  </Button>
                </div>
              </form>
            )}

            <div className="mt-5 text-center text-xs text-muted-foreground">
              Já possui uma conta?{" "}
              <Link
                href="/login"
                className="text-primary hover:underline font-semibold"
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
