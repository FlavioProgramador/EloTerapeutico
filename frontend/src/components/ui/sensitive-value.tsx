"use client";

import { Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SensitiveValueProps {
  maskedValue: string;
  fullValue?: string | null;
  canReveal?: boolean;
  className?: string;
  revealLabel?: string;
}

export function SensitiveValue({
  maskedValue,
  fullValue,
  canReveal = false,
  className,
  revealLabel = "dado",
}: SensitiveValueProps) {
  const [revealed, setRevealed] = useState(false);
  const revealAvailable = Boolean(canReveal && fullValue);

  useEffect(() => () => setRevealed(false), []);

  return (
    <span className={cn("inline-flex min-w-0 items-center gap-2", className)}>
      <span className="min-w-0 truncate">{revealed ? fullValue : maskedValue}</span>
      {revealAvailable && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 shrink-0 px-2 text-xs"
          onClick={() => setRevealed((current) => !current)}
          aria-pressed={revealed}
          aria-label={`${revealed ? "Ocultar" : "Mostrar"} ${revealLabel}`}
        >
          {revealed ? (
            <EyeOff className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Eye className="h-4 w-4" aria-hidden="true" />
          )}
          <span>{revealed ? "Ocultar" : "Mostrar"}</span>
        </Button>
      )}
    </span>
  );
}
