export type FormFieldType =
  | "short_text"
  | "long_text"
  | "number"
  | "date"
  | "select"
  | "radio"
  | "checkbox"
  | "scale"
  | "heading";
export type FormCategory =
  | "anamnese"
  | "avaliacao"
  | "evolucao"
  | "escalas"
  | "questionario"
  | "outro";
export type FormStatus = "active" | "archived";

export interface FormFieldConfig {
  options?: string[];
  max_length?: number;
  rows?: number;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  min_label?: string;
  max_label?: string;
  default_value?: string | number;
  allow_other?: boolean;
  allow_future?: boolean;
  allow_past?: boolean;
  visual_size?: "small" | "medium" | "large";
}

export interface FormField {
  id?: number | string;
  type: FormFieldType;
  label: string;
  placeholder?: string;
  help_text?: string;
  required?: boolean;
  order: number;
  is_visible?: boolean;
  internal_id?: string;
  config: FormFieldConfig;
}

export interface TherapeuticForm {
  id: number;
  name: string;
  description: string;
  category: FormCategory;
  category_display: string;
  status: FormStatus;
  status_display: string;
  source_template?: number | null;
  fields_count: number;
  fields: FormField[];
  created_by_name: string;
  updated_by_name: string;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FormTemplate {
  id: number;
  name: string;
  description: string;
  category: FormCategory;
  category_display: string;
  icon: string;
  fields_schema: FormField[];
  fields_count: number;
  is_system_template: boolean;
  is_active: boolean;
}

export interface PaginatedForms<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FormFilters {
  search?: string;
  status?: string;
  category?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface FormPayload {
  name: string;
  description?: string;
  category: FormCategory;
  fields: FormField[];
}
