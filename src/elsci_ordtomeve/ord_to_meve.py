import json
from datetime import datetime
from typing import Iterable

from ord_schema.proto.reaction_pb2 import CompoundIdentifier, ReactionRole, Reaction

from elsci_ordtomeve.ord_util import get_dataset
from elsci_ordtomeve.time_util import parse_ord_time
from elscimevesdk.HttpClient import ElsciHttpException
from elscimevesdk.Meve import Meve

from elscimevesdk.Event import Event
from elscimevesdk.util.api_util import basic_auth_header
from elscimevesdk.util.env_util import envvar

auth_header_val: str = basic_auth_header(envvar("MEVE_USER_NAME", "admin"), envvar("MEVE_USER_PASSWORD", "admin"))
base_url: str = envvar("MEVE_BASE_URL", "http://localhost:8080")
default_headers: dict[str, str] = {"Authorization": auth_header_val}
meve = Meve(base_url, default_headers=default_headers)

DATASETS_PATH = './src/elsci_ordtomeve/datasets.txt'
# either we fail to parse these or we don't want such events in Meve
STRUCTS_TO_IGNORE_PATH = './src/elsci_ordtomeve/structs_to_ignore.txt'

with open(STRUCTS_TO_IGNORE_PATH, 'r') as f:
    structs_to_ignore = set(f.read().splitlines())
    print(f"{len(structs_to_ignore)} of structures are added to the ignore set - they won't be recorded as events")

event_type_mapping = {
    ReactionRole.ReactionRoleType.REACTANT: "Reacted",
    ReactionRole.ReactionRoleType.PRODUCT: "Synthesized"
}
structure_type_mapping = {
    CompoundIdentifier.CompoundIdentifierType.SMILES: "SMILES",
    CompoundIdentifier.CompoundIdentifierType.CXSMILES: "SMILES",
    CompoundIdentifier.CompoundIdentifierType.INCHI: "INCHI",
    # CompoundIdentifier.CompoundIdentifierType.MDL: "MDLMOL",
}

class PreEvent:
    def __init__(self, event_name: str, struct: str, struct_format: str, ui_url: str, props: dict[str, any] = None):
        self.ui_url = ui_url
        self.struct_format = struct_format
        self.struct: str = struct
        self.event_name: str = event_name
        self.props = props

def submit_events(events: list[Event], dataset_id: str):
    try:
        meve.events().create(events)
    except Exception as e:
        if isinstance(e, ElsciHttpException) and e.response_body.startswith("{"):
            d = json.loads(e.response_body)
            if "invalidStructure" in d:
                struct: str = d["invalidStructure"]
                print(f"Couldn't parse structure {struct}, adding to the skip list")
                with open(STRUCTS_TO_IGNORE_PATH, 'a') as f:
                    f.write(struct+"\n")
                structs_to_ignore.add(struct)
                submit_events([e for e in events if e.originalStructure != struct], dataset_id)
                return
        print(e)
        raise RuntimeError(f"Failed to process dataset {dataset_id}")

def _preevent_from_identifiers(event_name: str, rxn: Reaction, identifiers: Iterable[CompoundIdentifier]) -> PreEvent | None:
    struct_format: str|None = None
    struct: str|None = None
    event_full: bool = False
    for identifier in identifiers:
        struct_format = structure_type_mapping.get(identifier.type)
        struct = identifier.value
        if struct_format and struct:
            event_full = True
            # besides names, in the identifiers there can be more than one structure (in different formats)
            # for the same product/reactant, we need only one
            break
    if event_full:
        return PreEvent(event_name, struct, struct_format, "https://open-reaction-database.org/id/" + rxn.reaction_id)

def get_reacted_events(rxn: Reaction) -> list[PreEvent]:
    pre_events: list[PreEvent] = []
    # Even though structures must be unique within a reaction, it's still possible that 2 distinct ones end up having
    # the same structure ID. So we can't fully guarantee the uniqueness. Meve will replace one event with another then.
    structs = set()
    for reactants in rxn.inputs:
        for component in rxn.inputs[reactants].components:
            event_name = event_type_mapping.get(component.reaction_role)
            if not event_name:
                continue
            if e := _preevent_from_identifiers(event_name, rxn, component.identifiers):
                if e.struct not in structs:
                    structs.add(e.struct)
                    pre_events.append(e)
    return pre_events

def get_synthesized_events(rxn: Reaction) -> list[PreEvent]:
    pre_events: list[PreEvent] = []
    # Even though structures must be unique within a reaction, it's still possible that 2 distinct ones end up having
    # the same structure ID. So we can't fully guarantee the uniqueness. Meve will replace one event with another then.
    structs = set()
    for outcome in rxn.outcomes:
        for product in outcome.products:
            if e := _preevent_from_identifiers("Synthesized", rxn, product.identifiers):
                if e.struct not in structs:
                    structs.add(e.struct)
                    pre_events.append(e)
    return pre_events

events_total = 0
reactions_total = 0
dataset_ids = []
with open(DATASETS_PATH, 'r') as f:
    lines = f.readlines()
    for line in lines:
        dataset_ids.extend(line.split(" "))
for dataset_id in dataset_ids:
    dataset = get_dataset(dataset_id.strip())
    events: list[Event] = []
    for rxn in dataset.reactions:
        reactions_total += 1
        pre_events: list[PreEvent] = []
        pre_events.extend(get_reacted_events(rxn))
        pre_events.extend(get_synthesized_events(rxn))
        rxn_time: datetime = parse_ord_time(rxn.provenance.experiment_start.value)
        for pre_event in pre_events:
            if pre_event.struct in structs_to_ignore:
                print(f" {rxn.reaction_id} has structure that we can't parse, skipping this structure: {pre_event.struct}")
                continue
            if pre_event.struct_format == 'SMILES' and '*' in pre_event.struct:
                print(f" {rxn.reaction_id} has structure with wildcards, skipping this structure: {pre_event.struct}")
                continue
            experimenter = rxn.provenance.experimenter.name or None
            events.append(Event(pre_event.event_name, experimenter, None,
                                pre_event.struct, pre_event.struct_format, None, rxn.reaction_id[4:], rxn_time, "ORD",
                                pre_event.ui_url, None, None))


    print(f"Parsed {len(events)} events")
    submit_events(events, dataset_id)
    events_total += len(events)

print(f"Parsed {events_total} events out of {reactions_total} reactions")

