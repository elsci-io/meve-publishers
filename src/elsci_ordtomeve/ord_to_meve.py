from datetime import datetime, timezone

from ord_schema.message_helpers import fetch_dataset
from ord_schema.orm.database import add_dataset
from ord_schema.proto.reaction_pb2 import CompoundIdentifier, ReactionRole, Reaction
from dateutil.parser import isoparser

isoparser = isoparser()

from elscimevesdk.Event import Event
def at_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError(
            "Can't turn a datetime w/o timezone into a UTC time. Ensure that you create a datetime that has"
            " timezone information. Otherwise it doesn't represent any particular instant and therefore it's not"
            " possible to calculate the UTC time.")
    # Signals API has a bug - it silently drops the timezone info considering all dates as if those were
    # UTC0 dates. So we need to change the time to UTC0 to be compatible.
    return dt.astimezone(timezone.utc)

def parse_ord_time(t: str) -> datetime | None:
    if not t:
        return None
    return at_utc(isoparser.isoparse(t))

event_type_mapping = {
    ReactionRole.ReactionRoleType.REACTANT: "Reacted",
    ReactionRole.ReactionRoleType.PRODUCT: "Synthesized"
}
structure_type_mapping = {
    CompoundIdentifier.CompoundIdentifierType.SMILES: "smiles",
    CompoundIdentifier.CompoundIdentifierType.CXSMILES: "smiles",
    CompoundIdentifier.CompoundIdentifierType.INCHI: "inchi",
    CompoundIdentifier.CompoundIdentifierType.MDL: "mdlmol",
}

class PreEvent:
    def __init__(self, event_name: str, struct: str, struct_format: str, ui_url: str):
        self.ui_url = ui_url
        self.struct_format = struct_format
        self.struct = struct
        self.event_name = event_name

def get_reacted_events(rxn: Reaction) -> list[PreEvent]:
    events: list[PreEvent] = []
    for input in rxn.inputs:
        components = rxn.inputs[input].components
        event_full: bool = False
        for component in components:
            event_name = event_type_mapping.get(component.reaction_role)
            if not event_name:
                continue
            struct_format: str = None
            struct: str = None
            for identifier in component.identifiers:
                struct_format = structure_type_mapping.get(identifier.type)
                struct = identifier.value
                if struct_format and struct:
                    event_full = True
                    break
            if event_full:
                events.append(PreEvent(event_name, struct, struct_format,
                                    "https://open-reaction-database.org/id/" + rxn.reaction_id))
    return events


dataset = fetch_dataset("ord_dataset-fc83743b978f4deea7d6856deacbfe53")
events: list[Event] = []
for rxn in dataset.reactions:
    pre_events: list[PreEvent] = []
    pre_events.extend(get_reacted_events(rxn))
    for outcome in rxn.outcomes:
        for product in outcome.products:
            for identifier in product.identifiers:
                struct_type = structure_type_mapping.get(identifier.type)
                struct = identifier.value
                if not struct_type or not struct:
                    continue
                pre_events.append(PreEvent("Synthesized", identifier.value, struct_type,
                                            "https://open-reaction-database.org/id/" + rxn.reaction_id))

    rxn_time: datetime = parse_ord_time(rxn.provenance.experiment_start.value)
    for pre_event in pre_events:
        events.append(Event(pre_event.event_name, rxn.provenance.experimenter.name, None, None,
                            pre_event.struct, pre_event.struct_format, None, rxn.reaction_id, rxn_time, pre_event.ui_url,
                            None, None))

for event in events:
    print(event.to_csv())