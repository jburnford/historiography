"""Locate life records in accepted additions, avoiding proposals still being written."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def accepted_life_paths(graph, person_ids):
    paths = set()
    for revision in graph['revision_history']:
        if not set(revision.get('added_node_ids', [])) & person_ids:
            continue
        receipt = revision.get('acceptance_record')
        if not receipt:
            continue
        record = json.loads((ROOT / receipt).read_text())
        packet = record.get('packet')
        if not packet:
            continue
        folder = (ROOT / packet).parent.parent
        if folder.name.startswith('remaining-'):
            paths.update(folder.rglob('life-status.json'))
        else:
            # From 1.203: other accepted packets contribute only records for entries they added.
            added = set(revision['added_node_ids']) & person_ids
            paths.update(path for path in folder.rglob('life-status.json')
                         if json.loads(path.read_text()).get('person_id') in added)
    return sorted(paths)
