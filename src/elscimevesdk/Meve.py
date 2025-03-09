from elscimevesdk.HttpClient import HttpClient
from elscimevesdk.event.EventClient import EventClient


class Meve:
    http_client: HttpClient
    org_id: str | None

    def __init__(self, base_url: str, default_headers: dict[str:str] = None):
        """
        :param base_url: e.g. https://peaksel.elsci.io
        :param org_name: the unique name of the org (can be taken from the URL in Peaksel). Ideally you should pass
                         `org_id` instead, but if you don't know it - the SDK will figure out the ID by the name.
        :param org_id: id of the org in which scope you're going to work. You can pass this or hte `org_name`
        :param default_headers: these HTTP headers will be added to every request
        """
        self.http_client = HttpClient(base_url, default_headers)

    def events(self) -> EventClient:
        return EventClient(self.http_client)