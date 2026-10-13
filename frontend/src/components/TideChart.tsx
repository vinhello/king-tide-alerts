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
  OBSERVED_DAYS,
  UPCOMING_DAYS,
  type ChartDataPoint,
} from "./tideChartData";

const PREDICTED_COLOR = "#0A7EA4";
const OBSERVED_COLOR = "#0D9488";

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
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [hasObserved, setHasObserved] = useState(false);
  const [threshold, setThreshold] = useState(6.0);
  const [kingTideHeight, setKingTideHeight] = useState(6.5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchTides() {
      try {
        // The chart still renders when only the predictions load.
        const [upcoming, observed] = await Promise.all([
          getUpcomingTides(UPCOMING_DAYS),
          getObservedTides(OBSERVED_DAYS).catch(() => null),
        ]);
        setThreshold(upcoming.threshold);
        setKingTideHeight(upcoming.king_tide_height);
        setHasObserved((observed?.observations.length ?? 0) > 0);
        setData(buildChartData(upcoming.predictions, observed));
      } catch {
        setError("Unable to load tide data");
      } finally {
        setLoading(false);
      }
    }
    fetchTides();
  }, []);

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

  const now = Date.now();
  const startTimestamp = data.length > 0 ? data[0].timestamp : now;
  const endTimestamp = data.length > 0 ? data[data.length - 1].timestamp : now;

  return (
    <div className="w-full">
      <div className="mb-4">
        <h2 className="text-xl sm:text-2xl mb-1">Tides</h2>
        <p className="text-xs sm:text-sm text-muted-foreground">
          {hasObserved
            ? `Measured at the gauge for the past ${OBSERVED_DAYS} days, predicted for the next ${UPCOMING_DAYS}. `
            : `Predicted for the next ${UPCOMING_DAYS} days. `}
          {formatRangeDate(startTimestamp)} – {formatRangeDate(endTimestamp)}
        </p>
      </div>

      <div className="bg-card rounded-lg border border-border p-3 sm:p-4">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
            <XAxis
              dataKey="timestamp"
              type="number"
              scale="time"
              domain={["dataMin", "dataMax"]}
              tickFormatter={formatTickDate}
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              label={{ value: 'Height (ft)', angle: -90, position: 'insideLeft', style: { fill: '#64748B', fontSize: 10 } }}
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickLine={{ stroke: '#e5e7eb' }}
              domain={[-1, 8]}
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
                const label = name === 'observed' ? 'Observed (gauge)' : 'Predicted';
                return [`${value.toFixed(1)} ft`, label];
              }}
            />
            <ReferenceLine
              y={threshold}
              stroke="#FB923C"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: `Flooding Risk (${threshold} ft)`,
                position: 'right',
                fill: '#FB923C',
                fontSize: 10,
              }}
            />
            <ReferenceLine
              y={kingTideHeight}
              stroke="#DC2626"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: `King Tide (${kingTideHeight} ft)`,
                position: 'right',
                fill: '#DC2626',
                fontSize: 10,
              }}
            />
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
                stroke={OBSERVED_COLOR}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: OBSERVED_COLOR }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-muted-foreground">
            {hasObserved && (
              <div className="flex items-center gap-2">
                <div className="h-0.5 w-6" style={{ borderTop: `2px solid ${OBSERVED_COLOR}` }} />
                <span>Observed (NOAA gauge)</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-6" style={{ borderTop: `2px solid ${PREDICTED_COLOR}` }} />
              <span>Predicted</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-6" style={{ borderTop: '2px dashed #FB923C' }} />
              <span>Possible bike path flooding</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-0.5 w-6" style={{ borderTop: '2px dashed #DC2626' }} />
              <span>King tide</span>
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
