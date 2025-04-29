"""Datetime for radiko specification."""

from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    # Reason: google-api-python-client-stubs's issue?
    from googleapiclient._apis.calendar.v3.schemas import EventDateTime  # pyright: ignore[reportMissingModuleSource]


class GoogleCalendarDatetime:
    """Datetime for Google Calendar specification."""

    @staticmethod
    def convert_to_google_calendar_format(datetime_value: datetime) -> "EventDateTime":
        tzinfo = datetime_value.tzinfo
        if not isinstance(tzinfo, ZoneInfo):
            msg = "Datetime must be created with ZoneInfo"
            raise TypeError(msg)
        return {
            # Like "Asia/Tokyo"
            "timeZone": tzinfo.key,
            "dateTime": datetime_value.isoformat(),
        }

    @staticmethod
    def convert_to_datetime(event_datetime: "EventDateTime") -> datetime:
        return datetime.fromisoformat(event_datetime["dateTime"]).astimezone(
            ZoneInfo(event_datetime["timeZone"]),
        )
