import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import History from "../History";

vi.mock("../../services/api", () => ({
  getEventHistory: vi.fn(),
  createCheckoutSession: vi.fn(),
}));

import { getEventHistory } from "../../services/api";

const sampleEvent = {
  id: "abc-123",
  event_datetime: "2026-01-15T09:30:00",
  predicted_height: 6.8,
  is_king_tide: true,
  seven_day_alert_sent: true,
  forty_eight_hour_alert_sent: true,
  notifications_sent: 42,
};

const sampleResponse = {
  events: [sampleEvent],
  total: 1,
  threshold: 6.0,
  king_tide_height: 6.5,
};

describe("History", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    vi.mocked(getEventHistory).mockReturnValue(new Promise(() => {})); // Never resolves
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );
    expect(screen.getByLabelText(/loading/i)).toBeInTheDocument();
  });

  it("renders events with data", async () => {
    vi.mocked(getEventHistory).mockResolvedValueOnce(sampleResponse);
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("6.8 ft")).toBeInTheDocument();
    });

    expect(screen.getByText("King Tide")).toBeInTheDocument();
    // The per-event send count is intentionally not shown to visitors.
    expect(screen.queryByText(/notifications? sent/i)).not.toBeInTheDocument();
  });

  it("renders empty state", async () => {
    vi.mocked(getEventHistory).mockResolvedValueOnce({
      events: [],
      total: 0,
      threshold: 6.0,
      king_tide_height: 6.5,
    });
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no tide events recorded yet/i)).toBeInTheDocument();
    });
  });

  it("renders filter buttons", () => {
    vi.mocked(getEventHistory).mockReturnValue(new Promise(() => {}));
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    expect(screen.getByRole("button", { name: /^all$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /upcoming/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /past/i })).toBeInTheDocument();
  });
});

describe("History dates", () => {
  it("shows the station's date for an early-morning tide", async () => {
    // 7:50 AM Pacific on Friday Dec 4, as the API sends it. Read in a
    // Pacific browser's own zone this used to show Thursday Dec 3.
    vi.mocked(getEventHistory).mockResolvedValue({
      ...sampleResponse,
      events: [{ ...sampleEvent, event_datetime: "2026-12-04T07:50:00+00:00" }],
    });
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Fri, Dec 4, 2026")).toBeInTheDocument();
    });
  });
});
