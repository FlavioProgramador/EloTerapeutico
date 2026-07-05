import type { PaginatedResponse } from "@/types";

export type DocumentTemplateStatus = "active" | "inactive" | "archived";
export type DocumentType =
  | "declaration"
  | "report"
  | "referral"
  | "certificate"
  | "consent"
  | "other";

export interface DocumentTemplate {
  public_id: string;
  name: string;
  description: string;
  category: string;
  document_type: DocumentType;
  document_type_display: string;
  specialty: string;
  content?: string;
  content_preview?: string;
  header_content?: string;
  footer_content?: string;
  include_professional_identification: boolean;
  include_clinic_identification: boolean;
  requires_signature: boolean;
  status: DocumentTemplateStatus;
  status_display: string;
  version: number;
  usage_count: number;
  author_name?: string;
  source_library_public_id?: string | null;
  is_library_template: boolean;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface DocumentTemplatePayload {
  name: string;
  description?: string;
  category: string;
  document_type: DocumentType;
  specialty?: string;
  content: string;
  header_content?: string;
  footer_content?: string;
  include_professional_identification?: boolean;
  include_clinic_identification?: boolean;
  requires_signature?: boolean;
  status?: DocumentTemplateStatus;
}

export type GeneratedDocumentStatus =
  | "draft"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled"
  | "archived";

export interface GeneratedDocument {
  public_id: string;
  document_number: string;
  title: string;
  patient: number;
  patient_name: string;
  professional_name: string;
  document_type: DocumentType;
  document_type_display: string;
  category: string;
  status: GeneratedDocumentStatus;
  status_display: string;
  generated_at?: string | null;
  created_at: string;
  updated_at: string;
  download_url?: string | null;
  template_public_id?: string | null;
  template_name?: string;
  template_version_snapshot?: number;
  content?: string;
  pdf_hash?: string;
  signature_hash?: string;
  professional_registration_snapshot?: string;
  signed_at?: string | null;
  failure_reason?: string;
  archived_at?: string | null;
}

export interface PlaceholderDefinition {
  key: string;
  token: string;
  label: string;
  group: string;
  description: string;
}

export interface EvolutionTemplate {
  id: number;
  name: string;
  description: string;
  category: string;
  specialty: string;
  content: string;
  content_preview: string;
  owner?: number | null;
  owner_name?: string;
  is_system: boolean;
  is_active: boolean;
  sort_order: number;
  usage_count: number;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EvolutionTemplatePayload {
  name: string;
  description?: string;
  category?: string;
  specialty?: string;
  content: string;
  is_active?: boolean;
  sort_order?: number;
}

export interface DocumentFilters {
  search?: string;
  status?: string;
  category?: string;
  document_type?: string;
  specialty?: string;
  patient?: number;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export type PaginatedTemplates = PaginatedResponse<DocumentTemplate>;
export type PaginatedGeneratedDocuments = PaginatedResponse<GeneratedDocument>;
