"""Build only explicitly approved public assets; never serve the repository root."""
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
    'site/.nojekyll': '.nojekyll',
}
DATA_ASSETS = {
    'historiography-1920-2000.json': 'data/graph.json',
    'seminar-pathways.json': 'data/pathways.json',
}
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


def build():
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    pathways = json.loads((ROOT / 'seminar-pathways.json').read_text())
    errors, _ = validate(graph, pathways)
    if errors:
        raise SystemExit('\n'.join(errors))
    # Refuse unexpected contents rather than silently publishing or deleting them.
    if DEST.is_symlink():
        raise SystemExit('Build directory must not be a symlink.')
    existing = list(DEST.rglob('*')) if DEST.exists() else []
    if any(p.is_symlink() for p in existing):
        raise SystemExit('Build output must not contain symlinks.')
    unexpected = {str(p.relative_to(DEST)) for p in existing if p.is_file()} - set(ASSETS.values())
    if unexpected:
        raise SystemExit(f'Unexpected build contents; review before continuing: {sorted(unexpected)}')
    for source, target in PAGE_ASSETS.items():
        out = DEST / target
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, out)
    for source, target in DATA_ASSETS.items():
        out = DEST / target
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = json.loads((ROOT / source).read_text())
        if 'journal_catalogue' in payload:
            payload['journal_catalogue'] = slim_journal_catalogue(payload['journal_catalogue'])
        out.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    published = (DEST / 'data' / 'graph.json').stat().st_size / 1024 / 1024
    original = (ROOT / 'historiography-1920-2000.json').stat().st_size / 1024 / 1024
    print(f'Built {len(ASSETS)} allowlisted files in {DEST.relative_to(ROOT)}/')
    print(f'  graph.json published at {published:.2f} MB (dataset is {original:.2f} MB)')


if __name__ == '__main__':
    build()
