import json
from datetime import datetime

from ord_schema.proto.reaction_pb2 import CompoundIdentifier, ReactionRole, Reaction

from elsci_ordtomeve.ord_util import get_dataset
from elsci_ordtomeve.time_util import parse_ord_time
from elscimevesdk.HttpClient import ElsciHttpException
from elscimevesdk.Meve import Meve

from elscimevesdk.Event import Event
from elscimevesdk.util.api_util import basic_auth_header
from elscimevesdk.util.env_util import envvar

passwrd: str = envvar("MEVE_USER_PASSWORD", "sdktest")  # these work only for locally deployed instances
auth_header_val: str = basic_auth_header("MEVE_USER_NAME", passwrd)
base_url: str = envvar("MEVE_BASE_URL", "http://localhost:8080")
default_headers: dict[str, str] = {"Authorization": auth_header_val}
meve = Meve(base_url, default_headers=default_headers)

# We can't parse these for some reason:
with open('./src/elsci_ordtomeve/structs_to_ignore.txt', 'r') as f:
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
    def __init__(self, event_name: str, struct: str, struct_format: str, ui_url: str):
        self.ui_url = ui_url
        self.struct_format = struct_format
        self.struct = struct
        self.event_name = event_name

def submit_events(events: list[Event], dataset_id: str):
    try:
        meve.events().create(events)
    except Exception as e:
        if isinstance(e, ElsciHttpException) and e.response_body.startswith("{"):
            d = json.loads(e.response_body)
            if "invalidStructure" in d:
                struct: str = d["invalidStructure"]
                print(f"Couldn't parse structure {struct}, adding to the skip list")
                with open('./src/elsci_ordtomeve/structs_to_ignore.txt', 'a') as f:
                    f.write(struct+"\n")
                structs_to_ignore.add(struct)
                submit_events([e for e in events if e.originalStructure != struct], dataset_id)
                return
        print(e)
        raise RuntimeError(f"Failed to process dataset {dataset_id}")

def get_reacted_events(rxn: Reaction) -> list[PreEvent]:
    events: list[PreEvent] = []
    for input in rxn.inputs:
        components = rxn.inputs[input].components
        for component in components:
            event_full: bool = False
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

events_total = 0
reactions_total = 0
dataset_ids = []
with open('./datasets.txt', 'r') as f:
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
            if pre_event.struct in structs_to_ignore:
                print(f" {rxn.reaction_id} has structure that we can't parse, skipping this structure: {pre_event.struct}")
                continue
            if pre_event.struct_format == 'SMILES' and '*' in pre_event.struct:
                print(f" {rxn.reaction_id} has structure with wildcards, skipping this structure: {pre_event.struct}")
                continue
            events.append(Event(pre_event.event_name, rxn.provenance.experimenter.name, None, None,
                                pre_event.struct, pre_event.struct_format, None, rxn.reaction_id, rxn_time, "ORD",
                                pre_event.ui_url, None, None))


    print(f"Parsed {len(events)} events")
    submit_events(events, dataset_id)
    events_total += len(events)

print(f"Parsed {events_total} events out of {reactions_total} reactions")

