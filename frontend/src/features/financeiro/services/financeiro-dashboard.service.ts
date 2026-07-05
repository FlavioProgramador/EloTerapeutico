import { api } from "@/lib/api";

export interface FinancialDashboardSummary {
  start_date: string;
  end_date: string;
  received: string;
  received_count: number;
  receivable: string;
  receivable_count: number;
  payable: string;
  payable_count: number;
  paid_expenses: string;
  paid_expenses_count: number;
  overdue: string;
  overdue_receivable_count: number;
  overdue_payable_count: number;
  projected_balance: string;
}

export interface MonthlySubscription {
  id: number;
  patient: number;
  patient_name: string;
  therapist_name: string;
  status: "active" | "paused" | "ended" | "cancelled";
  status_display: string;
  frequency: "weekly" | "biweekly" | "monthly";
  frequency_display: string;
  weekday: number;
  appointment_time: string;
  first_appointment_date: string;
  duration_minutes: number;
  monthly_amount: string;
  due_day: number;
  next_billing_date?: string | null;
  reminder_days_before?: number | null;
}

export interface CreateMonthlySubscription {
  patient: number;
  frequency: MonthlySubscription["frequency"];
  weekday: number;
  appointment_time: string;
  first_appointment_date: string;
  duration_minutes: number;
  monthly_amount: string;
  due_day: number;
  first_due_date?: string;
  reminder_days_before?: number | null;
  preferred_payment_method?: string;
  payment_link?: string;
  notes?: string;
}

export const financeiroDashboardService = {
  summary: async (startDate: string, endDate: string) => {
    const response = await api.get<FinancialDashboardSummary>("financeiro/summary/", {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },
  generateCharges: async (appointmentIds: number[], dueDate: string) => {
    const response = await api.post("financeiro/generate-monthly-charges/", {
      appointment_ids: appointmentIds,
      due_date: dueDate,
    });
    return response.data as { created_count: number; created: number[]; skipped: number[] };
  },
  subscriptions: async (status?: string) => {
    const response = await api.get<MonthlySubscription[]>("financeiro/subscriptions/", {
      params: status && status !== "all" ? { status } : undefined,
    });
    return response.data;
  },
  createSubscription: async (payload: CreateMonthlySubscription) => {
    const response = await api.post<MonthlySubscription>("financeiro/subscriptions/", payload);
    return response.data;
  },
  updateSubscriptionStatus: async (id: number, status: MonthlySubscription["status"]) => {
    const response = await api.post<MonthlySubscription>(
      `financeiro/subscriptions/${id}/status/`,
      { status },
    );
    return response.data;
  },
};
