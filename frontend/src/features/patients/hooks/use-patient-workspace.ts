"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import type { PatientToolbarFilters } from "../components/patient-toolbar";
import type { PatientStatus } from "../types";

const defaults: PatientToolbarFilters = {
  search: "",
  status: "all",
  modality: "",
  payerType: "",
  tag: "",
  noNextSession: false,
};

export function usePatientWorkspaceState() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [filters, setFilters] = useState<PatientToolbarFilters>(() => ({
    ...defaults,
    search: searchParams.get("search") ?? "",
    status: (searchParams.get("status") as PatientStatus | null) ?? "all",
    modality: searchParams.get("modality") ?? "",
    payerType: searchParams.get("payer_type") ?? "",
    tag: searchParams.get("tag") ?? "",
    noNextSession: searchParams.get("no_next_session") === "true",
  }));
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search);
  const [page, setPage] = useState(Number(searchParams.get("page") || 1));
  const [selectedId, setSelectedId] = useState<number | undefined>(() => {
    const value = Number(searchParams.get("patient"));
    return Number.isFinite(value) && value > 0 ? value : undefined;
  });
  const [advancedOpen, setAdvancedOpen] = useState(false);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedSearch(filters.search.trim());
      setPage(1);
    }, 350);
    return () => window.clearTimeout(timeout);
  }, [filters.search]);

  const queryFilters = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      status: filters.status === "all" ? undefined : filters.status,
      modality: filters.modality || undefined,
      payerType: filters.payerType || undefined,
      tag: filters.tag || undefined,
      noNextSession: filters.noNextSession || undefined,
      page,
      pageSize: 6,
    }),
    [debouncedSearch, filters, page],
  );

  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.search) params.set("search", filters.search);
    if (filters.status !== "all") params.set("status", filters.status);
    if (filters.modality) params.set("modality", filters.modality);
    if (filters.payerType) params.set("payer_type", filters.payerType);
    if (filters.tag) params.set("tag", filters.tag);
    if (filters.noNextSession) params.set("no_next_session", "true");
    if (page > 1) params.set("page", String(page));
    if (selectedId) params.set("patient", String(selectedId));
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }, [filters, page, pathname, router, selectedId]);

  return {
    filters,
    setFilters: (next: PatientToolbarFilters) => {
      setFilters(next);
      setPage(1);
    },
    queryFilters,
    page,
    setPage,
    selectedId,
    setSelectedId,
    advancedOpen,
    toggleAdvanced: () => setAdvancedOpen((current) => !current),
  };
}
