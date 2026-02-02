export type NotificationPreference = "email" | "sms" | "both";

export interface SubscribeRequest {
  name: string;
  email?: string;
  phone?: string;
  notification_preference: NotificationPreference;
}

export interface SubscriberResponse {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  notification_preference: NotificationPreference;
  confirmed: boolean;
  created_at: string;
}

export interface TidePrediction {
  datetime: string;
  height: number;
  type: string;
  is_king_tide: boolean;
}

export interface UpcomingTidesResponse {
  predictions: TidePrediction[];
  threshold: number;
  station_id: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
}

export interface ConfirmResponse {
  message: string;
}

export interface UnsubscribeResponse {
  message: string;
}
