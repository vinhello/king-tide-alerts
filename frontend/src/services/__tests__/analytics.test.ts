import { describe, it, expect, vi, afterEach } from "vitest";
import { EVENTS, trackEvent } from "../analytics";

describe("analytics", () => {
  afterEach(() => {
    delete window.posthog;
  });

  it("does nothing when PostHog is not loaded", () => {
    expect(() => trackEvent(EVENTS.subscribe)).not.toThrow();
  });

  it("forwards the event name and properties to PostHog when present", () => {
    window.posthog = { capture: vi.fn() };
    trackEvent(EVENTS.subscribe, { channel: "email" });
    expect(window.posthog.capture).toHaveBeenCalledWith("Subscribe", { channel: "email" });
  });

  it("sends no properties object when there are none", () => {
    window.posthog = { capture: vi.fn() };
    trackEvent(EVENTS.confirm);
    expect(window.posthog.capture).toHaveBeenCalledWith("Confirm", undefined);
  });

  it("swallows errors thrown by PostHog", () => {
    window.posthog = {
      capture: vi.fn(() => {
        throw new Error("blocked");
      }),
    };
    expect(() => trackEvent(EVENTS.donateClick)).not.toThrow();
  });
});
