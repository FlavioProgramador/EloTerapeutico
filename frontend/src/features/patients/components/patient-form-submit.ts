import type { PatientFormData } from "../schemas/patient.schemas";
import type { PatientFormRequest } from "../types/patient-form.types";
import { currencyToDecimal } from "./patient-form-formatters";

export function toPatientRequest(data: PatientFormData): PatientFormRequest {
  const {
    photo: _photo,
    address_zip_code,
    address_street,
    address_number,
    address_complement,
    address_neighborhood,
    address_city,
    address_state,
    tags,
    session_value,
    therapist,
    treatment_start_date,
    birth_date,
    cpf,
    ...rest
  } = data;
  return {
    ...rest,
    full_name: data.full_name.trim().replace(/\s+/g, " "),
    email: data.email?.trim().toLowerCase() || "",
    // Datas: enviar null quando vazio para evitar erro 400 com string vazia
    birth_date: birth_date || undefined,
    treatment_start_date: treatment_start_date || null,
    // CPF: enviar apenas se preenchido (o backend aceita CPF opcional)
    cpf: cpf ? cpf.trim() : undefined,
    session_value: currencyToDecimal(session_value),
    therapist: therapist ? Number(therapist) : undefined,
    insurance_name: data.payer_type === "insurance" ? data.insurance_name : "",
    tags: tags ? tags.split(",").map((tag) => tag.trim()).filter(Boolean) : [],
    address: {
      zip_code: address_zip_code || undefined,
      street: address_street || undefined,
      number: address_number || undefined,
      complement: address_complement || undefined,
      neighborhood: address_neighborhood || undefined,
      city: address_city || undefined,
      state: address_state || undefined,
    },
  };
}


export function toPatientMultipart(request: PatientFormRequest, photo: File) {
  const form = new FormData();
  Object.entries(request).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (Array.isArray(value)) {
      value.forEach((item) => form.append(key, String(item)));
    } else if (typeof value === "object") {
      form.append(key, JSON.stringify(value));
    } else {
      form.append(key, String(value));
    }
  });
  form.set("photo", photo);
  return form;
}
