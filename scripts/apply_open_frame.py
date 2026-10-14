"""Revision 1.133: end the 1920–2000 coverage cutoff (user, 2026-10-14).

    python3 scripts/apply_open_frame.py          # apply to the 1.132 graph
    python3 scripts/apply_open_frame.py --check  # rebuild 1.133 exactly from its baseline
"""
import argparse, hashlib, json, re, sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate

GRAPH = ROOT / 'historiography-1920-2000.json'
PATHWAYS = ROOT / 'seminar-pathways.json'
OUT = ROOT / 'data/production-batches/open-frame-1.133'
BASE = ROOT / 'drafts/historiography-1920-2000.v1.132.json'
REV, DAY, CUTOFF = '1.133', '2026-10-14', '2026-10-14'
ARCHIVE_SHA = '5fe82ffc101f1bef12e36a99f565eba40c0627eda5cde5397c86309d110935a9'
LIMIT = re.compile(r'(?:coverage|baseline) through 2000\b')
# The limit phrase with its joining punctuation on both sides ("· coverage through 2000;",
# "; coverage through 2000, "): replaced by one separator so what follows still reads.
LIMIT_JOINED = re.compile(r'\s*[·;,]?\s*(?:coverage|baseline) through 2000\b\s*[;,]?\s*')
AUTH = ("User, 2026-10-14: 'we need to end the 2000 break in this project'; the 2000 frame "
        "'comes from the original experiment where I scoped it to 2000, but we're building it out now'; "
        "decisions: switch now and build field by field; keep the exact-2000 view as an archive; drop the dates.")
REVIEW_BASIS = ('Reviewed through 2000 in the original 1920–2000 experiment. Later work is not yet '
                'surveyed for this entry; selected later interventions, where present, are dated individually.')
# The one non-label prose use of the phrase (spatialhistory scope_note); same meaning, new wording.
OLD_SCOPE = 'Later digital projects are not backdated into coverage through 2000.'
NEW_SCOPE = 'Later digital projects are not backdated into the period reviewed through 2000.'
OLD_Q = "Which parts of Hunt's argument would require extending this map beyond its current 2000 endpoint?"
NEW_Q = ("Which parts of Hunt's argument depend on work after 2000, and which entries on this "
         "pathway are still reviewed only through 2000?")


def read(p): return json.loads(Path(p).read_text())
def serial(v): return json.dumps(v, ensure_ascii=False, indent=2) + '\n'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clean_label(label):
    out = LIMIT_JOINED.sub(' · ', label).strip(' ·;,')
    return out or label


def transform(before):
    if before['revision_history'][-1]['version'] != '1.132':
        raise ValueError('Expected revision 1.132')
    g = deepcopy(before)
    g['title'] = 'The Historiography Atlas'
    g['schema_version'] = '1.5'
    ext = g['scope'].pop('extension')
    if ext['baseline_sha256'] != ARCHIVE_SHA:
        raise ValueError('Archive pointer is not the exact 1.121 view')
    g['scope']['main_period'] = [1920, None]
    g['scope']['frame'] = dict(start=1920, end=None, research_cutoff=CUTOFF,
        note=f'Open frame from revision {REV}. Each entry records how far it has been reviewed '
             '(coverage.reviewed_through); a review year is a limit of our reading, not an ending.')
    g['scope']['archive'] = dict(label='The original 1920–2000 experiment', baseline_period=[1920, 2000],
        baseline_graph=ext['baseline_graph'], baseline_revision=ext['baseline_revision'],
        baseline_sha256=ext['baseline_sha256'], acceptance_records=ext.get('acceptance_records', []))
    notes = g['scope']['notes']
    notes[:] = [n for n in notes if not n.startswith('Sources published after 2000 can retrospectively')]
    notes.append(f'From revision {REV} the atlas has no closing date. Fields are extended one at a time; '
                 'each entry states the year through which it has been reviewed. The original 1920–2000 '
                 'experiment (revision 1.121) is kept as an archived view.')
    for n in g['nodes']:
        n['date_label'] = clean_label(n['date_label'])
        if OLD_SCOPE in n.get('scope_note', ''):
            n['scope_note'] = n['scope_note'].replace(OLD_SCOPE, NEW_SCOPE)
        if n['entry_kind'] == 'group':
            n['coverage'] = dict(reviewed_through=2000, basis=REVIEW_BASIS)
        d = n.get('date_span')
        if d and d.get('end_kind') == 'coverage_limit':
            d['end'], d['end_kind'] = None, 'open'
            d.pop('coverage_through', None)
            d['basis'] = (d.get('basis', '') + f' Open from revision {REV}: the former 2000 end was the '
                          'atlas boundary, not an ending.').strip()
    for e in g.get('journal_catalogue', {}).get('edges', []):
        ts = e.get('temporal_scope') or {}
        # Notes say either "2000 is the atlas coverage boundary" or "2000 is the atlas boundary".
        if ts.get('end') == 2000 and '2000 is the atlas' in ts.get('note', ''):
            ts['end'] = None
            ts['note'] = (ts.get('note', '') + f' Open from revision {REV}: 2000 was the atlas boundary.').strip()
    g['revision_history'].append(dict(version=REV, date=DAY,
        acceptance_record=str((OUT / 'acceptance.json').relative_to(ROOT)),
        summary='Open frame: the 1920–2000 cutoff ends. Prose coverage limits become coverage.reviewed_through '
                '(2000 for every group, pending field-by-field review); open spans; the exact-2000 view '
                '(1.121) moves to scope.archive; title "The Historiography Atlas".',
        added_node_ids=[], added_edge_ids=[], revised_edge_ids=[]))
    return g


def pathways_transform(p):
    p = deepcopy(p)
    for path in p['pathways']:
        path['questions'] = [NEW_Q if q == OLD_Q else q for q in path['questions']]
    return p


class Batch:
    def apply(self):
        if (OUT / 'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        before = read(GRAPH)
        graph, paths = transform(before), pathways_transform(read(PATHWAYS))
        errors, _ = validate(graph, paths)
        if errors:
            raise ValueError('\n'.join(errors))
        BASE.parent.mkdir(exist_ok=True)
        if BASE.exists() and BASE.read_bytes() != GRAPH.read_bytes():
            raise ValueError('Refusing to replace a different snapshot')
        BASE.write_bytes(GRAPH.read_bytes())
        prior_paths = PATHWAYS.read_bytes()
        GRAPH.write_text(serial(graph))
        PATHWAYS.write_text(serial(paths))
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'acceptance.json').write_text(serial(dict(revision=REV, date=DAY, authorization=AUTH,
            baseline=str(BASE.relative_to(ROOT)), baseline_sha256=sha(BASE), production_sha256=sha(GRAPH),
            pathways_before_sha256=hashlib.sha256(prior_paths).hexdigest(), pathways_sha256=sha(PATHWAYS),
            prior_scope=before['scope'], prior_title=before['title'], prior_schema=before['schema_version'],
            prior_labels={n['id']: n['date_label'] for n in before['nodes'] if LIMIT.search(n['date_label'])},
            prior_spans={n['id']: n['date_span'] for n in before['nodes']
                         if n.get('date_span', {}).get('end_kind') == 'coverage_limit'})))
        return graph

    def baseline(self):
        record = read(OUT / 'acceptance.json')
        if BASE.exists():
            if sha(BASE) != record['baseline_sha256']:
                raise ValueError('Local 1.132 snapshot does not match the pinned baseline')
            return read(BASE)
        # Clean checkout (drafts/ is gitignored): recover 1.132 from git history. build_site
        # imports its sibling validate_graph by bare name, so its directory must be importable.
        if str(ROOT / 'scripts') not in sys.path:
            sys.path.append(str(ROOT / 'scripts'))
        from scripts.build_site import load_baseline
        graph, _ = load_baseline(dict(baseline_graph=str(BASE.relative_to(ROOT)),
                                      baseline_sha256=record['baseline_sha256']))
        if graph is None:
            raise ValueError('1.132 baseline unavailable')
        return graph

    def accepted(self):
        # the live graph moves on after 1.133; later revisions check against the accepted 1.133 graph
        record = read(OUT / 'acceptance.json')
        if sha(GRAPH) == record['production_sha256']:
            return read(GRAPH)
        if str(ROOT / 'scripts') not in sys.path:
            sys.path.append(str(ROOT / 'scripts'))
        from scripts.build_site import load_baseline
        graph, _ = load_baseline(dict(baseline_graph=f'drafts/historiography-1920-2000.v{REV}.json',
                                      baseline_sha256=record['production_sha256']))
        if graph is None:
            raise ValueError(f'Accepted {REV} graph unavailable')
        return graph

    def check(self):
        if transform(self.baseline()) != self.accepted():
            raise ValueError(f'Exact {REV} reconstruction differs')
        if pathways_transform(read(PATHWAYS)) != read(PATHWAYS):
            raise ValueError(f'{REV} pathway question not applied')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    b = Batch()
    graph = (b.check() or read(GRAPH)) if ap.parse_args().check else b.apply()
    errors, warnings = validate(graph, read(PATHWAYS))
    print(f'{REV}: {len(errors)} errors; {len(warnings)} warnings; {len(graph["nodes"])} nodes; {len(graph["edges"])} edges')


if __name__ == '__main__':
    main()
