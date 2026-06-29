"use client";

import { Suspense } from "react";

import { PatientsWorkspace } from "@/features/patients/components/patients-workspace";

function PatientsPageSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-20 animate-pulse rounded-xl bg-secondary" />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-24 animate-pulse rounded-xl bg-secondary" />
        ))}
      </div>
      <div className="grid gap-4 2xl:grid-cols-[minmax(0,1.85fr)_minmax(20rem,1fr)]">
        <div className="h-[36rem] animate-pulse rounded-xl bg-secondary" />
        <div className="h-[36rem] animate-pulse rounded-xl bg-secondary" />
      </div>
    </div>
  );
}

export default function PatientsListPage() {
  return (
    <Suspense fallback={<PatientsPageSkeleton />}>
      <PatientsWorkspace />
    </Suspense>
  );
}
