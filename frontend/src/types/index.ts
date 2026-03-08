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

// Admin types
export interface SubscriberStats {
  total: number;
  confirmed: number;
  unconfirmed: number;
  email_only: number;
  sms_only: number;
  both: number;
  growth: GrowthPoint[];
}

export interface GrowthPoint {
  date: string;
  count: number;
}

export interface NotificationStats {
  total_sent: number;
  seven_day_alerts: number;
  forty_eight_hour_reminders: number;
  confirmations: number;
  recent: NotificationHistoryItem[];
  daily_counts: DailyCount[];
}

export interface NotificationHistoryItem {
  id: string;
  subscriber_name: string;
  notification_type: string;
  sent_at: string;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface AdminEvent {
  id: string;
  event_datetime: string;
  predicted_height: number;
  seven_day_alert_sent: boolean;
  forty_eight_hour_alert_sent: boolean;
  notifications_sent: number;
}

export interface SystemHealth {
  scheduler_running: boolean;
  next_run_time: string | null;
  environment: string;
  latest_event_at: string | null;
}

export interface TestAlertResponse {
  message: string;
}
