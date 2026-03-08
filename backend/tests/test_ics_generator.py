from datetime import datetime, timezone

from app.services.ics_generator import generate_ics


def _make_event(dt, height):
    return {"event_datetime": dt, "predicted_height": height}


def test_generate_ics_empty():
    result = generate_ics([])
    assert "BEGIN:VCALENDAR" in result
    assert "END:VCALENDAR" in result
    assert "BEGIN:VEVENT" not in result


def test_generate_ics_single_event():
    dt = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = generate_ics([_make_event(dt, 6.8)])

    assert "BEGIN:VEVENT" in result
    assert "END:VEVENT" in result
    assert "DTSTART:20260315T100000Z" in result
    assert "DTEND:20260315T140000Z" in result
    assert "SUMMARY:" in result
    assert "DESCRIPTION:" in result


def test_generate_ics_king_tide_label():
    dt = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = generate_ics([_make_event(dt, 6.8)])
    assert "King Tide Flooding" in result
    assert "High Tide Flooding" not in result


def test_generate_ics_non_king_tide():
    dt = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = generate_ics([_make_event(dt, 6.2)])
    assert "High Tide Flooding" in result
    assert "King Tide Flooding" not in result


def test_generate_ics_uid_deterministic():
    dt = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    event = _make_event(dt, 6.8)
    result1 = generate_ics([event])
    result2 = generate_ics([event])

    uid_lines_1 = [line for line in result1.splitlines() if line.startswith("UID:")]
    uid_lines_2 = [line for line in result2.splitlines() if line.startswith("UID:")]

    assert uid_lines_1 == uid_lines_2
    assert len(uid_lines_1) == 1
