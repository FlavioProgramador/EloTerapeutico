import { notFound } from "next/navigation";

import { ProfessionalTelemedicineFlow } from "@/features/telemedicine/components/professional-telemedicine-flow";

export default async function ProfessionalOnlineConsultationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const roomId = Number.parseInt(id, 10);
  if (!Number.isInteger(roomId) || roomId <= 0) notFound();
  return <ProfessionalTelemedicineFlow roomId={roomId} />;
}
