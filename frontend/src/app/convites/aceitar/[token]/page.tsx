"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, Loader2 } from "lucide-react";

import { useAuth } from "@/contexts/auth";
import { useOrganization } from "@/contexts/organization";
import { api } from "@/lib/api";

export default function AcceptInvitationPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const { refreshOrganizations } = useOrganization();
  const [accepting, setAccepting] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState("");

  if (isLoading) {
    return (
      <main className="grid min-h-screen place-items-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </main>
    );
  }

  if (!isAuthenticated) {
    router.replace(
      `/login?next=${encodeURIComponent(`/convites/aceitar/${params.token}`)}`,
    );
    return null;
  }

  return (
    <main className="grid min-h-screen place-items-center bg-background p-4 text-foreground">
      <section className="w-full max-w-md rounded-2xl border border-border bg-card p-7 text-center shadow-sm">
        <CheckCircle2 className="mx-auto h-10 w-10 text-primary" />
        <h1 className="mt-4 text-xl font-bold">Convite para organização</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          O convite será validado pelo e-mail da sua conta e poderá ser usado somente uma vez.
        </p>
        {completed ? (
          <button
            type="button"
            onClick={() => router.replace("/onboarding")}
            className="mt-6 h-10 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground"
          >
            Continuar configuração
          </button>
        ) : (
          <button
            type="button"
            disabled={accepting}
            onClick={async () => {
              setAccepting(true);
              setError("");
              try {
                await api.post("organizations/invitations/accept/", {
                  token: params.token,
                });
                await refreshOrganizations();
                setCompleted(true);
              } catch {
                setError(
                  "O convite é inválido, expirou ou pertence a outro e-mail.",
                );
              } finally {
                setAccepting(false);
              }
            }}
            className="mt-6 inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-60"
          >
            {accepting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Aceitar convite
          </button>
        )}
        {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
      </section>
    </main>
  );
}
