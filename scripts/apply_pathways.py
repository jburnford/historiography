"""Apply a seminar-pathway revision: edits to seminar-pathways.json, recorded in the graph's history.

    python3 scripts/apply_pathways.py BATCH.json            # apply
    python3 scripts/apply_pathways.py BATCH.json --check    # rebuild exactly from the record

BATCH.json: revision, baseline_revision, date, batch_dir, authorization, summary, edits. Each edit
names a `pathway`; a new one has `new: true` with title, node_ids, questions and exercise; an
existing one may carry title_after, node_ids_after, replace_question {from, to}, add_question,
questions_after (the whole list, from revision 1.153) and exercise_after. The graph changes only by a revision_history entry. seminar-pathways.json is pinned
by the 1.123 release, so a revision also needs amendment entries there.
"""
import argparse, hashlib, json, sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from scripts.validate_graph import validate  # noqa: E402

GRAPH = ROOT / 'historiography-1920-2000.json'
PATHWAYS = ROOT / 'seminar-pathways.json'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def serial(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def transform_pathways(paths, edits):
    paths = deepcopy(paths)
    by_id = {p['id']: p for p in paths['pathways']}
    for e in edits:
        if e.get('new'):
            if e['pathway'] in by_id:
                raise ValueError('Pathway exists: ' + e['pathway'])
            paths['pathways'].append(dict(id=e['pathway'], title=e['title'], node_ids=list(e['node_ids']),
                                          questions=list(e['questions']), exercise=e['exercise']))
            continue
        p = by_id[e['pathway']]
        if 'title_after' in e:
            p['title'] = e['title_after']
        if 'node_ids_after' in e:
            p['node_ids'] = list(e['node_ids_after'])
        if 'questions_after' in e:
            p['questions'] = list(e['questions_after'])
        if 'replace_question' in e:
            i = p['questions'].index(e['replace_question']['from'])
            p['questions'][i] = e['replace_question']['to']
        if 'add_question' in e:
            p['questions'].append(e['add_question'])
        if 'exercise_after' in e:
            p['exercise'] = e['exercise_after']
    return paths


class Batch:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.cfg = read(self.path)
        self.rev = self.cfg['revision']
        self.out = ROOT / 'data/production-batches' / self.cfg['batch_dir']
        self.base = ROOT / f"drafts/historiography-1920-2000.v{self.cfg['baseline_revision']}.json"

    def transform_graph(self, before):
        if before['revision_history'][-1]['version'] != self.cfg['baseline_revision']:
            raise ValueError('Expected revision ' + self.cfg['baseline_revision'])
        g = deepcopy(before)
        g['revision_history'].append(dict(version=self.rev, date=self.cfg['date'],
            acceptance_record=str((self.out / 'acceptance.json').relative_to(ROOT)), summary=self.cfg['summary'],
            pathways_changed=[e['pathway'] for e in self.cfg['edits']]))
        return g

    def apply(self):
        if (self.out / 'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        before, prior = read(GRAPH), read(PATHWAYS)
        graph, paths = self.transform_graph(before), transform_pathways(prior, self.cfg['edits'])
        errors, _ = validate(graph, paths)
        if errors:
            raise ValueError('\n'.join(errors))
        self.base.parent.mkdir(exist_ok=True)
        if self.base.exists() and self.base.read_bytes() != GRAPH.read_bytes():
            raise ValueError('Refusing to replace a different snapshot')
        self.base.write_bytes(GRAPH.read_bytes())
        changed = {e['pathway'] for e in self.cfg['edits']}
        GRAPH.write_text(serial(graph))
        PATHWAYS.write_text(serial(paths))
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / 'acceptance.json').write_text(serial(dict(
            revision=self.rev, date=self.cfg['date'], authorization=self.cfg['authorization'],
            batch=str(self.path.relative_to(ROOT)), batch_sha256=sha(self.path),
            baseline=str(self.base.relative_to(ROOT)), baseline_sha256=sha(self.base), production_sha256=sha(GRAPH),
            pathways_sha256=sha(PATHWAYS),
            prior_pathways={p['id']: p for p in prior['pathways'] if p['id'] in changed})))
        return graph, paths

    def check(self):
        record = read(self.out / 'acceptance.json')
        if sha(self.path) != record['batch_sha256']:
            raise ValueError(f'Pinned {self.rev} batch changed')
        paths = read(PATHWAYS)
        if sha(PATHWAYS) == record['pathways_sha256']:
            # Rebuild the prior pathways from the record, then re-apply the edits.
            prior = deepcopy(paths)
            new_ids = {e['pathway'] for e in self.cfg['edits'] if e.get('new')}
            prior['pathways'] = [record['prior_pathways'].get(p['id'], p) for p in prior['pathways'] if p['id'] not in new_ids]
            if transform_pathways(prior, self.cfg['edits']) != paths:
                raise ValueError(f'Exact {self.rev} pathway reconstruction differs')
        from scripts.build_site import load_baseline
        before = read(self.base) if self.base.exists() else load_baseline(dict(
            baseline_graph=str(self.base.relative_to(ROOT)), baseline_sha256=record['baseline_sha256']))[0]
        if before is None or hashlib.sha256(serial(before).encode()).hexdigest() != record['baseline_sha256']:
            raise ValueError(f"{self.cfg['baseline_revision']} baseline unavailable or changed")
        accepted = read(GRAPH) if sha(GRAPH) == record['production_sha256'] else load_baseline(dict(
            baseline_graph=f'drafts/historiography-1920-2000.v{self.rev}.json', baseline_sha256=record['production_sha256']))[0]
        if accepted is None or self.transform_graph(before) != accepted:
            raise ValueError(f'Exact {self.rev} reconstruction differs')
        return accepted, paths


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('batch')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    b = Batch(args.batch)
    graph, paths = b.check() if args.check else b.apply()
    errors, warnings = validate(graph, paths)
    print(f'{b.rev}: {len(errors)} errors; {len(warnings)} warnings; {len(paths["pathways"])} pathways')


if __name__ == '__main__':
    main()
