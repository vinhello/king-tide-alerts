import { useEffect, useState } from "react";
import { AlertTriangle, ExternalLink } from "lucide-react";
import { getNwsAlerts } from "../services/api";
import type { NwsAlert } from "../types";

// Matches the backend cache, so a refresh never hits NWS more often than that.
const REFRESH_INTERVAL_MS = 600000;
const MAX_BANNERS = 2;
const PACIFIC = "America/Los_Angeles";

function formatUntil(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: PACIFIC,
  });
}

function formatIssued(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: PACIFIC,
  });
}

function isWarning(event: string): boolean {
  return /warning/i.test(event);
}

interface AdvisoryCardProps {
  alert: NwsAlert;
}

function AdvisoryCard({ alert }: AdvisoryCardProps) {
  const warning = isWarning(alert.event);
  const borderClass = warning ? "border-l-destructive" : "border-l-accent";
  const textClass = warning ? "text-destructive" : "text-accent";
  const until = formatUntil(alert.ends);
  const issued = formatIssued(alert.sent);

  // The summary only: the event, how long it is in effect, the NWS "WHAT"
  // sentence as received, who issued it, and the link to the rest.
  return (
    <div
      role="status"
      className={`bg-card rounded-lg border border-border border-l-4 ${borderClass} shadow-sm p-4 sm:p-5`}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className={`h-5 w-5 shrink-0 mt-0.5 ${textClass}`} aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">
            National Weather Service
          </p>
          <p className={`text-base font-medium ${textClass}`}>
            {alert.event}
            {until && (
              <span className="text-foreground font-normal"> · in effect until {until}</span>
            )}
          </p>
          {alert.what && (
            <p className="text-sm text-foreground mt-2">“{alert.what}”</p>
          )}
          <p className="text-xs text-muted-foreground mt-2">
            Issued by {alert.sender_name}
            {issued && ` on ${issued}`}.{" "}
            <a
              href={alert.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              Read the advisory
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Coastal flood products the National Weather Service has in effect for the
 * path's zones, quoted verbatim. Renders nothing when there are none or the
 * feed is unavailable.
 */
export default function NwsAdvisoryBanner() {
  const [alerts, setAlerts] = useState<NwsAlert[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await getNwsAlerts();
        if (!cancelled) {
          setAlerts(response.alerts.slice(0, MAX_BANNERS));
        }
      } catch {
        // Nothing to show; the rest of the page is unaffected.
      }
    }

    load();
    const interval = setInterval(load, REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (alerts.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-3 mb-3 sm:mb-4">
      {alerts.map((alert) => (
        <AdvisoryCard key={alert.id} alert={alert} />
      ))}
    </div>
  );
}
