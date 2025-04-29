"""Event manager."""

from collections.abc import Generator
import datetime
from logging import getLogger
from typing import Literal, TYPE_CHECKING

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.http import HttpMock
from httplib2 import Http

from googlelibraries.calendar.event import Event, EventFactory

if TYPE_CHECKING:
    # Reason: google-api-python-client-stubs's issue?
    from googleapiclient._apis.calendar.v3 import CalendarResource  # pyright: ignore[reportMissingModuleSource]


class ServiceFactory:
    """To mock HTTP request when test since argument of credentials and http are excluded in build method."""

    def __init__(
        self,
        service_name: Literal["calendar"],
        version: str,
        *,
        credentials: Credentials | None = None,
        http: Http | HttpMock | None = None,
    ) -> None:
        self.service_name = service_name
        self.version = version
        self.credentials = credentials
        self.http = http

    def create(self) -> Resource:
        return (
            build(self.service_name, self.version, credentials=self.credentials)
            if self.http is None
            else build(self.service_name, self.version, http=self.http)
        )


class EventManager:
    """Event manager."""

    def __init__(self, creds: Credentials, calendar_id: str, *, http: Http | HttpMock | None = None) -> None:
        self.service: CalendarResource = build("calendar", "v3", credentials=creds, http=http)
        self.calendar_id = calendar_id
        self.logger = getLogger(__name__)

    def register(self, event: Event) -> None:
        # Reason: Meta programming is used. pylint: disable-next=no-member
        self.service.events().insert(calendarId=self.calendar_id, body=event.convert_to_body()).execute()

    def iterate_future_event(self, now: datetime.datetime) -> Generator[Event]:
        """Iterates the events."""
        # Reason: Meta programming is used. pylint: disable-next=no-member
        events_resource = self.service.events()
        page_token = None
        while True:
            events_result = events_resource.list(
                calendarId=self.calendar_id,
                timeMin=now.replace(microsecond=0).isoformat(),
                singleEvents=True,
                orderBy="startTime",
                # Reason: Official documentation's instruction:
                # - Events: list | Google Calendar | Google for Developers
                #   https://developers.google.com/workspace/calendar/api/v3/reference/events/list?hl=ja
                pageToken=page_token,  # type: ignore[arg-type]
            ).execute()
            yield from (EventFactory.create(event) for event in events_result["items"])
            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

    def check(self) -> None:
        """Call the Calendar API."""
        self.logger.debug("Getting the upcoming 10 events")
        events_result = (
            # Reason: Meta programming is used. pylint: disable-next=no-member
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=self.create_now_string(),
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            self.logger.debug("No upcoming events found.")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            self.logger.debug("%s %s", start, event["summary"])

    @staticmethod
    def create_now_string() -> str:
        return datetime.datetime.now(tz=datetime.UTC).replace(microsecond=0).isoformat()
