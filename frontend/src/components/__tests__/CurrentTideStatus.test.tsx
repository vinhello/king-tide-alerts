import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import CurrentTideStatus from "../CurrentTideStatus";

vi.mock("../../services/api", () => ({
  getCurrentTideStatus: vi.fn(),
}));

import { getCurrentTideStatus } from "../../services/api";

const safeTideData = {
  current_height: 2.3,
  current_time: "2026-03-08T10:00:00",
  next_high_tide_time: "2026-03-08T14:30:00",
  next_high_tide_height: 5.1,
  hours_until_high_tide: 4.5,
  status: "safe" as const,
  threshold: 6.0,
};

const floodedTideData = {
  current_height: 6.9,
  current_time: "2026-03-08T10:00:00",
  next_high_tide_time: null,
  next_high_tide_height: null,
  hours_until_high_tide: null,
  status: "flooded" as const,
  threshold: 6.0,
};

describe("CurrentTideStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    vi.mocked(getCurrentTideStatus).mockReturnValue(new Promise(() => {})); // Never resolves
    render(<CurrentTideStatus />);
    expect(screen.getByLabelText(/loading current tide status/i)).toBeInTheDocument();
  });

  it("renders safe status with 'Safe to Ride'", async () => {
    vi.mocked(getCurrentTideStatus).mockResolvedValueOnce(safeTideData);
    render(<CurrentTideStatus />);

    await waitFor(() => {
      expect(screen.getByText("Safe to Ride")).toBeInTheDocument();
    });

    expect(screen.getByText("2.3 ft")).toBeInTheDocument();
    expect(screen.getByText(/4\.5 hours/i)).toBeInTheDocument();
  });

  it("renders flooded status with 'Path Flooded'", async () => {
    vi.mocked(getCurrentTideStatus).mockResolvedValueOnce(floodedTideData);
    render(<CurrentTideStatus />);

    await waitFor(() => {
      expect(screen.getByText("Path Flooded")).toBeInTheDocument();
    });

    expect(screen.getByText("6.9 ft")).toBeInTheDocument();
  });

  it("renders nothing on error", async () => {
    vi.mocked(getCurrentTideStatus).mockRejectedValueOnce(new Error("Network error"));
    const { container } = render(<CurrentTideStatus />);

    await waitFor(() => {
      // After error resolves, loading spinner is gone
      expect(container.querySelector('[aria-label="Loading current tide status"]')).toBeNull();
    });

    // Component renders nothing on error
    expect(container.firstChild).toBeNull();
  });
});
