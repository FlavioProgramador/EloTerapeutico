"use client";

import { useSearchParams } from "next/navigation";

import { DashboardHome } from "@/features/dashboard/dashboard-home";
import { ReportsDashboard } from "@/features/reports/reports-dashboard";

export default function DashboardPage() {
  const searchParams = useSearchParams();
  return searchParams.get("view") === "reports" ? <ReportsDashboard /> : <DashboardHome />;
}
