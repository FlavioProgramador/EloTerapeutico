import type { PatientDashboardItem, PatientStatus } from "../types";

export interface PatientPageData {
  pagination: {
    count: number;
    current_page: number;
    total_pages: number;
    next: string | null;
    previous: string | null;
  };
  results: PatientDashboardItem[];
}

export type BooleanFilter = "" | "true" | "false";

export interface PatientListFilters {
  status: "" | PatientStatus;
  therapist: string;
  modality: string;
  attendanceType: string;
  payerType: string;
  insurance: string;
  tag: string;
  createdFrom: string;
  createdTo: string;
  birthFrom: string;
  birthTo: string;
  noNextSession: boolean;
  hasAnamnesis: BooleanFilter;
  remindersEnabled: BooleanFilter;
}

export const EMPTY_PATIENT_FILTERS: PatientListFilters = {
  status: "",
  therapist: "",
  modality: "",
  attendanceType: "",
  payerType: "",
  insurance: "",
  tag: "",
  createdFrom: "",
  createdTo: "",
  birthFrom: "",
  birthTo: "",
  noNextSession: false,
  hasAnamnesis: "",
  remindersEnabled: "",
};

export const PATIENT_STATUS_VARIANT = {
  active: "success",
  evaluation: "warning",
  waiting_return: "outline",
  discharged: "primary",
  inactive: "muted",
  archived: "muted",
} as const;

export const PATIENT_FILTER_SELECTS = [
  {
    key: "status",
    label: "Status",
    options: [
      ["", "Todos"],
      ["active", "Ativo"],
      ["evaluation", "Em avaliação"],
      ["waiting_return", "Aguardando retorno"],
      ["discharged", "Alta"],
      ["inactive", "Encerrado"],
      ["archived", "Arquivado"],
    ],
  },
  {
    key: "modality",
    label: "Modalidade",
    options: [
      ["", "Todas"],
      ["in_person", "Presencial"],
      ["online", "Online"],
      ["hybrid", "Híbrido"],
    ],
  },
  {
    key: "attendanceType",
    label: "Tipo de atendimento",
    options: [
      ["", "Todos"],
      ["individual", "Individual"],
      ["couple", "Casal"],
      ["family", "Familiar"],
      ["group", "Grupo"],
      ["other", "Outro"],
    ],
  },
  {
    key: "payerType",
    label: "Tipo de pagador",
    options: [
      ["", "Todos"],
      ["private", "Particular"],
      ["insurance", "Convênio"],
    ],
  },
  {
    key: "hasAnamnesis",
    label: "Anamnese",
    options: [
      ["", "Todos"],
      ["true", "Com anamnese"],
      ["false", "Sem anamnese"],
    ],
  },
  {
    key: "remindersEnabled",
    label: "Lembretes",
    options: [
      ["", "Todos"],
      ["true", "Ativados"],
      ["false", "Desativados"],
    ],
  },
] as const;

export function patientInitials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function patientPayerLabel(patient: PatientDashboardItem) {
  return patient.payer_type === "insurance"
    ? patient.insurance_name || "Convênio não informado"
    : "Particular";
}

export function countPatientFilters(
  filters: PatientListFilters,
  birthdaysOnly: boolean,
) {
  return (
    Object.values(filters).filter((value) => value !== "" && value !== false)
      .length + Number(birthdaysOnly)
  );
}

export function buildPatientListParams(
  search: string,
  filters: PatientListFilters,
  page: number,
  pageSize: number,
  birthdaysOnly: boolean,
) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  const entries: Array<[string, string | boolean]> = [
    ["search", search],
    ["status", filters.status],
    ["therapist", filters.therapist],
    ["modality", filters.modality],
    ["attendance_type", filters.attendanceType],
    ["payer_type", filters.payerType],
    ["insurance", filters.insurance],
    ["tag", filters.tag],
    ["birth_date_gte", filters.birthFrom],
    ["birth_date_lte", filters.birthTo],
    ["no_next_session", filters.noNextSession],
    ["has_anamnesis", filters.hasAnamnesis],
    ["reminders_enabled", filters.remindersEnabled],
    ["birthdays", birthdaysOnly],
  ];
  entries.forEach(([key, value]) => {
    if (value !== "" && value !== false) params.set(key, String(value));
  });
  if (filters.createdFrom) {
    params.set("created_at_gte", `${filters.createdFrom}T00:00:00`);
  }
  if (filters.createdTo) {
    params.set("created_at_lte", `${filters.createdTo}T23:59:59`);
  }
  return params;
}

export function patientFiltersFromUrl(
  params: URLSearchParams,
): PatientListFilters {
  return {
    status: (params.get("status") as PatientStatus | null) ?? "",
    therapist: params.get("therapist") ?? "",
    modality: params.get("modality") ?? "",
    attendanceType: params.get("attendance_type") ?? "",
    payerType: params.get("payer_type") ?? "",
    insurance: params.get("insurance") ?? "",
    tag: params.get("tag") ?? "",
    createdFrom: params.get("created_from") ?? "",
    createdTo: params.get("created_to") ?? "",
    birthFrom: params.get("birth_from") ?? "",
    birthTo: params.get("birth_to") ?? "",
    noNextSession: params.get("no_next_session") === "true",
    hasAnamnesis: (params.get("has_anamnesis") as BooleanFilter | null) ?? "",
    remindersEnabled:
      (params.get("reminders_enabled") as BooleanFilter | null) ?? "",
  };
}
