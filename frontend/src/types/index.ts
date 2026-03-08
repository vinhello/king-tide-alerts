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
  type?: string;
  is_king_tide: boolean;
}

export interface UpcomingTidesResponse {
  predictions: TidePrediction[];
  threshold: number;
  king_tide_height: number;
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

export interface HistoryEvent {
  id: string;
  event_datetime: string;
  predicted_height: number;
  is_king_tide: boolean;
  seven_day_alert_sent: boolean;
  forty_eight_hour_alert_sent: boolean;
  notifications_sent: number;
}

export interface HistoryResponse {
  events: HistoryEvent[];
  total: number;
  threshold: number;
  king_tide_height: number;
}

export interface CurrentTideStatus {
  current_height: number;
  current_time: string;
  next_high_tide_time: string | null;
  next_high_tide_height: number | null;
  hours_until_high_tide: number | null;
  status: "safe" | "caution" | "flooded";
  threshold: number;
}
