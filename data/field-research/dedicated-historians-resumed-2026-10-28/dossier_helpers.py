"""Bounded historian research artifacts; no live graph mutation."""
import hashlib
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[2]
BASELINE = json.loads((AUDIT / 'request-baseline.json').read_text())
GRAPH = json.loads((AUDIT / 'baseline-graph.json').read_text())
NODES = {n['id']: n for n in GRAPH['nodes']}
SOURCES = {s['id']: s for s in GRAPH['sources']}
DAY = '2026-10-28'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class Dossier:
    def __init__(self, person_id):
        self.pid = person_id
        self.folder = AUDIT / person_id
        self.context = json.loads((self.folder / 'context.json').read_text())
        self.sources, self.addenda, self.proposals, self.holds = [], {}, [], []

    def source(self, sid, title, url, citation, note, status='supporting_page_checked'):
        assert sid not in SOURCES and sid not in {s['id'] for s in self.sources}
        self.sources.append(dict(id=sid, title=title, url=url, citation=citation,
            verification=dict(status=status, checked_on=DAY, note=note)))
        return sid

    def addendum(self, sid, note):
        assert sid in SOURCES
        self.addenda[sid] = dict(status='supporting_page_checked', checked_on=DAY, note=note)
        return sid

    def edge(self, proposal_id, source, target, kind, claim, note, sids, locators,
             grade='A_fresh_selected_primary'):
        assert source in NODES and target in NODES
        assert self.pid in (source, target)
        assert kind in {'influence', 'contribution', 'critique', 'comparison'}
        assert not any((e['source'], e['target'], e.get('relationship_kind')) ==
                       (source, target, kind) for e in GRAPH['edges']), 'Existing pair/kind needs an explicit distinction or held disposition'
        self.proposals.append(dict(proposal_id=proposal_id, source=source, target=target,
            relationship_kind=kind, relationship=claim, evidence_note=note, source_ids=sids,
            primary_locators=locators, grade=grade, decision='include_pending_independent_review',
            type='critique' if kind == 'critique' else 'connection', directed=kind != 'comparison',
            existing_endpoint_pair_edge_ids=[e['id'] for e in GRAPH['edges']
                if {e['source'], e['target']} == {source, target}]))

    def hold(self, case_id, decision, people, finding, locators=None):
        row = dict(case_id=case_id, decision=decision, people=people, finding=finding)
        if locators:
            row['locators'] = locators
        self.holds.append(row)

    def finish(self, assessment, coverage, notes):
        known = set(SOURCES) | {s['id'] for s in self.sources}
        assert sha(AUDIT / 'baseline-graph.json') == self.context['baseline_graph_sha256']
        assert len({p['proposal_id'] for p in self.proposals}) == len(self.proposals)
        assert len({(p['source'], p['target'], p['relationship_kind']) for p in self.proposals}) == len(self.proposals)
        assert all(set(p['source_ids']) <= known and p['primary_locators'] for p in self.proposals)
        write(self.folder / 'proposals.json', dict(person_id=self.pid,
            baseline_revision=BASELINE['baseline_revision'], checked_on=DAY, proposals=self.proposals))
        write(self.folder / 'sources.json', dict(sources=self.sources, source_addenda=self.addenda))
        write(self.folder / 'held-cases.json', dict(person_id=self.pid, checked_on=DAY,
            holds=self.holds, not_exhaustive=True))
        names = ['proposals.json', 'sources.json', 'held-cases.json']
        write(self.folder / 'case-review.json', dict(person_id=self.pid,
            baseline_revision=BASELINE['baseline_revision'],
            baseline_graph_sha256=BASELINE['baseline_graph_sha256'], checked_on=DAY,
            status='bounded_research_complete', baseline_incident_edges=self.context['incident_edges'],
            relevant_group_routes=self.context['named_group_routes'],
            existing_claim_assessment=assessment,
            new_proposal_ids=[p['proposal_id'] for p in self.proposals], coverage=coverage,
            duplicate_check='Pair/kind checked against frozen current graph; final cross-dossier and current-graph review still required',
            raw_policy='Raw source bodies/PDF/text/images remain ignored in raw/',
            output_hashes={name: sha(self.folder / name) for name in names}))
        (self.folder / 'README.md').write_text(
            '# ' + NODES[self.pid]['label'] + ': dedicated relationship dossier\n\n' + notes +
            '\n\nBounded selected source work; independent review remains pending. No edge quota or exhaustive-network claim.\n')
        write(self.folder / 'raw/retrieval-hashes.json',
            {p.name: sha(p) for p in (self.folder / 'raw').iterdir()
             if p.is_file() and p.name != 'retrieval-hashes.json'})
        print(self.pid, len(self.proposals), 'proposals; ready for independent passage and coverage review')
