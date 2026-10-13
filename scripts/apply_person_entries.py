"""Build, apply and reconstruct a person-entry revision from a research packet.

The packet directory holds batch.json (revision, baseline_revision, date, summary, authorization,
rationale, persons, optional extras) and one folder per person with entry-draft.json (node, people_update,
proposed_edges, new_sources, source_addenda or proposed_source_addenda, wikidata_check), in the
format of data/extension-2026/canadian-person-links-2026-10-13/. Revision 1.129 used its own
script (apply_canadian_person_links.py), which stays pinned to its acceptance record.

    python3 scripts/apply_person_entries.py PACKET_DIR --build   # freeze release/editorial-additions.json
    python3 scripts/apply_person_entries.py PACKET_DIR           # apply to the baseline revision
    python3 scripts/apply_person_entries.py PACKET_DIR --check   # rebuild the revision exactly
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate

GRAPH = ROOT / 'historiography-1920-2000.json'
EDGE_KEYS = ['source', 'target', 'relationship', 'type', 'relationship_kind', 'directed', 'source_ids', 'evidence_note',
             'classification_basis', 'map_label', 'target_strand']
TABLES = ('nodes', 'people', 'edges', 'sources', 'revision_history')


def read(path):
    return json.loads(Path(path).read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Batch:
    def __init__(self, pkt):
        self.pkt = Path(pkt).resolve()
        self.cfg = read(self.pkt / 'batch.json')
        self.rev, self.day = self.cfg['revision'], self.cfg['date']
        self.packet = self.pkt / 'release/editorial-additions.json'
        self.out = ROOT / 'data/production-batches' / self.cfg['batch_dir']
        self.base = ROOT / f"drafts/historiography-1920-2000.v{self.cfg['baseline_revision']}.json"

    def build(self):
        nodes, people_updates, edges, sources, addenda, roster_edges, wikidata = [], [], [], [], {}, [], []
        new_people, roster_additions = [], []
        for name in self.cfg['persons'] + self.cfg.get('extras', []):
            d = read(self.pkt / name / 'entry-draft.json')
            if d.get('node'):
                nodes.append(d['node'])
                pu = d['people_update']
                people_updates.append(dict(id=pu['id'], node_id=pu['node_id']))
                if pu.get('new'):
                    new_people.append({k: pu[k] for k in ('id', 'label', 'identity_note') if pu.get(k)})
                wikidata.append(dict(person_id=d['node']['id'], **d['wikidata_check']))
            for p in d.get('new_people', []):
                new_people.append(p)
            for ra in d.get('roster_additions', []):
                roster_additions.append(dict(node=ra['node'], row=ra['row'], proposal_id=ra.get('proposal_id')))
            for r in d['proposed_edges']:
                if r.get('include') is False:
                    continue
                e = {k: r[k] for k in EDGE_KEYS if r.get(k) is not None}
                e['proposal_id'] = r['proposal_id']
                edges.append(e)
                for row in ([r['roster_row']] if isinstance(r.get('roster_row'), str) else r.get('roster_row') or []):
                    roster_edges.append(dict(node=row, person_id=d['node']['id'], proposal_id=r['proposal_id']))
            sources += [s for s in d.get('new_sources', []) if s['id'] not in {x['id'] for x in sources}]
            for sid, note in {**(d.get('source_addenda') or {}), **(d.get('proposed_source_addenda') or {})}.items():
                add = note if isinstance(note, dict) else dict(status='supporting_page_checked', checked_on=self.day, note=note)
                if sid in addenda:  # two drafts re-read the same source: keep both notes
                    prev = addenda[sid]
                    add = dict(prev, note=f"{prev['note']} [{name} draft: {add['note']}]",
                               status=prev['status'] if prev['status'] == 'supporting_page_checked' else add['status'])
                addenda[sid] = add
        merges = self.cfg.get('source_merges', {})
        if merges:
            sources, nodes, edges, roster_additions = self.merge_sources(merges, sources, nodes, edges, roster_additions)
        packet = dict(schema='atlas_editorial_packet/1', revision=self.rev, baseline_revision=self.cfg['baseline_revision'],
                      prepared=self.day, nodes=nodes, people_updates=people_updates, roster_edges=roster_edges, edges=edges,
                      sources=sorted(sources, key=lambda s: s['id']), source_addenda=addenda,
                      edge_revisions=self.cfg.get('edge_revisions', {}), wikidata=wikidata, rationale=self.cfg['rationale'],
                      research={n: str((self.pkt / n).relative_to(ROOT)) for n in self.cfg['persons'] + self.cfg.get('extras', [])})
        if new_people or roster_additions:
            packet.update(new_people=new_people, roster_additions=roster_additions)
        self.packet.parent.mkdir(exist_ok=True)
        self.packet.write_text(json.dumps(packet, ensure_ascii=False, indent=1) + '\n')
        print(f'{self.rev} packet: {len(nodes)} person entries, {len(edges)} edges, {len(sources)} new sources, {len(addenda)} addenda, '
              f'{len(new_people)} new people, {len(roster_additions)} roster additions')

    @staticmethod
    def merge_sources(merges, sources, nodes, edges, roster_additions):
        """Fold duplicate new sources (same work drafted under several ids) into one canonical id.
        Each duplicate's verification note is appended to the canonical note, since the drafts
        read different pages; the strongest status wins."""
        rank = {'supporting_page_checked': 2, 'bibliographic_metadata_checked': 1}
        by_id = {s['id']: s for s in sources}
        for dup, canon in merges.items():
            if dup not in by_id or canon not in by_id:
                raise ValueError(f'Merge {dup} -> {canon}: both must be new sources')
            c, d = by_id[canon]['verification'], by_id[dup]['verification']
            c['note'] = f"{c['note']} [Also checked under {dup}: {d['note']}]"
            if rank.get(d['status'], 0) > rank.get(c['status'], 0):
                c['status'], c['checked_on'] = d['status'], d['checked_on']
        fix = lambda ids: list(dict.fromkeys(merges.get(i, i) for i in ids))
        for n in nodes:
            n['source_ids'] = fix(n['source_ids'])
        for e in edges:
            e['source_ids'] = fix(e['source_ids'])
        for ra in roster_additions:
            ra['row']['source_ids'] = fix(ra['row']['source_ids'])
        return [s for s in sources if s['id'] not in merges], nodes, edges, roster_additions

    def transform(self, before, packet):
        if before['revision_history'][-1]['version'] != packet['baseline_revision']:
            raise ValueError('Expected revision ' + packet['baseline_revision'])
        g = deepcopy(before)
        ids = {n['id'] for n in g['nodes']}
        for node in packet['nodes']:
            if node['id'] in ids:
                raise ValueError('Node exists: ' + node['id'])
            g['nodes'].append(deepcopy(node))
        people = {p['id'] for p in g['people']}
        for p in packet.get('new_people', []):
            if p['id'] in people:
                raise ValueError('Person exists: ' + p['id'])
            g['people'].append(deepcopy(p))
        for upd in packet['people_updates']:
            next(p for p in g['people'] if p['id'] == upd['id'])['node_id'] = upd['node_id']
        have = {s['id'] for s in g['sources']}
        for s in packet['sources']:
            if s['id'] in have:
                raise ValueError('Source exists: ' + s['id'])
            g['sources'].append(deepcopy(s))
        for s in g['sources']:
            add = packet['source_addenda'].get(s['id'])
            if add:
                v = s.setdefault('verification', {})
                v['note'] = (v.get('note', '') + f" Addendum {add['checked_on']}: {add['note']}").strip()
                if add['status'] == 'supporting_page_checked':
                    v['status'], v['checked_on'] = add['status'], add['checked_on']
        last = max(int(e['id'].split('_')[1]) for e in g['edges'])
        new_ids = {}
        for i, e in enumerate(packet['edges'], start=last + 1):
            new_ids[e['proposal_id']] = f'edge_{i:03d}'
            g['edges'].append(dict(id=new_ids[e['proposal_id']], **deepcopy(e)))
        for eid, upd in packet['edge_revisions'].items():
            next(e for e in g['edges'] if e['id'] == eid).update(deepcopy(upd))
        for ra in packet.get('roster_additions', []):
            node = next(n for n in g['nodes'] if n['id'] == ra['node'])
            if any(r['person_id'] == ra['row']['person_id'] for r in node['representative_people']):
                raise ValueError(f"Roster row exists: {ra['node']}/{ra['row']['person_id']}")
            row = deepcopy(ra['row'])
            if ra.get('proposal_id'):
                row['edge_id'] = new_ids[ra['proposal_id']]
            node['representative_people'].append(row)
        for re_ in packet['roster_edges']:
            node = next(n for n in g['nodes'] if n['id'] == re_['node'])
            next(r for r in node['representative_people'] if r['person_id'] == re_['person_id'])['edge_id'] = new_ids[re_['proposal_id']]
        g['revision_history'].append(dict(version=self.rev, date=self.day,
            acceptance_record=str((self.out / 'acceptance.json').relative_to(ROOT)), summary=self.cfg['summary'],
            added_node_ids=[n['id'] for n in packet['nodes']], added_edge_ids=list(new_ids.values()),
            revised_edge_ids=sorted(packet['edge_revisions'])))
        return g

    def accepted_graph(self):
        record = read(self.out / 'acceptance.json')
        if sha(GRAPH) == record['production_sha256']:
            return read(GRAPH)
        from scripts.build_site import load_baseline
        graph, _ = load_baseline(dict(baseline_graph=f'drafts/historiography-1920-2000.v{self.rev}.json',
                                      baseline_sha256=record['production_sha256']))
        if graph is None:
            raise ValueError(f'Accepted {self.rev} graph unavailable')
        return graph

    def baseline(self):
        record = read(self.out / 'acceptance.json')
        if self.base.exists():
            before = read(self.base)
        else:
            before = deepcopy(self.accepted_graph())
            for table, length in record['previous_table_lengths'].items():
                before[table] = before[table][:length]
            for table, rows in record['prior_records'].items():
                for i, row in enumerate(before[table]):
                    if row['id'] in rows:
                        before[table][i] = deepcopy(rows[row['id']])
        if hashlib.sha256(serial(before).encode()).hexdigest() != record['baseline_sha256']:
            raise ValueError(f"Exact {self.cfg['baseline_revision']} baseline recovery differs")
        return before

    def apply(self):
        if (self.out / 'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        packet = read(self.packet)
        before = read(GRAPH)
        graph = self.transform(before, packet)
        errors, _ = validate(graph, read(ROOT / 'seminar-pathways.json'))
        if errors:
            raise ValueError('\n'.join(errors))
        self.base.parent.mkdir(exist_ok=True)
        if self.base.exists() and self.base.read_bytes() != GRAPH.read_bytes():
            raise ValueError('Refusing to replace a different snapshot')
        self.base.write_bytes(GRAPH.read_bytes())
        self.out.mkdir(parents=True, exist_ok=True)
        GRAPH.write_text(serial(graph))
        touched = dict(people={u['id'] for u in packet['people_updates']}, edges=set(packet['edge_revisions']),
                       sources=set(packet['source_addenda']),
                       nodes={r['node'] for r in packet['roster_edges'] + packet.get('roster_additions', [])})
        record = dict(revision=self.rev, date=self.day, authorization=self.cfg['authorization'],
            baseline=str(self.base.relative_to(ROOT)), baseline_sha256=sha(self.base), packet=str(self.packet.relative_to(ROOT)),
            packet_sha256=sha(self.packet), production_sha256=sha(GRAPH),
            previous_table_lengths={k: len(before[k]) for k in TABLES},
            prior_records={t: {r['id']: r for r in before[t] if r['id'] in ids} for t, ids in touched.items()},
            counts=dict(new_person_entries=len(packet['nodes']), new_edges=len(packet['edges']),
                        new_sources=len(packet['sources']), source_addenda=len(packet['source_addenda'])))
        (self.out / 'acceptance.json').write_text(serial(record))
        return graph

    def check(self):
        record = read(self.out / 'acceptance.json')
        if sha(self.packet) != record['packet_sha256']:
            raise ValueError(f'Pinned {self.rev} packet changed')
        graph = self.transform(self.baseline(), read(self.packet))
        if graph != self.accepted_graph():
            raise ValueError(f'Exact {self.rev} reconstruction differs')
        return graph


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('packet_dir')
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    b = Batch(args.packet_dir)
    if args.build:
        return b.build()
    graph = b.check() if args.check else b.apply()
    errors, warnings = validate(graph, read(ROOT / 'seminar-pathways.json'))
    print(f'{b.rev}: {len(errors)} errors; {len(warnings)} warnings; {len(graph["nodes"])} nodes; {len(graph["edges"])} edges')


if __name__ == '__main__':
    main()
