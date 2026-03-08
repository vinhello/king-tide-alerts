import { useEffect, useState } from "react";
import {
  Shield,
  Users,
  Bell,
  Calendar,
  Send,
  LogOut,
  Activity,
  CheckCircle,
  XCircle,
} from "lucide-react";
import {
  LineChart,
  BarChart,
  XAxis,
  YAxis,
  Tooltip,
  Line,
  Bar,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import {
  getAdminHealth,
  getSubscriberStats,
  getNotificationStats,
  getAdminEvents,
  sendTestAlert,
} from "../services/api";
import type {
  SystemHealth,
  SubscriberStats,
  NotificationStats,
  AdminEvent,
} from "../types";

const SESSION_KEY = "adminApiKey";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface StatCardProps {
  label: string;
  value: number | string;
  sub?: string;
}

function StatCard({ label, value, sub }: StatCardProps) {
  return (
    <div className="bg-card rounded-xl shadow-sm border border-border p-6">
      <p className="text-sm text-muted-foreground mb-1">{label}</p>
      <p className="text-3xl font-semibold text-foreground">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

interface SectionProps {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}

function Section({ icon, title, children }: SectionProps) {
  return (
    <section aria-labelledby={`section-${title.replace(/\s+/g, "-").toLowerCase()}`}>
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h2
          id={`section-${title.replace(/\s+/g, "-").toLowerCase()}`}
          className="text-lg font-semibold text-foreground"
        >
          {title}
        </h2>
      </div>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Login gate
// ---------------------------------------------------------------------------

interface LoginFormProps {
  onLogin: (key: string) => void;
  loginError: string;
  loginLoading: boolean;
}

function LoginForm({ onLogin, loginError, loginLoading }: LoginFormProps) {
  const [inputKey, setInputKey] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onLogin(inputKey.trim());
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="bg-card rounded-xl shadow-sm border border-border p-8 w-full max-w-sm">
        <div className="flex items-center gap-2 mb-6">
          <Shield className="h-6 w-6 text-primary" aria-hidden="true" />
          <h1 className="text-xl font-semibold text-foreground">Admin Login</h1>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label
              htmlFor="admin-api-key"
              className="block text-sm font-medium text-foreground mb-1"
            >
              API Key
            </label>
            <input
              id="admin-api-key"
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              placeholder="Enter admin API key"
              required
              autoComplete="current-password"
              className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {loginError && (
            <p role="alert" className="text-destructive text-sm mb-4">
              {loginError}
            </p>
          )}

          <button
            type="submit"
            disabled={loginLoading || !inputKey.trim()}
            className="w-full py-2 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loginLoading ? "Verifying..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Health banner
// ---------------------------------------------------------------------------

interface HealthBannerProps {
  health: SystemHealth;
}

function HealthBanner({ health }: HealthBannerProps) {
  return (
    <div className="bg-card rounded-xl shadow-sm border border-border p-4 flex flex-wrap gap-4 items-center text-sm">
      <div className="flex items-center gap-2">
        <span
          className={`inline-block w-2.5 h-2.5 rounded-full ${
            health.scheduler_running ? "bg-green-500" : "bg-red-500"
          }`}
          aria-hidden="true"
        />
        <span className="text-foreground font-medium">
          Scheduler: {health.scheduler_running ? "Running" : "Stopped"}
        </span>
      </div>

      <div className="text-muted-foreground">
        Environment:{" "}
        <span className="text-foreground font-medium capitalize">{health.environment}</span>
      </div>

      {health.next_run_time && (
        <div className="text-muted-foreground">
          Next run:{" "}
          <span className="text-foreground font-medium">{formatDateTime(health.next_run_time)}</span>
        </div>
      )}

      {health.latest_event_at && (
        <div className="text-muted-foreground">
          Latest event:{" "}
          <span className="text-foreground font-medium">{formatDate(health.latest_event_at)}</span>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Subscriber stats section
// ---------------------------------------------------------------------------

interface SubscriberSectionProps {
  stats: SubscriberStats;
}

function SubscriberSection({ stats }: SubscriberSectionProps) {
  return (
    <Section
      icon={<Users className="h-5 w-5 text-primary" aria-hidden="true" />}
      title="Subscriber Stats"
    >
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <StatCard label="Total subscribers" value={stats.total} />
        <StatCard label="Confirmed" value={stats.confirmed} />
        <StatCard label="Unconfirmed" value={stats.unconfirmed} />
        <StatCard label="Email only" value={stats.email_only} />
        <StatCard label="SMS only" value={stats.sms_only} />
        <StatCard label="Email + SMS" value={stats.both} />
      </div>

      {stats.growth.length > 0 && (
        <div className="bg-card rounded-xl shadow-sm border border-border p-6">
          <p className="text-sm font-medium text-foreground mb-4">30-day subscriber growth</p>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={stats.growth} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickFormatter={(v: string) =>
                  new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                }
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                allowDecimals={false}
              />
              <Tooltip
                labelFormatter={(label) =>
                  typeof label === "string"
                    ? new Date(label).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })
                    : String(label)
                }
                contentStyle={{
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="var(--primary)"
                strokeWidth={2}
                dot={false}
                name="Subscribers"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Notification stats section
// ---------------------------------------------------------------------------

interface NotificationSectionProps {
  stats: NotificationStats;
}

function NotificationSection({ stats }: NotificationSectionProps) {
  return (
    <Section
      icon={<Bell className="h-5 w-5 text-primary" aria-hidden="true" />}
      title="Notification History"
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total sent" value={stats.total_sent} />
        <StatCard label="7-day alerts" value={stats.seven_day_alerts} />
        <StatCard label="48-hour reminders" value={stats.forty_eight_hour_reminders} />
        <StatCard label="Confirmations" value={stats.confirmations} />
      </div>

      {stats.daily_counts.length > 0 && (
        <div className="bg-card rounded-xl shadow-sm border border-border p-6 mb-6">
          <p className="text-sm font-medium text-foreground mb-4">30-day daily notification volume</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.daily_counts} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickFormatter={(v: string) =>
                  new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                }
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                allowDecimals={false}
              />
              <Tooltip
                labelFormatter={(label) =>
                  typeof label === "string"
                    ? new Date(label).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })
                    : String(label)
                }
                contentStyle={{
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="count" fill="var(--primary)" name="Notifications" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {stats.recent.length > 0 && (
        <div className="bg-card rounded-xl shadow-sm border border-border overflow-hidden">
          <p className="text-sm font-medium text-foreground px-6 py-4 border-b border-border">
            Recent notifications (last 20)
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th scope="col" className="text-left px-6 py-3 text-muted-foreground font-medium">
                    Subscriber
                  </th>
                  <th scope="col" className="text-left px-6 py-3 text-muted-foreground font-medium">
                    Type
                  </th>
                  <th scope="col" className="text-left px-6 py-3 text-muted-foreground font-medium">
                    Sent at
                  </th>
                </tr>
              </thead>
              <tbody>
                {stats.recent.map((item) => (
                  <tr key={item.id} className="border-b border-border last:border-0">
                    <td className="px-6 py-3 text-foreground">{item.subscriber_name}</td>
                    <td className="px-6 py-3 text-muted-foreground capitalize">
                      {item.notification_type.replace(/_/g, " ")}
                    </td>
                    <td className="px-6 py-3 text-muted-foreground">
                      {formatDateTime(item.sent_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Upcoming events section
// ---------------------------------------------------------------------------

interface EventsSectionProps {
  events: AdminEvent[];
}

function EventsSection({ events }: EventsSectionProps) {
  return (
    <Section
      icon={<Calendar className="h-5 w-5 text-primary" aria-hidden="true" />}
      title="Upcoming Events"
    >
      {events.length === 0 ? (
        <p className="text-muted-foreground text-sm">No upcoming events on record.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {events.map((event) => (
            <div
              key={event.id}
              className="bg-card rounded-xl shadow-sm border border-border p-4 sm:p-5"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {formatDateTime(event.event_datetime)}
                  </p>
                  <p className="text-2xl font-semibold text-foreground mt-0.5">
                    {event.predicted_height.toFixed(1)} ft
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {event.notifications_sent} notification
                    {event.notifications_sent !== 1 ? "s" : ""} sent
                  </p>
                </div>

                <div className="flex flex-col gap-2 text-sm sm:items-end">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">7-day alert:</span>
                    {event.seven_day_alert_sent ? (
                      <CheckCircle
                        className="h-4 w-4 text-green-600"
                        aria-label="Sent"
                      />
                    ) : (
                      <span className="text-muted-foreground" aria-label="Not sent">
                        —
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">48-hour alert:</span>
                    {event.forty_eight_hour_alert_sent ? (
                      <CheckCircle
                        className="h-4 w-4 text-green-600"
                        aria-label="Sent"
                      />
                    ) : (
                      <span className="text-muted-foreground" aria-label="Not sent">
                        —
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Test alert form
// ---------------------------------------------------------------------------

interface TestAlertFormProps {
  apiKey: string;
}

function TestAlertForm({ apiKey }: TestAlertFormProps) {
  const [height, setHeight] = useState("6.8");
  const [daysUntil, setDaysUntil] = useState("7");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setResult("");
    setError("");
    setSending(true);

    const parsedHeight = parseFloat(height);
    const parsedDays = parseInt(daysUntil, 10);

    if (isNaN(parsedHeight) || isNaN(parsedDays)) {
      setError("Please enter valid numeric values.");
      setSending(false);
      return;
    }

    try {
      const response = await sendTestAlert(apiKey, parsedHeight, parsedDays);
      setResult(response.message);
    } catch {
      setError("Failed to send test alert. Check the API key and try again.");
    } finally {
      setSending(false);
    }
  }

  return (
    <Section
      icon={<Send className="h-5 w-5 text-primary" aria-hidden="true" />}
      title="Send Test Alert"
    >
      <div className="bg-card rounded-xl shadow-sm border border-border p-6">
        <form onSubmit={handleSubmit} noValidate>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label
                htmlFor="test-height"
                className="block text-sm font-medium text-foreground mb-1"
              >
                Tide height (ft)
              </label>
              <input
                id="test-height"
                type="number"
                step="0.1"
                min="0"
                value={height}
                onChange={(e) => setHeight(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div>
              <label
                htmlFor="test-days-until"
                className="block text-sm font-medium text-foreground mb-1"
              >
                Days until tide
              </label>
              <input
                id="test-days-until"
                type="number"
                step="1"
                min="1"
                value={daysUntil}
                onChange={(e) => setDaysUntil(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={sending}
            className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {sending ? "Sending..." : "Send test alert"}
          </button>

          {result && (
            <p role="status" className="mt-3 text-sm text-green-700 dark:text-green-400">
              {result}
            </p>
          )}
          {error && (
            <p role="alert" className="mt-3 text-sm text-destructive">
              {error}
            </p>
          )}
        </form>
      </div>
    </Section>
  );
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

interface DashboardData {
  health: SystemHealth;
  subscriberStats: SubscriberStats;
  notificationStats: NotificationStats;
  events: AdminEvent[];
}

interface DashboardProps {
  apiKey: string;
  onLogout: () => void;
}

function Dashboard({ apiKey, onLogout }: DashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchAll() {
      setLoading(true);
      setError("");
      try {
        const [health, subscriberStats, notificationStats, events] = await Promise.all([
          getAdminHealth(apiKey),
          getSubscriberStats(apiKey),
          getNotificationStats(apiKey),
          getAdminEvents(apiKey),
        ]);
        if (!cancelled) {
          setData({ health, subscriberStats, notificationStats, events });
        }
      } catch {
        if (!cancelled) {
          setError("Failed to load dashboard data. Your session may have expired.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchAll();

    return () => {
      cancelled = true;
    };
  }, [apiKey]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-5xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-foreground">King Tide Admin</h1>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            aria-label="Log out"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Log out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div
              className="h-8 w-8 rounded-full border-4 border-primary/30 border-t-primary animate-spin"
              role="status"
              aria-label="Loading dashboard"
            />
          </div>
        ) : error ? (
          <div
            className="flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
            role="alert"
          >
            <XCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            {error}
          </div>
        ) : data ? (
          <div className="flex flex-col gap-10">
            <HealthBanner health={data.health} />
            <SubscriberSection stats={data.subscriberStats} />
            <NotificationSection stats={data.notificationStats} />
            <EventsSection events={data.events} />
            <TestAlertForm apiKey={apiKey} />
          </div>
        ) : null}
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function Admin() {
  const [apiKey, setApiKey] = useState<string>(() => {
    return sessionStorage.getItem(SESSION_KEY) ?? "";
  });
  const [authenticated, setAuthenticated] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // Auto-login on mount if key is already in sessionStorage
  useEffect(() => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) {
      attemptLogin(stored);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function attemptLogin(key: string) {
    setLoginLoading(true);
    setLoginError("");
    try {
      await getAdminHealth(key);
      sessionStorage.setItem(SESSION_KEY, key);
      setApiKey(key);
      setAuthenticated(true);
    } catch {
      setLoginError("Invalid API key. Please try again.");
      sessionStorage.removeItem(SESSION_KEY);
    } finally {
      setLoginLoading(false);
    }
  }

  function handleLogout() {
    sessionStorage.removeItem(SESSION_KEY);
    setApiKey("");
    setAuthenticated(false);
    setLoginError("");
  }

  if (!authenticated) {
    return (
      <LoginForm
        onLogin={attemptLogin}
        loginError={loginError}
        loginLoading={loginLoading}
      />
    );
  }

  return <Dashboard apiKey={apiKey} onLogout={handleLogout} />;
}
