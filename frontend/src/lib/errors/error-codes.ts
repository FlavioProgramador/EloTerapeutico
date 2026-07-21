export const PUBLIC_ERROR_MESSAGES: Readonly<Record<string, string>> = {
  AUTH_INVALID_CREDENTIALS: "E-mail ou senha inválidos.",
  AUTH_SESSION_EXPIRED: "Sua sessão expirou. Entre novamente.",
  PERMISSION_DENIED: "Você não tem permissão para realizar esta ação.",
  NOT_FOUND: "O conteúdo solicitado não foi encontrado.",
  PATIENT_NOT_FOUND: "O paciente não foi encontrado.",
  APPOINTMENT_CONFLICT: "Já existe um compromisso nesse horário.",
  CHANNEL_NOT_AVAILABLE: "Este canal está temporariamente indisponível.",
  INVALID_INPUT: "Revise as informações preenchidas.",
  RATE_LIMITED: "Muitas tentativas foram realizadas. Aguarde e tente novamente.",
  SERVICE_UNAVAILABLE: "O serviço está temporariamente indisponível. Tente novamente mais tarde.",
};

export const HTTP_PUBLIC_MESSAGES: Readonly<Record<number, string>> = {
  400: "Revise as informações preenchidas.",
  401: "Sua sessão expirou. Entre novamente.",
  403: "Você não tem permissão para realizar esta ação.",
  404: "O conteúdo solicitado não foi encontrado.",
  409: "Não foi possível concluir porque os dados foram alterados ou estão em conflito.",
  422: "Revise os campos destacados e tente novamente.",
  429: "Muitas tentativas foram realizadas. Aguarde e tente novamente.",
};

export const DEFAULT_PUBLIC_ERROR =
  "Não foi possível concluir a operação. Tente novamente.";
