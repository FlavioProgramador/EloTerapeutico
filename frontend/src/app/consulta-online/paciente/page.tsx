import type { Metadata } from "next";

import { PatientTelemedicineFlow } from "@/features/telemedicine/components/patient-telemedicine-flow";

export const metadata: Metadata = {
  title: "Atendimento online | Elo Terapêutico",
  description: "Acesso protegido ao atendimento online.",
  robots: { index: false, follow: false, noarchive: true },
  referrer: "no-referrer",
};

export default function PatientOnlineConsultationPage() {
  return <PatientTelemedicineFlow />;
}
