import { useEffect, useState } from "react";
import { Waves, Clock, Loader2 } from "lucide-react";
import { getCurrentTideStatus } from "../services/api";
import type { CurrentTideStatus as CurrentTideStatusType } from "../types";

const REFRESH_INTERVAL_MS = 360000; // 6 minutes

// The reading comes from the Golden Gate gauge, not from the path itself, so
// the labels state how likely flooding is rather than what the path looks like.
function statusLabel(status: CurrentTideStatusType["status"]): string {
  if (status === "flooded") return "Flooding likely";
  if (status === "caution") return "Flooding possible";
  return "Flooding unlikely";
}

function statusColorClass(status: CurrentTideStatusType["status"]): string {
  if (status === "flooded") return "text-destructive";
  if (status === "caution") return "text-accent";
  return "text-secondary";
}

export default function CurrentTideStatus() {
  const [data, setData] = useState<CurrentTideStatusType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const result = await getCurrentTideStatus();
        setData(result);
        setError(false);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    fetchStatus();

    const interval = setInterval(fetchStatus, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-card rounded-lg border border-border border-l-4 border-l-primary shadow-sm p-4 sm:p-6 flex items-center justify-center">
        <Loader2
          className="h-5 w-5 animate-spin text-muted-foreground"
          aria-label="Loading current tide status"
        />
      </div>
    );
  }

  if (error || !data) {
    return null;
  }

  const colorClass = statusColorClass(data.status);

  return (
    <div className="bg-card rounded-lg border border-border border-l-4 border-l-primary shadow-sm p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6">
        {/* Current height */}
        <div className="flex items-start gap-3">
          <Waves
            className={`h-5 w-5 shrink-0 mt-px ${colorClass}`}
            aria-hidden="true"
          />
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">
              Current Height
            </p>
            <p className={`text-2xl font-medium ${colorClass}`}>
              {data.current_height.toFixed(1)} ft
            </p>
          </div>
        </div>

        {/* Divider */}
        <div
          className="hidden sm:block w-px self-stretch bg-border"
          aria-hidden="true"
        />

        {/* Status badge */}
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">
            Flood Risk Now
          </p>
          <p className={`text-base font-medium ${colorClass}`}>
            {statusLabel(data.status)}
          </p>
        </div>

        {/* Divider */}
        {data.hours_until_high_tide !== null &&
          data.hours_until_high_tide > 0 && (
            <>
              <div
                className="hidden sm:block w-px self-stretch bg-border"
                aria-hidden="true"
              />

              {/* Next high tide ETA */}
              <div className="flex items-start gap-3">
                <Clock
                  className="h-5 w-5 shrink-0 mt-px text-muted-foreground"
                  aria-hidden="true"
                />
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">
                    Next High Tide
                  </p>
                  <p className="text-sm text-foreground">
                    In {data.hours_until_high_tide.toFixed(1)} hours
                    {data.next_high_tide_height !== null && (
                      <span className="text-muted-foreground">
                        {" "}
                        ({data.next_high_tide_height.toFixed(1)} ft)
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </>
          )}
      </div>
      <p className="mt-4 text-xs text-muted-foreground">
        Based on the water level measured at the Golden Gate gauge. Conditions
        on the path can differ.
      </p>
    </div>
  );
}
