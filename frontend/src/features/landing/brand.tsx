import { HeartHandshake } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

interface BrandProps {
  className?: string;
  compact?: boolean;
}

export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-primary/25 bg-primary text-primary-foreground shadow-lg shadow-primary/20",
        className,
      )}
    >
      <HeartHandshake className="h-5 w-5" strokeWidth={1.9} />
    </span>
  );
}

export function Brand({ className, compact = false }: BrandProps) {
  return (
    <Link
      href="/"
      aria-label="Ir para o início do Elo Terapêutico"
      className={cn(
        "inline-flex items-center gap-3 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-4 focus-visible:ring-offset-background",
        className,
      )}
    >
      <BrandMark className={compact ? "h-9 w-9 rounded-lg" : undefined} />
      <span className="flex flex-col leading-none">
        <span className="text-[0.98rem] font-extrabold tracking-[-0.02em] text-foreground sm:text-base">
          Elo Terapêutico
        </span>
        {!compact && (
          <span className="mt-1 text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Gestão clínica
          </span>
        )}
      </span>
    </Link>
  );
}
