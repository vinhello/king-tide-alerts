import { describe, it, expect, vi, afterEach } from "vitest";
import { EVENTS, trackEvent } from "../analytics";

describe("analytics", () => {
  afterEach(() => {
    delete window.plausible;
  });

  it("does nothing when Plausible is not loaded", () => {
    expect(() => trackEvent(EVENTS.subscribe)).not.toThrow();
  });

  it("forwards the event name and props to Plausible when present", () => {
    window.plausible = vi.fn();
    trackEvent(EVENTS.subscribe, { channel: "email" });
    expect(window.plausible).toHaveBeenCalledWith("Subscribe", { props: { channel: "email" } });
  });

  it("omits the options object when there are no props", () => {
    window.plausible = vi.fn();
    trackEvent(EVENTS.confirm);
    expect(window.plausible).toHaveBeenCalledWith("Confirm", undefined);
  });

  it("swallows errors thrown by Plausible", () => {
    window.plausible = vi.fn(() => {
      throw new Error("blocked");
    });
    expect(() => trackEvent(EVENTS.donateClick)).not.toThrow();
  });
});
