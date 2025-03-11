import json
from datetime import datetime
from typing import Optional

IDEATED: str = "IDEATED"
REACTED: str = "REACTED"
SYNTHESIZED: str = "SYNTHESIZED"
REGISTERED: str = "REGISTERED"
REQUESTED: str = "REQUESTED"


class Event:
    def __init__(self, name, created_by, project, structure: str|None, structure_format: str|None,
                 entity: str, context: str, happened_time: datetime, originating_system: str,
                 details_ui_url, details_api_url, props: dict[str, any] | None):
        self.name = name
        self.username = created_by
        self.project = project
        self.structureFormat = structure_format
        # self.structureId = structure_id
        self.originalStructure = structure
        # self.entity = entity

        self.originatingSystem = originating_system
        self.context = context
        self.happenedTime = None
        if happened_time:
            self.happenedTime = happened_time.isoformat()
        self.detailsUiUrl = details_ui_url
        self.detailsApiUrl = details_api_url
        self.props = props

    def to_csv(self) -> str:
        return ",".join(Event._none_to_empty([
            self.name, self.entity, self.context, self.structureId, self.username, self.project,
            self.happenedTime, self.detailsApiUrl, self.detailsUiUrl])
        )
    def to_json(self) -> str:
        return json.dumps(self, default=vars)

    def __str__(self):
        return "EventDto: " + self.to_csv()

    @staticmethod
    def _none_to_empty(l: list[str]) -> list[str]:
        result: list[str] = []
        for val in l:
            if val is None:
                result.append("")
            else:
                result.append(val)
        return result
