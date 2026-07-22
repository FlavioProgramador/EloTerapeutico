import { HeartHandshake } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

interface BrandProps {
  className?: string;
  compact?: boolean;
}

export function BrandMark({ className }: { className?: string }) {
  const isCompact = className?.includes("h-9");
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid h-12 w-12 shrink-0 place-items-center rounded-xl border border-primary/25 bg-primary text-primary-foreground shadow-lg shadow-primary/20",
        className,
      )}
    >
      <HeartHandshake className={cn("h-7 w-7", isCompact && "h-5 w-5")} strokeWidth={1.9} />
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
        <span className="text-lg font-extrabold tracking-[-0.02em] text-primary sm:text-xl">
          Elo Terapêutico
        </span>
        {!compact && (
          <span className="mt-1 text-[0.65rem] font-bold uppercase tracking-[0.25em] text-muted-foreground/80">
            Gestão clínica
          </span>
        )}
      </span>
    </Link>
  );
}
