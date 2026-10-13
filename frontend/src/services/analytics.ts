/**
 * Thin wrapper around Plausible's custom events.
 *
 * Plausible is loaded from the page's script tag and is cookieless. If the
 * script is blocked or absent, every call here is a no-op: analytics must
 * never affect the page. Event names must match the goals configured in the
 * Plausible dashboard.
 */

export type EventProps = Record<string, string | number | boolean>;

declare global {
  interface Window {
    plausible?: (event: string, options?: { props?: EventProps }) => void;
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
    if (typeof window === "undefined" || typeof window.plausible !== "function") return;
    window.plausible(name, props ? { props } : undefined);
  } catch {
    // Never let analytics break the page.
  }
}
