import axios from "axios";
import type {
  CheckoutSessionResponse,
  ConfirmResponse,
  SubscribeRequest,
  SubscriberResponse,
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
