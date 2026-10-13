import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import NwsAdvisoryBanner from "../NwsAdvisoryBanner";

vi.mock("../../services/api", () => ({
  getNwsAlerts: vi.fn(),
}));

import { getNwsAlerts } from "../../services/api";

const advisory = {
  id: "urn:test:advisory",
  event: "Coastal Flood Advisory",
  severity: "Minor",
  headline: "Coastal Flood Advisory issued October 13 at 4:57AM PDT until October 13 at 3:00PM PDT by NWS San Francisco CA",
  what: "Up to 1.1 ft of inundation above ground level is possible in low-lying areas near shorelines and tidal waterways.",
  where: "San Francisco Bay Shoreline.",
  when: "Until 3 PM PDT Tuesday.",
  impacts: "Flooding of low-lying infrastructure.",
  additional_details: "",
  instruction: "Do not drive around barricades.",
  onset: "2026-10-13T04:57:00-07:00",
  ends: "2026-10-13T15:00:00-07:00",
  sent: "2026-10-13T04:57:00-07:00",
  sender_name: "NWS San Francisco CA",
  zones: ["CAZ508"],
  link: "https://forecast.weather.gov/MapClick.php?zoneid=CAZ508",
};

const warning = { ...advisory, id: "urn:test:warning", event: "Coastal Flood Warning" };

describe("NwsAdvisoryBanner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when no product is in effect", async () => {
    vi.mocked(getNwsAlerts).mockResolvedValueOnce({ alerts: [], zones: ["CAZ508"] });
    const { container } = render(<NwsAdvisoryBanner />);
    await waitFor(() => expect(getNwsAlerts).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when the feed fails", async () => {
    vi.mocked(getNwsAlerts).mockRejectedValueOnce(new Error("down"));
    const { container } = render(<NwsAdvisoryBanner />);
    await waitFor(() => expect(getNwsAlerts).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("quotes the NWS product, attributes it, and links to the source", async () => {
    vi.mocked(getNwsAlerts).mockResolvedValueOnce({ alerts: [advisory], zones: ["CAZ508"] });

    render(<NwsAdvisoryBanner />);

    expect(await screen.findByText("Coastal Flood Advisory")).toBeInTheDocument();
    expect(screen.getByText(/in effect until/i)).toHaveTextContent("Oct 13");
    expect(screen.getByText(/up to 1\.1 ft of inundation/i)).toBeInTheDocument();
    expect(screen.getByText(/issued by NWS San Francisco CA/i)).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /read the advisory/i });
    expect(link).toHaveAttribute("href", advisory.link);
    expect(link).toHaveAttribute("target", "_blank");
    expect(screen.getByRole("status")).toHaveClass("border-l-accent");

    // The remaining NWS text is behind a toggle.
    expect(screen.queryByText(/do not drive around barricades/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /full nws text/i }));
    expect(screen.getByText(/do not drive around barricades/i)).toBeInTheDocument();
    expect(screen.getByText("Until 3 PM PDT Tuesday.")).toBeInTheDocument();
    expect(screen.queryByText("Additional details")).not.toBeInTheDocument();
  });

  it("uses the warning tone for a Coastal Flood Warning and caps at two banners", async () => {
    vi.mocked(getNwsAlerts).mockResolvedValueOnce({
      alerts: [warning, advisory, { ...advisory, id: "urn:test:third" }],
      zones: ["CAZ508"],
    });

    render(<NwsAdvisoryBanner />);

    const banners = await screen.findAllByRole("status");
    expect(banners).toHaveLength(2);
    expect(banners[0]).toHaveClass("border-l-destructive");
    expect(banners[1]).toHaveClass("border-l-accent");
  });
});
