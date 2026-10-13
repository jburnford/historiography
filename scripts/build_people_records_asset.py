"""Build a small, source-linked profile pilot from registry v9; never match by name.

Only public work/review metadata is exported. No affiliations, review text, abstracts,
ORCID profile contents or local capture paths enter the browser asset.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlparse

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/evidence-layer'
PILOT = ('paul_e_lovejoy', 'geoff_eley', 'serge_noiret', 'lorraine_daston',
         'jay_winter', 'peter_galison', 'ida_altman', 'joel_mokyr')
TIERS = {'accepted': 0, 'anchored': 1, 'probable': 2}


def effective_tier(atlas, credit):
    if atlas not in TIERS or credit not in TIERS:
        raise ValueError('Unresolved or conflicted identity must not be published')
    return max((atlas, credit), key=TIERS.get)


def public_url(url):
    p = urlparse(url or '')
    return url if p.scheme in ('http', 'https') and p.netloc and not p.username and not p.password else None


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--registry', default='v9')
    ap.add_argument('--out', type=Path, default=DATA / 'site-people.json')
    args = ap.parse_args()
    registry = ROOT / 'data/person-registry/generated' / args.registry / 'registry.duckdb'
    hn_path = ROOT / 'data/hnet-graph/generated/graph.sqlite'
    node_path = ROOT / 'data/unified-graph/generated/nodes.csv'
    catalogues = [ROOT / 'data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb',
                  ROOT / 'data/history-journals-supplement-2026-09-26/generated/v1/catalog.duckdb']
    paths = [registry, hn_path, node_path, *catalogues, ROOT / 'historiography-1920-2000.json', Path(__file__).resolve()]
    before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    db = duckdb.connect(str(registry), read_only=True)
    hn = sqlite3.connect(f'file:{hn_path}?mode=ro', uri=True)
    xr = [duckdb.connect(str(p), read_only=True) for p in catalogues]
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    labels = {p['id']: p['label'] for p in graph['people']}
    out = {}
    for pid in PILOT:
        row = db.execute('SELECT individual_id,status,bases FROM occurrence_resolution WHERE occurrence_id=?',
                         ['atlas:person:'+pid]).fetchone()
        if not row or not row[0] or row[1] not in TIERS:
            raise ValueError('Pilot atlas identity is unresolved: '+pid)
        individual, atlas_tier, atlas_bases = row
        credits = db.execute('''SELECT o.occurrence_id,o.corpus,o.record_id,o.item_id,o.role,r.status,r.bases
            FROM occurrences o JOIN occurrence_resolution r USING(occurrence_id)
            WHERE r.individual_id=? AND o.corpus<>'atlas' ORDER BY o.corpus,o.record_id,o.item_id,o.role''', [individual]).fetchall()
        records = []
        for occurrence, corpus, rid, item, role, tier, bases in credits:
            title, year, review_year, venue, url = None, None, None, None, None
            if corpus == 'crossref':
                meta = next((m for c in xr if (m := c.execute(
                    'SELECT title_text,publication_year,container_title,doi,record_type FROM records WHERE record_id=?', [rid]).fetchone())), None)
                if not meta:
                    raise ValueError('Missing Crossref metadata: '+rid)
                title, year, venue, doi, record_type = meta
                kind = 'journal_item'
                url = 'https://doi.org/'+doi
            elif corpus == 'hnet':
                review = hn.execute('''SELECT r.date_month,n.label,s.source_url,s.wayback_url FROM reviews r
                    LEFT JOIN nodes n ON n.id=r.network_id JOIN sources s ON s.id=r.source_id WHERE r.id=?''', [rid]).fetchone()
                if not review:
                    raise ValueError('Missing review metadata: '+rid)
                date, venue, url, archive = review
                review_year = int(date[:4]) if date else None
                url = public_url(url) or public_url(archive)
                if role == 'reviewer':
                    works = hn.execute('''SELECT i.title FROM edges e JOIN items i ON i.id=e.object
                        WHERE e.subject=? AND e.predicate='reviews_item' ORDER BY i.id''', [rid]).fetchall()
                    title, year, kind = '; '.join(w[0] for w in works), review_year, 'review_written'
                else:
                    work = hn.execute('SELECT title,publication_year FROM items WHERE id=?', [item]).fetchone()
                    if not work:
                        raise ValueError('Missing reviewed item: '+str(item))
                    title, year = work
                    kind = 'reviewed_book'
            elif corpus == 'rih':
                # Read only the selected review and source rows; their essay bodies stay local.
                scan = duckdb.connect()
                node = scan.execute("SELECT label,data FROM read_csv(?,all_varchar=true,max_line_size=20000000) WHERE id=?", [str(node_path),rid]).fetchone()
                if not node:
                    raise ValueError('Missing RiH review: '+rid)
                title, data = node[0], json.loads(node[1])
                meta = data.get('metadata', {})
                date = meta.get('date_month')
                review_year = int(date[:4]) if date else None
                source = scan.execute("SELECT data FROM read_csv(?,all_varchar=true,max_line_size=20000000) WHERE id=?", [str(node_path),meta.get('source_id')]).fetchone()
                source = json.loads(source[0]) if source else {}
                url = source.get('source_url') or source.get('url') or source.get('wayback_url')
                venue = 'Reviews in History'
                kind = 'review_written' if role == 'reviewer' else 'reviewed_book'
                year = review_year if role == 'reviewer' else None
                scan.close()
            else:
                raise ValueError('Unknown corpus: '+corpus)
            if not title or not public_url(url):
                raise ValueError('Missing public title or source link: '+rid)
            records.append(dict(id=occurrence, source_id=rid, item_id=item, kind=kind, title=title,
                year=year, review_year=review_year, venue=venue, role=role, url=public_url(url),
                identity_tier=effective_tier(atlas_tier,tier), credit_tier=tier, identity_bases=bases))
        out[pid] = dict(label=labels[pid], atlas_identity_tier=atlas_tier, atlas_identity_bases=atlas_bases,
            counts={k:len({(r['item_id'] if k=='reviewed_book' else r['source_id']) for r in records if r['kind']==k})
                    for k in ('journal_item','reviewed_book','review_written')}, records=records)
    hn.close()
    db.close()
    for c in xr:
        c.close()
    if before != {str(p.relative_to(ROOT)):sha(p) for p in paths}:
        raise ValueError('Source changed during profile build')
    asset = dict(schema_version='1.0', registry_version=args.registry,
        coverage='Eight atlas profiles, linked through the frozen registry snapshot to selected H-Net, Reviews in History and Crossref records. This is a pilot, not a complete bibliography.',
        identity_note='The displayed tier is the weaker of the atlas-to-person match and the source-credit match. Probable matches need review; counts do not establish influence.',
        people=out)
    args.out.write_text(json.dumps(asset,ensure_ascii=False,indent=1)+'\n')
    audit = DATA / 'audits/people-records-2026-10-10.json'
    audit.parent.mkdir(parents=True,exist_ok=True)
    audit.write_text(json.dumps(dict(inputs=before,registry_version=args.registry,profile_ids=list(PILOT),
        output_sha256=sha(args.out),records=sum(len(p['records']) for p in out.values())),indent=2)+'\n')
    print(f'{len(out)} profiles; {sum(len(p["records"]) for p in out.values())} source credits; {args.out.stat().st_size} bytes')


if __name__ == '__main__':
    main()
