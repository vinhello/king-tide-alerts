/**
 * Thin wrapper around PostHog's custom events.
 *
 * PostHog is loaded from the page's script tag in cookieless mode: no cookies,
 * no browser storage, no person profiles. If the script is blocked or absent,
 * every call here is a no-op: analytics must never affect the page. Event
 * names must match the conversion goals configured in the PostHog dashboard.
 */

export type EventProps = Record<string, string | number | boolean>;

declare global {
  interface Window {
    posthog?: { capture: (event: string, properties?: EventProps) => void };
  }
}

export const EVENTS = {
  subscribe: "Subscribe",
  confirm: "Confirm",
  resendConfirmation: "Resend Confirmation",
  calendarDownload: "Calendar Download",
  donateClick: "Donate Click",
  feedbackSent: "Feedback Sent",
} as const;

export function trackEvent(name: string, props?: EventProps): void {
  try {
    if (typeof window === "undefined") return;
    const posthog = window.posthog;
    if (!posthog || typeof posthog.capture !== "function") return;
    posthog.capture(name, props);
  } catch {
    // Never let analytics break the page.
  }
}
