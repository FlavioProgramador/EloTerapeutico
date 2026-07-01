import { Camera, UserRound, X } from "lucide-react";
import type { ChangeEvent } from "react";

interface Props {
  preview: string | null;
  current: string | null;
  error?: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onRemove: () => void;
}

function sanitizeImageSrc(
  value: string | null,
  expectedPreview: string | null,
): string | null {
  if (!value) return null;

  const candidate = value.trim();
  if (!candidate) return null;

  try {
    const parsed = new URL(candidate);

    if (parsed.protocol === "blob:") {
      return expectedPreview && candidate === expectedPreview ? candidate : null;
    }

    if (parsed.protocol === "https:" || parsed.protocol === "http:") {
      return parsed.toString();
    }
  } catch {
    return null;
  }

  return null;
}

export function PatientPhotoField(props: Props) {
  const photoSrc = sanitizeImageSrc(
    props.preview || props.current,
    props.preview,
  );

  return (
    <div className="flex items-center gap-4 sm:col-span-2">
      <div className="relative grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-full border border-border bg-primary/10 text-primary">
        {photoSrc ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={photoSrc}
            alt="Foto do paciente"
            className="h-full w-full object-cover"
          />
        ) : (
          <UserRound className="h-7 w-7" />
        )}
        <label className="absolute bottom-0 right-0 grid h-6 w-6 cursor-pointer place-items-center rounded-full bg-primary text-primary-foreground shadow">
          <Camera className="h-3 w-3" />
          <span className="sr-only">Selecionar foto</span>
          <input
            type="file"
            accept="image/jpeg,image/png"
            className="sr-only"
            onChange={props.onChange}
          />
        </label>
      </div>
      <div className="text-[11px] text-muted-foreground">
        <p className="font-medium text-foreground">Foto do paciente (opcional)</p>
        <p className="mt-1">JPG ou PNG, até 2 MB.</p>
        {photoSrc && (
          <button
            type="button"
            onClick={props.onRemove}
            className="mt-2 inline-flex items-center gap-1 text-destructive hover:underline"
          >
            <X className="h-3 w-3" /> Remover foto
          </button>
        )}
        {props.error && (
          <p className="mt-1 text-destructive" role="alert">
            {props.error}
          </p>
        )}
      </div>
    </div>
  );
}
