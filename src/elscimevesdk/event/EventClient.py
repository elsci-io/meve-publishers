import json

from elscimevesdk.Event import Event
from elscimevesdk.HttpClient import HttpClient


class EventClient:
    def __init__(self, settings: HttpClient):
        self.http: HttpClient = settings

    def create(self, events: list[Event]) -> None:
        return self.http.post("/api/event", bytearray(json.dumps(events, default=vars), "utf-8"))