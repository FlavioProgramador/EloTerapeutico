import Link from "next/link";
import { HeartHandshake } from "lucide-react";
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
        "grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-[hsl(163,27%,62%)]/25 bg-[hsl(165,27%,12%)] text-[hsl(38,25%,87%)] shadow-lg",
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
        "inline-flex items-center gap-3 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(38,25%,87%)] focus-visible:ring-offset-4 focus-visible:ring-offset-[hsl(165,40%,7%)]",
        className,
      )}
    >
      <BrandMark className={compact ? "h-9 w-9 rounded-lg" : undefined} />
      <span className="flex flex-col leading-none">
        <span className="text-[0.98rem] font-extrabold tracking-[-0.02em] text-[hsl(40,20%,94%)] sm:text-base">
          Elo Terapêutico
        </span>
        {!compact && (
          <span className="mt-1 text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-[hsl(163,8%,68%)]">
            Gestão clínica
          </span>
        )}
      </span>
    </Link>
  );
}
