import type { EvolutionPayload, EvolutionWorkspace } from "../../types";
import type {
  EvolutionAppointmentOption,
  EvolutionAttachment,
} from "../../evolution-modal.types";

export interface EvolutionEditorProps {
  open: boolean;
  evolution?: EvolutionWorkspace | null;
  saving: boolean;
  finalizing: boolean;
  onClose: () => void;
  onSave: (payload: EvolutionPayload) => Promise<void>;
  onFinalize: (id: number) => Promise<void>;
}

export type EvolutionWithModalData = EvolutionWorkspace & {
  attachments?: EvolutionAttachment[];
  appointment_data?: EvolutionAppointmentOption | null;
  content_format?: "markdown" | "plain_text";
};

export interface EvolutionEditorFormState {
  appointment: string;
  sessionDate: string;
  content: string;
  confidential: boolean;
  dateOverrideConfirmed: boolean;
}
