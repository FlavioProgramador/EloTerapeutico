import { CircleCheck, ShieldAlert } from "lucide-react";

export function TelemedicineErrorState({ message }: { message: string }) {
  return (
    <div className="py-10 text-center" role="alert">
      <span className="mx-auto grid size-12 place-items-center rounded-full bg-destructive/10 text-destructive">
        <ShieldAlert className="size-5" />
      </span>
      <h2 className="mt-4 text-lg font-bold">Não foi possível acessar a sala</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        {message}
      </p>
      <p className="mt-4 text-xs text-muted-foreground">
        Solicite um novo convite ao profissional quando necessário.
      </p>
    </div>
  );
}

export function TelemedicineEndedState() {
  return (
    <div className="py-10 text-center">
      <span className="mx-auto grid size-12 place-items-center rounded-full bg-emerald-500/10 text-emerald-600">
        <CircleCheck className="size-6" />
      </span>
      <h2 className="mt-4 text-xl font-bold">Atendimento encerrado</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        A câmera, o microfone e as credenciais temporárias foram liberados.
      </p>
    </div>
  );
}
