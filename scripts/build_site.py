"""Build only explicitly approved public assets; never serve the repository root.

Usage:
  python3 scripts/build_site.py                      # production build into docs/
  python3 scripts/build_site.py --graph P --dest D   # local preview of another graph file
                                                     # (D must be under /tmp; never docs/)
  python3 scripts/build_site.py --baseline P         # override the 2000 baseline graph file

When the graph carries `scope.extension` and names an archived baseline graph in
`scope.extension.baseline_graph` (or --baseline is given), the build also publishes that
baseline, slimmed like the main graph, as `data/graph-2000.json`, and records the asset in
the published `scope.extension.baseline_asset` so the site can offer an exact 2000 view.
"""
import argparse
import json
from pathlib import Path
import shutil

from validate_graph import validate

ROOT = Path(__file__).resolve().parents[1]
# GitHub Pages can serve a branch only from the repository root or `/docs`, so the
# allowlisted build lands in `docs/` and is committed. Nothing else in the repo is served.
DEST = ROOT / 'docs'
PAGE_ASSETS = {
    'site/index.html': 'index.html',
    'site/styles.css': 'styles.css',
    'site/app.js': 'app.js',
    'site/core.mjs': 'core.mjs',
    'site/field.mjs': 'field.mjs',
    'site/people.mjs': 'people.mjs',
    'site/.nojekyll': '.nojekyll',
}
DATA_ASSETS = {
    'historiography-1920-2000.json': 'data/graph.json',
    'seminar-pathways.json': 'data/pathways.json',
}
BASELINE_ASSET = 'data/graph-2000.json'   # published only when an archived baseline exists
ASSETS = {**PAGE_ASSETS, **DATA_ASSETS}


def slim_journal_catalogue(catalogue):
    """Publish only the journals the site can draw.

    The catalogue is a research inventory of ~1,600 periodicals with their subject
    classifications and review history. The site needs the journals that carry an
    evidenced venue edge, plus the sources those claims cite. Shipping the whole
    catalogue made the browser download 11 MB before rendering anything. The repository
    copy stays authoritative; only this published copy is reduced.
    """
    edges = catalogue.get('edges', [])
    linked = {e['source'] for e in edges}
    nodes = [n for n in catalogue.get('nodes', []) if n['id'] in linked]
    cited = {i for n in nodes for i in n.get('source_ids', [])}
    cited |= {i for e in edges for i in e.get('source_ids', [])}
    kept = {'schema_version', 'as_of', 'scope', 'identity_policy', 'interpretation_note',
            'title_relationships'}
    slim = {k: v for k, v in catalogue.items() if k in kept}
    slim['nodes'] = nodes
    slim['edges'] = edges
    slim['sources'] = [s for s in catalogue.get('sources', []) if s['id'] in cited]
    # Keep the honest count of what exists but is not drawn.
    slim['unlinked_periodical_count'] = sum(
        1 for n in catalogue.get('nodes', [])
        if n.get('entry_kind') == 'periodical' and n['id'] not in linked)
    slim['omitted_from_publication'] = (
        'Subject classifications, review history and unlinked periodicals are omitted from '
        'the published copy for size. See the repository dataset for the full catalogue.')
    return slim


def overlay_people_wikidata(payload):
    """Add accepted Wikidata identities and life dates to the published people records.

    `data/people-wikidata.json` is the reviewed grounding sheet. Only entries with
    status `accepted` are applied, and only onto the published copy: the repository
    dataset is not modified. Each applied record carries its own provenance.
    """
    sheet = ROOT / 'data' / 'people-wikidata.json'
    if not sheet.exists():
        return 0
    rows = json.loads(sheet.read_text())
    accepted = {r['person_id']: r for r in rows.get('people', []) if r.get('status') == 'accepted'}
    applied = 0
    for person in payload.get('people', []):
        row = accepted.get(person['id'])
        if not row:
            continue
        person['wikidata'] = {'qid': row['wikidata']['qid'], 'label': row['wikidata']['label']}
        if row.get('life'):
            person['life'] = {k: row['life'][k] for k in
                              ('birth', 'death', 'birth_precision', 'death_precision', 'retrieved')}
        applied += 1
    if applied:
        payload.setdefault('published_enrichment', []).append({
            'fields': ['people[].wikidata', 'people[].life'],
            'source': 'data/people-wikidata.json',
            'note': 'Applied at build time to the published copy only; the repository dataset '
                    'does not carry these fields. Wikidata content is CC0.',
            'count': applied})
    return applied


def publish_graph(payload):
    """Slim the journal catalogue and overlay accepted Wikidata identities; returns the payload."""
    if 'journal_catalogue' in payload:
        payload['journal_catalogue'] = slim_journal_catalogue(payload['journal_catalogue'])
    if 'people' in payload:
        enriched = overlay_people_wikidata(payload)
        if enriched:
            print(f'  {enriched} people carry Wikidata identities and life dates in the published copy')
    return payload


def build(graph_path=None, dest=None, baseline_path=None):
    graph_path = Path(graph_path) if graph_path else ROOT / 'historiography-1920-2000.json'
    dest = Path(dest).resolve() if dest else DEST
    preview = dest != DEST
    if preview and not str(dest).startswith('/tmp/'):
        raise SystemExit('Preview builds must go under /tmp; docs/ is the production build only.')
    graph = json.loads(graph_path.read_text())
    pathways = json.loads((ROOT / 'seminar-pathways.json').read_text())
    errors, _ = validate(graph, pathways)
    if errors:
        raise SystemExit('\n'.join(errors))
    # Refuse unexpected contents rather than silently publishing or deleting them.
    if dest.is_symlink():
        raise SystemExit('Build directory must not be a symlink.')
    existing = list(dest.rglob('*')) if dest.exists() else []
    if any(p.is_symlink() for p in existing):
        raise SystemExit('Build output must not contain symlinks.')
    allowed = set(ASSETS.values()) | {BASELINE_ASSET}
    unexpected = {str(p.relative_to(dest)) for p in existing if p.is_file()} - allowed
    if unexpected:
        raise SystemExit(f'Unexpected build contents; review before continuing: {sorted(unexpected)}')
    for source, target in PAGE_ASSETS.items():
        out = dest / target
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, out)
    # The 2000 baseline: an archived graph file, never a date filter over the current one.
    extension = graph.get('scope', {}).get('extension')
    baseline = None
    if extension:
        candidate = Path(baseline_path) if baseline_path else (
            ROOT / extension['baseline_graph'] if extension.get('baseline_graph') else None)
        if candidate and candidate.is_file():
            baseline = json.loads(candidate.read_text())
            b_errors, _ = validate(baseline, pathways)
            if b_errors:
                raise SystemExit('Baseline graph fails validation:\n' + '\n'.join(b_errors))
        elif candidate:
            print(f'  Baseline graph {candidate} not found; no 2000 view will be published')
    published = 0
    for source, target in DATA_ASSETS.items():
        out = dest / target
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = graph if target == 'data/graph.json' else json.loads((ROOT / source).read_text())
        payload = publish_graph(json.loads(json.dumps(payload)))
        if target == 'data/graph.json' and extension:
            payload['scope']['extension'] = {**extension, 'baseline_asset': BASELINE_ASSET if baseline else None}
        out.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
        published += 1
    baseline_out = dest / BASELINE_ASSET
    if baseline:
        baseline_out.write_text(json.dumps(publish_graph(baseline), ensure_ascii=False, separators=(',', ':')))
        published += 1
        print(f'  2000 baseline published from {candidate.relative_to(ROOT) if candidate.is_relative_to(ROOT) else candidate}')
    elif baseline_out.exists():
        baseline_out.unlink()
    size = (dest / 'data' / 'graph.json').stat().st_size / 1024 / 1024
    original = graph_path.stat().st_size / 1024 / 1024
    print(f'Built {len(PAGE_ASSETS) + published} allowlisted files in {dest if preview else DEST.relative_to(ROOT)}/')
    print(f'  graph.json published at {size:.2f} MB (dataset is {original:.2f} MB)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--graph', help='graph file to build from (preview only; requires --dest under /tmp)')
    ap.add_argument('--dest', help='output directory for a preview build (must be under /tmp)')
    ap.add_argument('--baseline', help='archived baseline graph to publish as data/graph-2000.json')
    args = ap.parse_args()
    if bool(args.graph) != bool(args.dest):
        ap.error('--graph and --dest go together')
    build(args.graph, args.dest, args.baseline)
