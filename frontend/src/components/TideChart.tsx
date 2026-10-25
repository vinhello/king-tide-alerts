import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { CalendarDays } from "lucide-react";
import { getObservedTides, getUpcomingTides } from "../services/api";
import { EVENTS, trackEvent } from "../services/analytics";
import {
  buildChartData,
  WINDOWS,
  type ChartDataPoint,
  type WindowKey,
} from "./tideChartData";

// Measured water is the ground truth, so it wears the ink color; the
// prediction keeps the site blue. The two never read alike, for any color
// vision, and the dashed thresholds are a third style again.
const MEASURED_COLOR = "#1C1917";
const PREDICTED_COLOR = "#0A7EA4";

function formatTickDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatTooltipDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatRangeDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export default function TideChart() {
  const [windowKey, setWindowKey] = useState<WindowKey>("week");
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [hasObserved, setHasObserved] = useState(false);
  const [threshold, setThreshold] = useState(6.0);
  const [kingTideHeight, setKingTideHeight] = useState(6.5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { observedDays, upcomingDays } = WINDOWS[windowKey];

  useEffect(() => {
    let cancelled = false;

    async function fetchTides() {
      try {
        // The chart still renders when only the predictions load.
        const [upcoming, observed] = await Promise.all([
          getUpcomingTides(upcomingDays),
          getObservedTides(observedDays).catch(() => null),
        ]);
        if (cancelled) return;
        setThreshold(upcoming.threshold);
        setKingTideHeight(upcoming.king_tide_height);
        setHasObserved((observed?.observations.length ?? 0) > 0);
        setData(buildChartData(upcoming.predictions, observed));
        setError("");
      } catch {
        if (!cancelled) setError("Unable to load tide data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchTides();

    return () => {
      cancelled = true;
    };
  }, [observedDays, upcomingDays]);

  const now = Date.now();
  const startTimestamp = data.length > 0 ? data[0].timestamp : now;
  const endTimestamp = data.length > 0 ? data[data.length - 1].timestamp : now;

  const windowButtons = (
    <div className="flex items-center gap-2" role="group" aria-label="Chart range">
      {(Object.keys(WINDOWS) as WindowKey[]).map((key) => (
        <button
          key={key}
          type="button"
          onClick={() => setWindowKey(key)}
          aria-pressed={windowKey === key}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors border ${
            windowKey === key
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-card text-muted-foreground border-border hover:text-foreground hover:border-primary/50"
          }`}
        >
          {WINDOWS[key].label}
        </button>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="w-full">
        <h2 className="text-xl sm:text-2xl mb-4">Tides</h2>
        <div className="bg-card rounded-lg border border-border p-6 sm:p-8">
          <p className="text-muted-foreground text-center">Loading tide data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full">
        <h2 className="text-xl sm:text-2xl mb-4">Tides</h2>
        <div className="bg-card rounded-lg border border-border p-6 sm:p-8">
          <p className="text-destructive text-center">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl mb-1">Tides</h2>
          <p className="text-xs sm:text-sm text-muted-foreground">
            {hasObserved
              ? `Measured at the gauge for the past ${observedDays} days, predicted for the next ${upcomingDays}. `
              : `Predicted for the next ${upcomingDays} days. `}
            {formatRangeDate(startTimestamp)} – {formatRangeDate(endTimestamp)}
          </p>
        </div>
        {windowButtons}
      </div>

      <div className="bg-card rounded-lg border border-border p-3 sm:p-4">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 12, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
            <XAxis
              dataKey="timestamp"
              type="number"
              scale="time"
              domain={["dataMin", "dataMax"]}
              tickFormatter={formatTickDate}
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickLine={{ stroke: '#e5e7eb' }}
              minTickGap={40}
            />
            <YAxis
              label={{ value: 'Height (ft)', angle: -90, position: 'insideLeft', style: { fill: '#64748B', fontSize: 10 } }}
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickLine={{ stroke: '#e5e7eb' }}
              domain={[-2, 8]}
              ticks={[-2, 0, 2, 4, 6, 8]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelFormatter={(value) => formatTooltipDate(value as number)}
              formatter={(value, name) => {
                if (typeof value !== 'number') return String(value);
                const label = name === 'observed' ? 'Measured' : 'Predicted';
                return [`${value.toFixed(1)} ft`, label];
              }}
            />
            <ReferenceLine y={threshold} stroke="#FB923C" strokeDasharray="5 5" strokeWidth={2} />
            <ReferenceLine y={kingTideHeight} stroke="#DC2626" strokeDasharray="5 5" strokeWidth={2} />
            {hasObserved && (
              <ReferenceLine
                x={now}
                stroke="#64748B"
                strokeDasharray="3 3"
                label={{ value: 'Now', position: 'top', fill: '#64748B', fontSize: 10 }}
              />
            )}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke={PREDICTED_COLOR}
              strokeWidth={2}
              dot={(props: Record<string, unknown>) => {
                const { cx, cy, payload } = props as {
                  cx: number;
                  cy: number;
                  payload: ChartDataPoint;
                };
                if (payload.isKingTide) {
                  return (
                    <circle
                      key={`dot-${cx}-${cy}`}
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill="#FB923C"
                      stroke="#FB923C"
                      strokeWidth={2}
                    />
                  );
                }
                return null;
              }}
              activeDot={{ r: 4, fill: PREDICTED_COLOR }}
            />
            {hasObserved && (
              <Line
                type="monotone"
                dataKey="observed"
                stroke={MEASURED_COLOR}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 4, fill: MEASURED_COLOR }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-muted-foreground">
            {hasObserved && (
              <div className="flex items-center gap-2">
                <div className="h-0.5 w-6" style={{ borderTop: `3px solid ${MEASURED_COLOR}` }} />
                <span>Measured at the gauge</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-6" style={{ borderTop: `2px solid ${PREDICTED_COLOR}` }} />
              <span>Predicted</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-6" style={{ borderTop: '2px dashed #FB923C' }} />
              <span>Possible bike path flooding ({threshold.toFixed(1)} ft)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-6" style={{ borderTop: '2px dashed #DC2626' }} />
              <span>High chance of flooding ({kingTideHeight.toFixed(1)} ft)</span>
            </div>
          </div>
          <a
            href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/tides/calendar.ics`}
            download="king-tide-alerts.ics"
            onClick={() => trackEvent(EVENTS.calendarDownload)}
            className="inline-flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
          >
            <CalendarDays className="h-4 w-4" />
            Add to Calendar
          </a>
        </div>
      </div>
    </div>
  );
}
