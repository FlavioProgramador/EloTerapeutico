"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  buildPatientListParams,
  EMPTY_PATIENT_FILTERS,
  patientFiltersFromUrl,
} from "../components/patient-list-config";

export function usePatientReferenceFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const url = useSearchParams();
  const initialFilters = useMemo(
    () => patientFiltersFromUrl(new URLSearchParams(url.toString())),
    [url],
  );
  const [search, setSearch] = useState(url.get("search") ?? "");
  const [debouncedSearch, setDebouncedSearch] = useState(search);
  const [draftFilters, setDraftFilters] = useState(initialFilters);
  const [filters, setFilters] = useState(initialFilters);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [birthdaysOnly, setBirthdaysOnly] = useState(
    url.get("birthdays") === "true",
  );
  const [page, setPage] = useState(Math.max(1, Number(url.get("page") || 1)));
  const [pageSize, setPageSize] = useState(
    Math.max(5, Number(url.get("page_size") || 10)),
  );

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(1);
    }, 350);
    return () => window.clearTimeout(timeout);
  }, [search]);

  const params = useMemo(
    () =>
      buildPatientListParams(
        debouncedSearch,
        filters,
        page,
        pageSize,
        birthdaysOnly,
      ),
    [birthdaysOnly, debouncedSearch, filters, page, pageSize],
  );

  useEffect(() => {
    const visible = new URLSearchParams(params);
    const rename = (from: string, to: string, value: string) => {
      visible.delete(from);
      if (value) visible.set(to, value);
    };
    rename("created_at_gte", "created_from", filters.createdFrom);
    rename("created_at_lte", "created_to", filters.createdTo);
    rename("birth_date_gte", "birth_from", filters.birthFrom);
    rename("birth_date_lte", "birth_to", filters.birthTo);
    if (page === 1) visible.delete("page");
    if (pageSize === 10) visible.delete("page_size");
    const query = visible.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  }, [filters, page, pageSize, params, pathname, router]);

  const clearFilters = () => {
    setDraftFilters(EMPTY_PATIENT_FILTERS);
    setFilters(EMPTY_PATIENT_FILTERS);
    setBirthdaysOnly(false);
    setPage(1);
  };

  return {
    search,
    setSearch,
    debouncedSearch,
    draftFilters,
    setDraftFilters,
    filters,
    setFilters,
    filtersOpen,
    setFiltersOpen,
    birthdaysOnly,
    setBirthdaysOnly,
    page,
    setPage,
    pageSize,
    setPageSize,
    params,
    clearFilters,
  };
}
