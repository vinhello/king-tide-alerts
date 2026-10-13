/**
 * Where did this visit come from? Captured once per browser session on the
 * first page load, so a signup later in the visit still carries the original
 * referrer and campaign. Stored in sessionStorage; everything is best-effort.
 */

const STORAGE_KEY = "kta.signupSource";

export interface SignupSource {
  signup_referrer?: string;
  signup_utm_source?: string;
  signup_utm_medium?: string;
  signup_utm_campaign?: string;
  signup_landing_path?: string;
}

function trimTo(value: string | null | undefined, max: number): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  return trimmed ? trimmed.slice(0, max) : undefined;
}

/** Build a source record from the current location and referrer. Exported for tests. */
export function sourceFromLocation(
  search: string,
  pathname: string,
  referrer: string,
  ownOrigin: string
): SignupSource {
  const params = new URLSearchParams(search);
  // A referrer from our own site is navigation, not a source.
  const external = referrer && !referrer.startsWith(ownOrigin) ? referrer : undefined;
  return {
    signup_referrer: trimTo(external, 500),
    signup_utm_source: trimTo(params.get("utm_source"), 100),
    signup_utm_medium: trimTo(params.get("utm_medium"), 100),
    signup_utm_campaign: trimTo(params.get("utm_campaign"), 100),
    signup_landing_path: trimTo(pathname, 200),
  };
}

/** Record the source for this session if none is stored yet. Safe to call on every load. */
export function captureSignupSource(): void {
  try {
    if (sessionStorage.getItem(STORAGE_KEY)) return;
    const source = sourceFromLocation(
      window.location.search,
      window.location.pathname,
      document.referrer,
      window.location.origin
    );
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(source));
  } catch {
    // Storage can be unavailable (private mode, blocked). Attribution is optional.
  }
}

/** The stored source for this session, or an empty record. */
export function getSignupSource(): SignupSource {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SignupSource) : {};
  } catch {
    return {};
  }
}
