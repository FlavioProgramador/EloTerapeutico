import { Mail, Phone } from "lucide-react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { PatientActionsMenu } from "./patient-actions-menu";
import {
  PATIENT_STATUS_VARIANT,
  patientInitials,
  patientPayerLabel,
} from "./patient-list-config";
import type { PatientListItem } from "./patient-list-item";

interface RowProps {
  patient: PatientListItem;
  canManage: boolean;
  canAccessRecords: boolean;
  reminderPending: boolean;
  onReminderChange: (enabled: boolean) => void;
  onEdit: () => void;
  onDeactivate: () => void;
  onRestore: () => void;
  onRemove: () => void;
  onRegistrationLink: () => void;
}

function ReminderSwitch({
  patient,
  disabled,
  pending,
  onChange,
}: {
  patient: PatientListItem;
  disabled: boolean;
  pending: boolean;
  onChange: (enabled: boolean) => void;
}) {
  const enabled = Boolean(patient.reminders_enabled);
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      aria-label={`Lembretes de ${patient.display_name}`}
      disabled={disabled || pending}
      onClick={(event) => {
        event.stopPropagation();
        onChange(!enabled);
      }}
      className={`relative inline-flex h-6 w-10 rounded-full border transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-45 ${
        enabled ? "border-primary bg-primary" : "border-border bg-secondary"
      }`}
    >
      <span
        className={`mt-0.5 h-4 w-4 rounded-full bg-background shadow-sm transition-transform ${
          enabled ? "translate-x-5" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

function ActionMenu(props: RowProps) {
  return (
    <PatientActionsMenu
      patient={props.patient}
      canManage={props.canManage}
      canAccessRecords={props.canAccessRecords}
      onEdit={props.onEdit}
      onDeactivate={props.onDeactivate}
      onRestore={props.onRestore}
      onRemove={props.onRemove}
      onRegistrationLink={props.onRegistrationLink}
    />
  );
}

export function PatientDesktopRow(props: RowProps) {
  const router = useRouter();
  const patient = props.patient;

  return (
    <tr className="hover:bg-secondary/35">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-primary/20 bg-primary/10 text-xs font-bold text-primary">
            {patientInitials(patient.display_name)}
          </span>
          <div className="min-w-0">
            <button
              type="button"
              onClick={() => router.push(`/dashboard/patients/${patient.id}`)}
              className="block max-w-52 truncate text-left text-xs font-semibold text-foreground hover:text-primary"
            >
              {patient.display_name}
            </button>
            <p className="mt-1 text-[10px] text-muted-foreground">
              {patient.masked_cpf}
            </p>
          </div>
        </div>
      </td>
      <td className="max-w-64 px-3 py-3">
        <p className="flex items-center gap-2 truncate text-[11px] text-foreground">
          <Mail className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          {patient.email || "E-mail não informado"}
        </p>
        <p className="mt-1 flex items-center gap-2 truncate text-[10px] text-muted-foreground">
          <Phone className="h-3.5 w-3.5 shrink-0" />
          {patient.phone || "Telefone não informado"}
        </p>
      </td>
      <td className="px-3 py-3 text-xs text-foreground">
        {typeof patient.age === "number" ? `${patient.age} anos` : "Não informada"}
      </td>
      <td className="max-w-48 px-3 py-3 text-xs text-foreground">
        <span className="block truncate">{patientPayerLabel(patient)}</span>
      </td>
      <td className="px-3 py-3 text-center">
        <ReminderSwitch
          patient={patient}
          disabled={!props.canManage}
          pending={props.reminderPending}
          onChange={props.onReminderChange}
        />
      </td>
      <td className="px-3 py-3">
        <Badge variant={PATIENT_STATUS_VARIANT[patient.status]}>
          {patient.status_display}
        </Badge>
      </td>
      <td className="px-3 py-3">
        <ActionMenu {...props} />
      </td>
    </tr>
  );
}

export function PatientMobileCard(props: RowProps) {
  const router = useRouter();
  const patient = props.patient;

  return (
    <article className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-primary/20 bg-primary/10 text-xs font-bold text-primary">
            {patientInitials(patient.display_name)}
          </span>
          <div className="min-w-0">
            <button
              type="button"
              onClick={() => router.push(`/dashboard/patients/${patient.id}`)}
              className="block max-w-48 truncate text-left text-sm font-semibold text-foreground"
            >
              {patient.display_name}
            </button>
            <p className="mt-1 text-[10px] text-muted-foreground">
              {patient.masked_cpf}
            </p>
          </div>
        </div>
        <ActionMenu {...props} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="text-[9px] font-semibold uppercase text-muted-foreground">
            Idade
          </p>
          <p className="mt-1 text-foreground">
            {typeof patient.age === "number" ? `${patient.age} anos` : "Não informada"}
          </p>
        </div>
        <div>
          <p className="text-[9px] font-semibold uppercase text-muted-foreground">
            Pagador
          </p>
          <p className="mt-1 truncate text-foreground">
            {patientPayerLabel(patient)}
          </p>
        </div>
        <div className="col-span-2 min-w-0">
          <p className="text-[9px] font-semibold uppercase text-muted-foreground">
            Contato
          </p>
          <p className="mt-1 truncate text-foreground">
            {patient.phone || "Telefone não informado"}
          </p>
          <p className="mt-1 truncate text-[10px] text-muted-foreground">
            {patient.email || "E-mail não informado"}
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
        <Badge variant={PATIENT_STATUS_VARIANT[patient.status]}>
          {patient.status_display}
        </Badge>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-muted-foreground">Lembrete</span>
          <ReminderSwitch
            patient={patient}
            disabled={!props.canManage}
            pending={props.reminderPending}
            onChange={props.onReminderChange}
          />
        </div>
      </div>
    </article>
  );
}
