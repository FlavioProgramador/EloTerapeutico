/**
 * Skeleton – Componente de loading state estruturado.
 * Substitui spinners genéricos por placeholders que preservam o layout da página.
 * Acessível: usa role="status" e aria-label para leitores de tela.
 */

import React from "react";

interface SkeletonProps {
  className?: string;
  /** Número de linhas a renderizar (para listas) */
  lines?: number;
}

function SkeletonBase({ className = "" }: { className?: string }) {
  return (
    <div
      role="status"
      aria-label="Carregando..."
      className={`animate-pulse rounded-md bg-muted/60 ${className}`}
    />
  );
}

/** Linha de texto genérica */
export function SkeletonText({ className = "" }: SkeletonProps) {
  return <SkeletonBase className={`h-4 w-full ${className}`} />;
}

/** Card skeleton */
export function SkeletonCard({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`rounded-lg border border-border/50 p-4 space-y-3 bg-card ${className}`}
      aria-label="Carregando conteúdo..."
      role="status"
    >
      <SkeletonBase className="h-4 w-2/3" />
      <SkeletonBase className="h-3 w-full" />
      <SkeletonBase className="h-3 w-4/5" />
    </div>
  );
}

/** Linha de tabela skeleton */
export function SkeletonTableRow() {
  return (
    <div className="flex gap-4 py-3 border-b border-border/40 items-center" role="status">
      <SkeletonBase className="h-8 w-8 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-1.5">
        <SkeletonBase className="h-3.5 w-40" />
        <SkeletonBase className="h-3 w-24" />
      </div>
      <SkeletonBase className="h-6 w-16 rounded-full" />
      <SkeletonBase className="h-6 w-20" />
    </div>
  );
}

interface SkeletonTableProps {
  lines?: number;
  rows?: number;
  columns?: number;
}

/** Lista de n linhas de tabela */
export function SkeletonTable({ lines, rows, columns }: SkeletonTableProps) {
  const count = lines ?? rows ?? 5;
  return (
    <div className="space-y-0">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonTableRow key={i} />
      ))}
    </div>
  );
}

/** KPI / Stat card skeleton */
export function SkeletonStat() {
  return (
    <div
      className="rounded-lg border border-border/50 p-4 space-y-2 bg-card"
      role="status"
      aria-label="Carregando indicador..."
    >
      <SkeletonBase className="h-3 w-24" />
      <SkeletonBase className="h-7 w-32" />
      <SkeletonBase className="h-3 w-20" />
    </div>
  );
}

/** Bloco de formulário skeleton */
export function SkeletonForm({ lines = 3 }: SkeletonProps) {
  return (
    <div className="space-y-4" role="status" aria-label="Carregando formulário...">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="space-y-1.5">
          <SkeletonBase className="h-3 w-24" />
          <SkeletonBase className="h-10 w-full rounded-md" />
        </div>
      ))}
    </div>
  );
}

// Export default para uso simples
export const Skeleton = SkeletonBase;
