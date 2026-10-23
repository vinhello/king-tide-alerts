import { describe, it, expect } from "vitest";
import { buildChartData } from "../tideChartData";

const upcoming = [
  { datetime: "2026-10-13 12:00", height: 5.2, is_king_tide: false },
  { datetime: "2026-10-13 13:00", height: 6.6, is_king_tide: true },
];

describe("buildChartData", () => {
  it("merges observed and predicted values by hour and sorts by time", () => {
    const observed = {
      observations: [
        { datetime: "2026-10-13 11:00", height: 5.9 },
        { datetime: "2026-10-13 10:00", height: 5.4 },
      ],
      predictions: [
        { datetime: "2026-10-13 10:00", height: 4.6 },
        { datetime: "2026-10-13 11:00", height: 5.0 },
      ],
      days: 3,
      as_of: "2026-10-13 11:00",
      station_id: "9414290",
    };

    const data = buildChartData(upcoming, observed);

    expect(data.map((d) => d.date)).toEqual([
      "2026-10-13 10:00",
      "2026-10-13 11:00",
      "2026-10-13 12:00",
      "2026-10-13 13:00",
    ]);
    expect(data[0]).toMatchObject({ observed: 5.4, predicted: 4.6, isKingTide: false });
    expect(data[1]).toMatchObject({ observed: 5.9, predicted: 5.0 });
    expect(data[2]).toMatchObject({ predicted: 5.2 });
    expect(data[2].observed).toBeUndefined();
    expect(data[3]).toMatchObject({ predicted: 6.6, isKingTide: true });
  });

  it("falls back to predictions alone when nothing was observed", () => {
    const data = buildChartData(upcoming, null);
    expect(data).toHaveLength(2);
    expect(data.every((d) => d.observed === undefined)).toBe(true);
  });
});
