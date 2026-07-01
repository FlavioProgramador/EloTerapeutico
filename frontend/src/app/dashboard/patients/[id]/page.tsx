"use client";

import {
  ArrowLeft,
  CalendarPlus,
  ClipboardList,
  Edit2,
  Mail,
  MapPin,
  Phone,
  Trash2,
  UserRound,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { Badge, getPatientStatusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth";
import { PatientFormDrawer } from "@/features/patients/components/patient-form-drawer";
import {
  useDeletePatient,
  usePatient,
} from "@/features/patients/hooks/use-patients";

function Detail({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium text-foreground">
        {value || "Não informado"}
      </p>
    </div>
  );
}

function addressLabel(value: unknown) {
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object") return undefined;
  const address = value as Record<string, string | undefined>;
  return [
    address.street,
    address.number,
    address.neighborhood,
    address.city,
    address.state,
  ]
    .filter(Boolean)
    .join(", ");
}

export default function PatientDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const patientId = Number(params.id);
  const [editOpen, setEditOpen] = useState(false);
  const patientQuery = usePatient(patientId);
  const deleteMutation = useDeletePatient();
  const patient = patientQuery.data;

  if (patientQuery.isLoading) {
    return <div className="h-[34rem] animate-pulse rounded-xl bg-secondary" />;
  }

  if (!patient || patientQuery.isError) {
    return (
      <div className="rounded-xl border border-dashed border-border p-12 text-center">
        <h1 className="text-base font-bold text-foreground">
          Paciente não encontrado
        </h1>
        <Button
          className="mt-4"
          variant="outline"
          onClick={() => router.push("/dashboard/patients")}
        >
          Voltar para pacientes
        </Button>
      </div>
    );
  }

  const canManage =
    user?.role === "admin" ||
    (user?.role === "therapist" && patient.therapist === user.id);
  const canAccessRecords = canManage;
  const address = addressLabel(patient.address);
  const createdAt = patient.created_at
    ? new Date(patient.created_at).toLocaleDateString("pt-BR")
    : "Não informado";

  const archive = () => {
    if (
      !window.confirm(
        `Arquivar o cadastro de ${patient.full_name}? O histórico será preservado.`,
      )
    ) {
      return;
    }
    deleteMutation.mutate(patient.id, {
      onSuccess: () => router.push("/dashboard/patients"),
    });
  };

  return (
    <div className="space-y-5">
      <button
        type="button"
        onClick={() => router.push("/dashboard/patients")}
        className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Voltar para pacientes
      </button>

      <header className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <span className="grid h-12 w-12 place-items-center rounded-full border border-primary/25 bg-primary/10 text-lg font-bold text-primary">
            {patient.full_name.charAt(0).toUpperCase()}
          </span>
          <div>
            <h1 className="text-xl font-bold text-foreground">
              {patient.social_name || patient.full_name}
            </h1>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant={getPatientStatusVariant(patient.status)}>
                {patient.status_display || patient.status}
              </Badge>
              <span className="text-[10px] text-muted-foreground">
                Cadastrado em {createdAt}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {canAccessRecords && (
            <Button
              size="sm"
              onClick={() => router.push(`/dashboard/records/${patient.id}`)}
              leftIcon={<ClipboardList className="h-4 w-4" />}
            >
              Ver prontuário
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => router.push(`/dashboard/agenda?patient=${patient.id}`)}
            leftIcon={<CalendarPlus className="h-4 w-4" />}
          >
            Agendar consulta
          </Button>
          {canManage && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setEditOpen(true)}
              leftIcon={<Edit2 className="h-4 w-4" />}
            >
              Editar cadastro
            </Button>
          )}
          {canManage && (
            <Button
              size="sm"
              variant="outline"
              onClick={archive}
              isLoading={deleteMutation.isPending}
              leftIcon={<Trash2 className="h-4 w-4" />}
            >
              Arquivar
            </Button>
          )}
        </div>
      </header>

      <div className="grid gap-4 xl:grid-cols-3">
        <section className="rounded-xl border border-border bg-card p-5 xl:col-span-2">
          <h2 className="flex items-center gap-2 border-b border-border pb-3 text-base font-semibold">
            <UserRound className="h-4 w-4 text-primary" /> Dados cadastrais
          </h2>
          <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <Detail label="Nome completo" value={patient.full_name} />
            <Detail
              label="CPF"
              value={patient.formatted_cpf || patient.masked_cpf}
            />
            <Detail
              label="Nascimento"
              value={
                patient.birth_date
                  ? new Date(`${patient.birth_date}T12:00:00`).toLocaleDateString(
                      "pt-BR",
                    )
                  : undefined
              }
            />
            <Detail label="Terapeuta" value={patient.therapist_name} />
            <Detail label="Modalidade" value={patient.modality} />
            <Detail label="Pagador" value={patient.payer_type} />
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="border-b border-border pb-3 text-base font-semibold">
            Contato
          </h2>
          <div className="mt-4 space-y-4">
            <p className="flex items-center gap-2 text-sm text-foreground">
              <Phone className="h-4 w-4 text-primary" />
              {patient.phone || "Não informado"}
            </p>
            <p className="flex items-center gap-2 text-sm text-foreground">
              <Mail className="h-4 w-4 text-primary" />
              {patient.email || "Não informado"}
            </p>
            <p className="flex items-start gap-2 text-sm text-foreground">
              <MapPin className="mt-0.5 h-4 w-4 text-primary" />
              {address || "Não informado"}
            </p>
          </div>
        </section>
      </div>

      <PatientFormDrawer
        open={editOpen}
        patientId={patient.id}
        onClose={() => setEditOpen(false)}
        onSaved={() => patientQuery.refetch()}
      />
    </div>
  );
}
