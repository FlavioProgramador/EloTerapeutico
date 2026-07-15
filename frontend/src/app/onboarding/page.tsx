"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Clock3,
  Loader2,
  MapPin,
  Phone,
  Stethoscope,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/auth";
import { api } from "@/lib/api";

interface OnboardingData {
  clinic_name?: string;
  professional_address?: Record<string, string>;
  onboarding_completed?: boolean;
  user?: {
    full_name?: string;
    specialty?: string;
    crp_number?: string;
    phone?: string;
    default_session_duration?: number;
  };
}

export default function OnboardingPage() {
  const router = useRouter();
  const { updateUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: "",
    specialty: "",
    crp_number: "",
    clinic_name: "",
    phone: "",
    address_line: "",
    city: "",
    state: "",
    default_session_duration: "50",
  });

  useEffect(() => {
    let mounted = true;
    void api
      .get<OnboardingData>("auth/onboarding/")
      .then(({ data }) => {
        if (!mounted) return;
        if (data.onboarding_completed) {
          router.replace("/dashboard");
          return;
        }
        setForm({
          full_name: data.user?.full_name || "",
          specialty: data.user?.specialty || "",
          crp_number: data.user?.crp_number || "",
          clinic_name: data.clinic_name || "",
          phone: data.user?.phone || "",
          address_line: data.professional_address?.address_line || "",
          city: data.professional_address?.city || "",
          state: data.professional_address?.state || "",
          default_session_duration: String(
            data.user?.default_session_duration || 50,
          ),
        });
      })
      .catch(() =>
        toast.error("Não foi possível carregar a configuração inicial."),
      )
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [router]);

  function change(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(skipOptional = false) {
    setSaving(true);
    try {
      const response = await api.post<{
        next: string;
        onboarding_completed: boolean;
        user?: { full_name?: string; specialty?: string; phone?: string };
      }>("auth/onboarding/", {
        full_name: form.full_name,
        specialty: form.specialty,
        crp_number: form.crp_number,
        clinic_name: form.clinic_name,
        phone: form.phone,
        professional_address: {
          address_line: form.address_line,
          city: form.city,
          state: form.state,
        },
        default_session_duration: Number(form.default_session_duration) || 50,
        complete: true,
        skip_optional: skipOptional,
      });
      updateUser({
        full_name: response.data.user?.full_name || form.full_name,
        specialty: response.data.user?.specialty || form.specialty,
        phone: response.data.user?.phone || form.phone,
        clinic_name: form.clinic_name,
        onboarding_completed: response.data.onboarding_completed,
      });
      toast.success(
        skipOptional
          ? "Você pode completar os dados depois."
          : "Configuração inicial concluída.",
      );
      router.replace(response.data.next || "/dashboard");
    } catch (error) {
      const message =
        typeof error === "object" && error !== null && "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response
              ?.data?.detail
          : null;
      toast.error(message || "Não foi possível salvar a configuração inicial.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#F7FAF8]">
        <div className="flex items-center gap-3 text-sm text-gray-600">
          <Loader2 className="h-5 w-5 animate-spin" /> Preparando sua conta...
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#F7FAF8] px-5 py-10 text-[#1A2E26] sm:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-[#F97316]"
          >
            <ArrowLeft className="h-4 w-4" /> Página inicial
          </Link>
          <button
            type="button"
            onClick={() => void submit(true)}
            disabled={saving}
            className="text-sm font-bold text-gray-500 hover:text-[#F97316] disabled:opacity-50"
          >
            Continuar e preencher depois
          </button>
        </div>

        <section className="mt-8 overflow-hidden rounded-[32px] border border-[#1A2E26]/10 bg-white shadow-sm">
          <div className="border-b border-gray-100 bg-gradient-to-r from-[#FFF7ED] to-[#ECFDF5] px-7 py-8 sm:px-10">
            <p className="text-sm font-extrabold uppercase tracking-[0.2em] text-[#F97316]">
              Configuração inicial
            </p>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">
              Deixe o Elo Terapêutico com a sua cara.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-600">
              Esses dados ajudam a configurar perfil, agenda e documentos.
              Apenas o nome é essencial; o restante pode ser concluído depois.
            </p>
          </div>

          <div className="grid gap-8 p-7 sm:p-10 lg:grid-cols-2">
            <div className="space-y-5">
              <Input
                label="Nome profissional"
                leftIcon={<Stethoscope className="h-4 w-4" />}
                value={form.full_name}
                onChange={(event) => change("full_name", event.target.value)}
              />
              <Input
                label="Profissão ou especialidade"
                value={form.specialty}
                onChange={(event) => change("specialty", event.target.value)}
              />
              <Input
                label="Registro profissional"
                placeholder="Ex.: 06/123456"
                value={form.crp_number}
                onChange={(event) => change("crp_number", event.target.value)}
              />
              <Input
                label="Nome da clínica"
                leftIcon={<Building2 className="h-4 w-4" />}
                value={form.clinic_name}
                onChange={(event) => change("clinic_name", event.target.value)}
              />
              <Input
                label="Telefone"
                leftIcon={<Phone className="h-4 w-4" />}
                value={form.phone}
                onChange={(event) => change("phone", event.target.value)}
              />
            </div>

            <div className="space-y-5">
              <Input
                label="Endereço profissional"
                leftIcon={<MapPin className="h-4 w-4" />}
                value={form.address_line}
                onChange={(event) => change("address_line", event.target.value)}
              />
              <div className="grid gap-4 sm:grid-cols-[1fr_110px]">
                <Input
                  label="Cidade"
                  value={form.city}
                  onChange={(event) => change("city", event.target.value)}
                />
                <Input
                  label="UF"
                  maxLength={2}
                  value={form.state}
                  onChange={(event) =>
                    change("state", event.target.value.toUpperCase())
                  }
                />
              </div>
              <Input
                label="Duração padrão da sessão"
                type="number"
                min={10}
                max={480}
                leftIcon={<Clock3 className="h-4 w-4" />}
                value={form.default_session_duration}
                onChange={(event) =>
                  change("default_session_duration", event.target.value)
                }
              />

              <div className="rounded-2xl border border-[#2F855A]/15 bg-[#ECFDF5] p-5 text-sm text-[#166534]">
                A configuração pode ser alterada a qualquer momento. Nenhum dado
                clínico é solicitado nesta etapa.
              </div>

              <Button
                type="button"
                onClick={() => void submit(false)}
                isLoading={saving}
                className="h-12 w-full rounded-xl bg-[#F97316] font-bold text-white hover:bg-[#EA580C]"
              >
                Concluir e acessar o dashboard{" "}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
