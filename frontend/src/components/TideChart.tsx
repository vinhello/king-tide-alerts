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
  height: number;
  isKingTide: boolean;
}

export default function TideChart() {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [threshold, setThreshold] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchTides() {
      try {
        const response = await getUpcomingTides(14);
        setThreshold(response.threshold);
        setData(
          response.predictions.map((p: TidePrediction) => ({
            date: new Date(p.datetime).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            }),
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
      <section className="tide-chart">
        <h2>Upcoming High Tides</h2>
        <p className="loading">Loading tide data...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="tide-chart">
        <h2>Upcoming High Tides</h2>
        <p className="error-message">{error}</p>
      </section>
    );
  }

  return (
    <section className="tide-chart">
      <h2>Upcoming High Tides</h2>
      <p className="chart-subtitle">
        San Francisco / Golden Gate — height above Mean Higher High Water (ft)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" stroke="#718096" fontSize={12} />
          <YAxis stroke="#718096" fontSize={12} />
          <Tooltip />
          <ReferenceLine
            y={threshold}
            stroke="#e53e3e"
            strokeDasharray="5 5"
            label={{ value: "King Tide Threshold", fill: "#e53e3e", fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="height"
            stroke="#2b6cb0"
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
                    r={5}
                    fill="#e53e3e"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                );
              }
              return (
                <circle
                  key={`dot-${cx}-${cy}`}
                  cx={cx}
                  cy={cy}
                  r={3}
                  fill="#2b6cb0"
                />
              );
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
