import { useEffect, useState } from "react";
import { Clock, CheckCircle, Loader2 } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { getEventHistory } from "../services/api";
import type { HistoryEvent, HistoryResponse } from "../types";

type FilterOption = "all" | "upcoming" | "past";

const PER_PAGE = 50;

function formatEventDate(datetime: string): string {
  return new Date(datetime).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function heightColorClass(height: number, kingTideHeight: number, threshold: number): string {
  if (height >= kingTideHeight) return "text-destructive";
  if (height >= threshold) return "text-accent";
  return "text-muted-foreground";
}

interface EventCardProps {
  event: HistoryEvent;
  threshold: number;
  kingTideHeight: number;
}

function EventCard({ event, threshold, kingTideHeight }: EventCardProps) {
  const heightClass = heightColorClass(event.predicted_height, kingTideHeight, threshold);

  return (
    <div className="bg-card rounded-lg border border-border p-4 sm:p-5">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-foreground">
              {formatEventDate(event.event_datetime)}
            </span>
            {event.is_king_tide && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-destructive/10 text-destructive">
                King Tide
              </span>
            )}
          </div>
          <span className={`text-2xl font-medium ${heightClass}`}>
            {event.predicted_height.toFixed(1)} ft
          </span>
        </div>

        <div className="flex flex-col gap-2 sm:items-end text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">7-day alert:</span>
            {event.seven_day_alert_sent ? (
              <CheckCircle className="h-4 w-4 text-secondary" aria-label="Sent" />
            ) : (
              <span className="text-muted-foreground" aria-label="Not sent">—</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">48-hour alert:</span>
            {event.forty_eight_hour_alert_sent ? (
              <CheckCircle className="h-4 w-4 text-secondary" aria-label="Sent" />
            ) : (
              <span className="text-muted-foreground" aria-label="Not sent">—</span>
            )}
          </div>
          <div className="text-muted-foreground">
            {event.notifications_sent} notification{event.notifications_sent !== 1 ? "s" : ""} sent
          </div>
        </div>
      </div>
    </div>
  );
}

export default function History() {
  const [filter, setFilter] = useState<FilterOption>("all");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchHistory() {
      setLoading(true);
      setError("");
      try {
        const result = await getEventHistory(page, PER_PAGE, filter);
        if (!cancelled) {
          setData(result);
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load alert history.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchHistory();

    return () => {
      cancelled = true;
    };
  }, [filter, page]);

  const handleFilterChange = (newFilter: FilterOption) => {
    setFilter(newFilter);
    setPage(1);
  };

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;

  const filterButtons: { label: string; value: FilterOption }[] = [
    { label: "All", value: "all" },
    { label: "Upcoming", value: "upcoming" },
    { label: "Past", value: "past" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        <div className="mx-auto max-w-[720px] px-4 py-8 sm:py-12">
          {/* Page header */}
          <div className="text-center mb-8 sm:mb-10">
            <div className="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-primary/10 mb-4">
              <Clock className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
            </div>
            <h1 className="text-2xl sm:text-3xl mb-3">Alert History</h1>
            <p className="text-muted-foreground max-w-lg mx-auto">
              A record of high tide events and the alerts sent to subscribers.
            </p>
          </div>

          {/* Filter buttons */}
          <div className="flex items-center gap-2 mb-6" role="group" aria-label="Filter events">
            {filterButtons.map(({ label, value }) => (
              <button
                key={value}
                onClick={() => handleFilterChange(value)}
                aria-pressed={filter === value}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors border ${
                  filter === value
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-card text-muted-foreground border-border hover:text-foreground hover:border-primary/50"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Loading" />
            </div>
          ) : error ? (
            <p className="text-destructive text-center py-8">{error}</p>
          ) : data && data.events.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No tide events recorded yet.</p>
          ) : (
            <>
              <div className="flex flex-col gap-3">
                {data?.events.map((event: HistoryEvent) => (
                  <EventCard
                    key={event.id}
                    event={event}
                    threshold={data.threshold}
                    kingTideHeight={data.king_tide_height}
                  />
                ))}
              </div>

              {/* Pagination */}
              {data && data.total > PER_PAGE && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 rounded-md text-sm font-medium border border-border bg-card text-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:border-primary/50 transition-colors"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-4 py-2 rounded-md text-sm font-medium border border-border bg-card text-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:border-primary/50 transition-colors"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
