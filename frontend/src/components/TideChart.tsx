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
import type { TidePrediction } from "../types";
import { getUpcomingTides } from "../services/api";

interface ChartDataPoint {
  date: string;
  dateLabel: string;
  height: number;
  isKingTide: boolean;
}

export default function TideChart() {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [threshold, setThreshold] = useState(6.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchTides() {
      try {
        const response = await getUpcomingTides(14);
        setThreshold(response.threshold);
        setData(
          response.predictions.map((p: TidePrediction, index: number) => ({
            date: p.datetime,
            dateLabel: index % 4 === 0 ? new Date(p.datetime).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            }) : "",
            height: p.height,
            isKingTide: p.is_king_tide,
          }))
        );
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
        <h2 className="text-xl sm:text-2xl mb-4">Upcoming Tides</h2>
        <div className="bg-card rounded-lg border border-border p-6 sm:p-8">
          <p className="text-muted-foreground text-center">Loading tide data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full">
        <h2 className="text-xl sm:text-2xl mb-4">Upcoming Tides</h2>
        <div className="bg-card rounded-lg border border-border p-6 sm:p-8">
          <p className="text-destructive text-center">{error}</p>
        </div>
      </div>
    );
  }

  const startDate = data.length > 0 ? new Date(data[0].date) : new Date();
  const endDate = data.length > 0 ? new Date(data[data.length - 1].date) : new Date();

  return (
    <div className="w-full">
      <div className="mb-4">
        <h2 className="text-xl sm:text-2xl mb-1">Upcoming Tides</h2>
        <p className="text-xs sm:text-sm text-muted-foreground">
          {startDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })} - {endDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
        </p>
      </div>

      <div className="bg-card rounded-lg border border-border p-3 sm:p-4">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
            <XAxis
              dataKey="dateLabel"
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              label={{ value: 'Height (ft)', angle: -90, position: 'insideLeft', style: { fill: '#64748B', fontSize: 10 } }}
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickLine={{ stroke: '#e5e7eb' }}
              domain={[0, 8]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelFormatter={(_, payload) => {
                if (payload && payload[0]) {
                  return new Date(payload[0].payload.date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                  });
                }
                return '';
              }}
  formatter={(value, name) => {
                if (name === 'height' && typeof value === 'number') {
                  return [`${value.toFixed(1)} ft`, 'Tide Height'];
                }
                return String(value);
              }}
            />
            <ReferenceLine
              y={threshold}
              stroke="#FB923C"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: `Alert Level (${threshold} ft)`,
                position: 'right',
                fill: '#FB923C',
                fontSize: 10,
              }}
            />
            <Line
              type="monotone"
              dataKey="height"
              stroke="#0A7EA4"
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
              activeDot={{ r: 6, fill: '#0A7EA4' }}
            />
          </LineChart>
        </ResponsiveContainer>

        <div className="mt-4 flex items-center gap-4 text-xs sm:text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-[#0A7EA4]" />
            <span>Normal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-[#FB923C]" />
            <span>Alert Level</span>
          </div>
        </div>
      </div>
    </div>
  );
}
