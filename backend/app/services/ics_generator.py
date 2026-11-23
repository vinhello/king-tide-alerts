from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Tide times come from NOAA in the station's local time and are kept with
# that wall-clock reading (see recent_tides.STATION_TZ). A calendar needs the
# real instant, so the reading is placed in Pacific time before conversion.
STATION_TZ = ZoneInfo("America/Los_Angeles")


def _escape_ics_text(text: str) -> str:
    """Escape special characters per RFC 5545 section 3.3.11."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold_line(line: str) -> str:
    """Fold lines longer than 75 octets per RFC 5545 section 3.1."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    chunks = []
    chunks.append(encoded[:75].decode("utf-8", errors="ignore"))
    encoded = encoded[75:]
    while len(encoded) > 74:
        chunks.append(encoded[:74].decode("utf-8", errors="ignore"))
        encoded = encoded[74:]
    if encoded:
        chunks.append(encoded.decode("utf-8"))
    return "\r\n ".join(chunks)


def generate_ics(events: list[dict], station_id: str = "9414290") -> str:
    """Generate an ICS calendar file from tide events.

    Each event dict has: event_datetime (datetime), predicted_height (float)
    """
    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//King Tide Alert//kingtidealert.com//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:King Tide Alerts",
    ]

    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for event in events:
        dt: datetime = event["event_datetime"]
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        height: float = event["predicted_height"]
        peak = dt.replace(tzinfo=STATION_TZ).astimezone(timezone.utc)
        dtstart = (peak - timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
        dtend = (peak + timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")

        if height >= 6.5:
            summary = f"King Tide Flooding - {height:.1f} ft"
        else:
            summary = f"High Tide Flooding - {height:.1f} ft"

        description = (
            f"High tide of {height:.1f} ft predicted. "
            "Bay Trail bike path through Sausalito may be flooded approximately "
            "2 hours before and after peak. "
            "Use Bridgeway Boulevard sidewalk as alternate route."
        )

        uid = f"{station_id}-{dt.isoformat()}@kingtidealert.com"

        lines += [
            "BEGIN:VEVENT",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            _fold_line(f"SUMMARY:{_escape_ics_text(summary)}"),
            _fold_line(f"DESCRIPTION:{_escape_ics_text(description)}"),
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
