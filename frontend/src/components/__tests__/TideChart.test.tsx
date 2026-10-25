import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import TideChart from "../TideChart";

// Mock recharts to avoid SVG rendering issues in jsdom
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: ({ dataKey }: { dataKey: string }) => <div data-testid="line" data-key={dataKey} />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ReferenceLine: () => <div data-testid="reference-line" />,
}));

vi.mock("../../services/api", () => ({
  getUpcomingTides: vi.fn(),
  getObservedTides: vi.fn(),
}));

import { getObservedTides, getUpcomingTides } from "../../services/api";

const upcoming = {
  predictions: [
    { datetime: "2026-02-10 01:00", height: 1.84, type: "H", is_king_tide: true },
    { datetime: "2026-02-10 14:00", height: 0.52, type: "H", is_king_tide: false },
  ],
  threshold: 1.0,
  king_tide_height: 1.5,
  station_id: "9414290",
};

const nothingObserved = {
  observations: [],
  predictions: [],
  days: 2,
  as_of: "",
  station_id: "9414290",
};

const observed = {
  observations: [
    { datetime: "2026-02-09 10:00", height: 2.1 },
    { datetime: "2026-02-09 11:00", height: 2.4 },
  ],
  predictions: [
    { datetime: "2026-02-09 10:00", height: 1.6 },
    { datetime: "2026-02-09 11:00", height: 1.9 },
  ],
  days: 2,
  as_of: "2026-02-09 11:00",
  station_id: "9414290",
};

describe("TideChart", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getObservedTides).mockResolvedValue(nothingObserved);
  });

  it("renders loading state", () => {
    vi.mocked(getUpcomingTides).mockReturnValue(new Promise(() => {})); // Never resolves
    render(<TideChart />);
    expect(screen.getByText(/loading tide data/i)).toBeInTheDocument();
  });

  it("renders the predicted chart when nothing has been observed", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValueOnce(upcoming);

    render(<TideChart />);

    await waitFor(() => {
      expect(screen.getByTestId("line-chart")).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "Tides" })).toBeInTheDocument();
    expect(getUpcomingTides).toHaveBeenLastCalledWith(5);
    expect(screen.getByText("Predicted")).toBeInTheDocument();
    expect(screen.getAllByTestId("line")).toHaveLength(1);
    expect(screen.queryByText(/measured at the gauge/i)).not.toBeInTheDocument();
    // Flooding and king tide thresholds only; no "Now" marker without observations
    expect(screen.getAllByTestId("reference-line")).toHaveLength(2);
  });

  it("draws the measured line and the Now marker when the gauge has data", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValueOnce(upcoming);
    vi.mocked(getObservedTides).mockResolvedValueOnce(observed);

    render(<TideChart />);

    await waitFor(() => {
      expect(screen.getByText("Measured at the gauge")).toBeInTheDocument();
    });

    const lines = screen.getAllByTestId("line").map((el) => el.getAttribute("data-key"));
    expect(lines).toEqual(["predicted", "observed"]);
    expect(screen.getAllByTestId("reference-line")).toHaveLength(3);
    expect(screen.getByText("Path starts flooding (1.0 ft)")).toBeInTheDocument();
    expect(screen.getByText("Deeper flooding (1.5 ft)")).toBeInTheDocument();
  });

  it("still renders predictions when the observed fetch fails", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValueOnce(upcoming);
    vi.mocked(getObservedTides).mockRejectedValueOnce(new Error("NOAA down"));

    render(<TideChart />);

    await waitFor(() => {
      expect(screen.getByTestId("line-chart")).toBeInTheDocument();
    });

    expect(screen.queryByText(/unable to load/i)).not.toBeInTheDocument();
    expect(screen.getAllByTestId("line")).toHaveLength(1);
  });

  it("switches to the 14-day view and refetches both series", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValue(upcoming);
    vi.mocked(getObservedTides).mockResolvedValue(observed);

    render(<TideChart />);
    await waitFor(() => {
      expect(screen.getByText("Measured at the gauge")).toBeInTheDocument();
    });
    expect(getUpcomingTides).toHaveBeenLastCalledWith(5);
    expect(getObservedTides).toHaveBeenLastCalledWith(2);

    fireEvent.click(screen.getByRole("button", { name: "14 days" }));

    await waitFor(() => {
      expect(getObservedTides).toHaveBeenLastCalledWith(3);
    });
    expect(getUpcomingTides).toHaveBeenLastCalledWith(11);
    expect(screen.getByRole("button", { name: "14 days" })).toHaveAttribute("aria-pressed", "true");
  });

  it("renders Add to Calendar link", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValueOnce(upcoming);

    render(<TideChart />);

    await waitFor(() => {
      expect(screen.getByText(/add to calendar/i)).toBeInTheDocument();
    });

    const link = screen.getByRole("link", { name: /add to calendar/i });
    expect(link).toHaveAttribute("download", "king-tide-alerts.ics");
  });
});
