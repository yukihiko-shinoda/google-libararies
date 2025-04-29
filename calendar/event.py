"""Model of Google Calendar event."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from googlelibraries.calendar.datetime import GoogleCalendarDatetime

if TYPE_CHECKING:
    # Reason: google-api-python-client-stubs's issue?
    from googleapiclient._apis.calendar.v3.schemas import (  # pyright: ignore[reportMissingModuleSource]  # isort:skip
        Event as EventSchema,
    )


@dataclass
class Event:
    """Event model."""

    summary: str
    start: datetime
    end: datetime
    description: str | None = None

    def convert_to_body(self) -> "EventSchema":
        """Convert to body for Google Calendar API."""
        body: EventSchema = {
            "summary": self.summary,
            "start": GoogleCalendarDatetime.convert_to_google_calendar_format(self.start),
            "end": GoogleCalendarDatetime.convert_to_google_calendar_format(self.end),
        }
        if self.description:
            body["description"] = self.description
        return body

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Event):
            raise NotImplementedError
        return self.summary == value.summary and self.start == value.start


class EventFactory:
    @staticmethod
    def create(event: "EventSchema") -> Event:
        return Event(
            summary=event["summary"],
            start=GoogleCalendarDatetime.convert_to_datetime(event["start"]),
            end=GoogleCalendarDatetime.convert_to_datetime(event["end"]),
            description=event.get("description"),
        )
