import axios from "axios";
import type {
  AdminEvent,
  CheckoutSessionResponse,
  ConfirmResponse,
  CurrentTideStatus,
  HistoryResponse,
  NotificationStats,
  SubscribeRequest,
  SubscriberResponse,
  SubscriberStats,
  SystemHealth,
  TestAlertResponse,
  UnsubscribeResponse,
  UpcomingTidesResponse,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

export async function subscribe(
  data: SubscribeRequest
): Promise<SubscriberResponse> {
  const response = await api.post<SubscriberResponse>("/api/subscribe", data);
  return response.data;
}

export async function confirmSubscription(
  token: string
): Promise<ConfirmResponse> {
  const response = await api.get<ConfirmResponse>(`/api/confirm/${token}`);
  return response.data;
}

export async function unsubscribe(
  token: string
): Promise<UnsubscribeResponse> {
  const response = await api.get<UnsubscribeResponse>(
    `/api/unsubscribe/${token}`
  );
  return response.data;
}

export async function getUpcomingTides(
  days: number = 14
): Promise<UpcomingTidesResponse> {
  const response = await api.get<UpcomingTidesResponse>(
    `/api/tides/upcoming?days=${days}`
  );
  return response.data;
}

export async function createCheckoutSession(): Promise<CheckoutSessionResponse> {
  const response = await api.post<CheckoutSessionResponse>(
    "/api/stripe/create-checkout-session",
    { amount: 500 }
  );
  return response.data;
}

export async function getEventHistory(
  page: number = 1,
  perPage: number = 50,
  filter: "all" | "upcoming" | "past" = "all"
): Promise<HistoryResponse> {
  const response = await api.get<HistoryResponse>("/api/tides/history", {
    params: { page, per_page: perPage, filter },
  });
  return response.data;
}

export async function getCurrentTideStatus(): Promise<CurrentTideStatus> {
  const response = await api.get<CurrentTideStatus>("/api/tides/current");
  return response.data;
}

function adminHeaders(password: string) {
  return { headers: { "x-admin-password": password } };
}

export async function getAdminHealth(apiKey: string): Promise<SystemHealth> {
  const response = await api.get<SystemHealth>("/api/admin/health", adminHeaders(apiKey));
  return response.data;
}

export async function getSubscriberStats(apiKey: string): Promise<SubscriberStats> {
  const response = await api.get<SubscriberStats>("/api/admin/stats", adminHeaders(apiKey));
  return response.data;
}

export async function getNotificationStats(apiKey: string): Promise<NotificationStats> {
  const response = await api.get<NotificationStats>("/api/admin/notifications", adminHeaders(apiKey));
  return response.data;
}

export async function getAdminEvents(apiKey: string): Promise<AdminEvent[]> {
  const response = await api.get<AdminEvent[]>("/api/admin/events", adminHeaders(apiKey));
  return response.data;
}

export async function sendTestAlert(
  apiKey: string,
  height: number = 6.8,
  daysUntil: number = 7
): Promise<TestAlertResponse> {
  const response = await api.post<TestAlertResponse>(
    `/api/admin/test-alert?height=${height}&days_until=${daysUntil}`,
    null,
    adminHeaders(apiKey)
  );
  return response.data;
}
