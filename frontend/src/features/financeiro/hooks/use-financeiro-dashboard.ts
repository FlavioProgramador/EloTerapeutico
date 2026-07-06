import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  financeiroDashboardService,
  type CreateMonthlySubscription,
  type MonthlySubscription,
} from "../services/financeiro-dashboard.service";

const DASHBOARD_KEY = ["financeiro", "dashboard"] as const;
const SUBSCRIPTIONS_KEY = ["financeiro", "subscriptions"] as const;

export function useFinanceiroDashboard(startDate: string, endDate: string) {
  return useQuery({
    queryKey: [...DASHBOARD_KEY, startDate, endDate],
    queryFn: () => financeiroDashboardService.summary(startDate, endDate),
  });
}

export function useMonthlySubscriptions(status?: string) {
  return useQuery({
    queryKey: [...SUBSCRIPTIONS_KEY, status],
    queryFn: () => financeiroDashboardService.subscriptions(status),
  });
}

export function useGenerateCharges() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ appointmentIds, dueDate }: { appointmentIds: number[]; dueDate: string }) =>
      financeiroDashboardService.generateCharges(appointmentIds, dueDate),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: DASHBOARD_KEY });
      queryClient.invalidateQueries({ queryKey: ["unbilledAppointments"] });
      toast.success(`${result.created_count} cobrança(s) gerada(s).`);
    },
    onError: () => toast.error("Não foi possível gerar as cobranças."),
  });
}

export function useCreateMonthlySubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateMonthlySubscription) =>
      financeiroDashboardService.createSubscription(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBSCRIPTIONS_KEY });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: DASHBOARD_KEY });
      toast.success("Mensalidade criada com sucesso.");
    },
    onError: () => toast.error("Não foi possível criar a mensalidade."),
  });
}

export function useUpdateMonthlySubscriptionStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: MonthlySubscription["status"] }) =>
      financeiroDashboardService.updateSubscriptionStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBSCRIPTIONS_KEY });
      toast.success("Status da mensalidade atualizado.");
    },
    onError: () => toast.error("Não foi possível atualizar a mensalidade."),
  });
}
