import { render, screen, waitFor } from "@testing-library/react";
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
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ReferenceLine: () => <div data-testid="reference-line" />,
}));

vi.mock("../../services/api", () => ({
  getUpcomingTides: vi.fn(),
}));

import { getUpcomingTides } from "../../services/api";

describe("TideChart", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    vi.mocked(getUpcomingTides).mockReturnValue(new Promise(() => {})); // Never resolves
    render(<TideChart />);
    expect(screen.getByText(/loading tide data/i)).toBeInTheDocument();
  });

  it("renders chart with tide data", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValueOnce({
      predictions: [
        { datetime: "2026-02-10 01:41", height: 1.84, type: "H", is_king_tide: true },
        { datetime: "2026-02-10 14:23", height: 0.52, type: "H", is_king_tide: false },
      ],
      threshold: 1.0,
      king_tide_height: 1.5,
      station_id: "9414290",
    });

    render(<TideChart />);

    await waitFor(() => {
      expect(screen.getByTestId("line-chart")).toBeInTheDocument();
    });

    expect(screen.getByText(/upcoming tides/i)).toBeInTheDocument();
  });

  it("shows king tide threshold line", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValueOnce({
      predictions: [
        { datetime: "2026-02-10 01:41", height: 1.84, type: "H", is_king_tide: true },
      ],
      threshold: 1.0,
      king_tide_height: 1.5,
      station_id: "9414290",
    });

    render(<TideChart />);

    await waitFor(() => {
      const referenceLines = screen.getAllByTestId("reference-line");
      expect(referenceLines).toHaveLength(2);
    });
  });

  it("renders Add to Calendar link", async () => {
    vi.mocked(getUpcomingTides).mockResolvedValueOnce({
      predictions: [
        { datetime: "2026-02-10 01:41", height: 1.84, type: "H", is_king_tide: true },
      ],
      threshold: 1.0,
      king_tide_height: 1.5,
      station_id: "9414290",
    });

    render(<TideChart />);

    await waitFor(() => {
      expect(screen.getByText(/add to calendar/i)).toBeInTheDocument();
    });

    const link = screen.getByRole("link", { name: /add to calendar/i });
    expect(link).toHaveAttribute("download", "king-tide-alerts.ics");
  });
});
