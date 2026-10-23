import type { ObservedTidesResponse, TidePrediction } from "../types";

// Two views: a short one where the two curves read clearly, and a longer one.
export const WINDOWS = {
  week: { label: "7 days", observedDays: 2, upcomingDays: 5 },
  fortnight: { label: "14 days", observedDays: 3, upcomingDays: 11 },
} as const;

export type WindowKey = keyof typeof WINDOWS;

export interface ChartDataPoint {
  timestamp: number;
  date: string;
  predicted?: number;
  observed?: number;
  isKingTide: boolean;
}

function toTimestamp(datetime: string): number {
  return new Date(datetime).getTime();
}

/**
 * One series keyed by hour: NOAA's recent observations and the predictions
 * for the same hours, plus the upcoming predictions. Hours present in both
 * prediction sets carry the same value, so the merge is harmless.
 */
export function buildChartData(
  upcoming: TidePrediction[],
  observed: ObservedTidesResponse | null,
): ChartDataPoint[] {
  const byTime = new Map<number, ChartDataPoint>();
  const pointFor = (datetime: string): ChartDataPoint => {
    const timestamp = toTimestamp(datetime);
    let point = byTime.get(timestamp);
    if (!point) {
      point = { timestamp, date: datetime, isKingTide: false };
      byTime.set(timestamp, point);
    }
    return point;
  };

  for (const p of observed?.predictions ?? []) {
    pointFor(p.datetime).predicted = p.height;
  }
  for (const o of observed?.observations ?? []) {
    pointFor(o.datetime).observed = o.height;
  }
  for (const p of upcoming) {
    const point = pointFor(p.datetime);
    point.predicted = p.height;
    point.isKingTide = p.is_king_tide;
  }

  return [...byTime.values()].sort((a, b) => a.timestamp - b.timestamp);
}
