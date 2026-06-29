"use client";

import { useParams } from "next/navigation";
import { RecordWorkspace } from "@/features/records/components/record-workspace";

export default function RecordDetailPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = Number(params.patientId);

  return <RecordWorkspace patientId={patientId} />;
}
