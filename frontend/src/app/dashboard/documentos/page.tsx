import { Suspense } from "react";
import { DocumentsWorkspace } from "@/features/documents/components/documents-workspace";

export default function DocumentsPage() {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-xl bg-secondary" />}>
      <DocumentsWorkspace />
    </Suspense>
  );
}
