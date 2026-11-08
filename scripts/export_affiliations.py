"""Person -> institution affiliations, dated, for the graph (2026-11-08; user on York, i-1143: "this node and other
departments should feature the faculty who taught there; we should have everyone who advised a PhD at very least and
I think we're expanding that with the reviews"). Writes data/graph/affiliations.csv.gz, one row per person key,
institution (ROR) and source, with the first and last year seen:

- `aha_directory`: the AHA Directory of History Departments (2026 snapshot: last year 2026);
- `aha_advisor`: AHA dissertation records naming the advisor and department (years of the theses);
- `ihr`: IHR 'Teachers of History' staff lists (years of the lists);
- `orcid`, `wikidata`: employment with start and end (data/field-research/historian-positions-2026-10-29);
- `review_credit`: the institution printed with a review the person wrote (H-Net, Reviews in History; review years);
- `jstor_signature`: the institution printed under a JSTOR review the person is credited with (review year);
- `lc_373`: the LC authority's associated institution (an LC corporate name, reaching ROR through Wikidata items
  that carry both ids; start/end where LC gives them).
Institution names reach ROR through the reviewed groundings (data/field-research/institutions-2026-10-31/
institution-strings.csv; the JSTOR session's signature-institutions.csv, accepted only). University systems
('University of California System') place nobody. The person column is the key at export time; scripts/build_graph.py
follows later merges. Rows whose institution has no institution key are counted in the report (by ROR) for minting.

    python3 scripts/export_affiliations.py
"""
import collections, csv, gzip, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckdb
from identifiers import State, DEFAULT_DIR
from key_review_credit_merges import jstor_signatures, LC_NOTES

ROOT = Path(__file__).resolve().parents[1]
POS = ROOT / 'data/field-research/historian-positions-2026-10-29/positions.csv'
GROUND = ROOT / 'data/field-research/institutions-2026-10-31/institution-strings.csv'
SIGG = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/signature-institutions/signature-institutions.csv'
OUT = ROOT / 'data/graph/affiliations.csv.gz'
REPORT = ROOT / 'data/graph/affiliations-report.json'
LC_ORG_ROR = ROOT / 'data/graph/lc-org-ror.json'      # LC corporate name id -> ROR, via Wikidata (P244 + P6782)


def lc_org_ror(ids):
    """LC corporate name ids -> ROR ids through Wikidata items carrying both (QLever); cached in data/graph."""
    have = json.loads(LC_ORG_ROR.read_text()) if LC_ORG_ROR.exists() else {}
    want = sorted(set(ids) - set(have.get('_asked', [])))
    if want:
        from held_lc_rules import qlever
        P = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/> '
        for i in range(0, len(want), 400):
            vs = ' '.join(f'"{x}"' for x in want[i:i + 400])
            for b in qlever(P + 'SELECT ?lc ?ror WHERE { VALUES ?lc {%s} ?item wdt:P244 ?lc ; wdt:P6782 ?ror }' % vs):
                have[b['lc']['value']] = b['ror']['value']
        have['_asked'] = sorted(set(have.get('_asked', [])) | set(want))
        LC_ORG_ROR.write_text(json.dumps(have, indent=0, sort_keys=True))
    return {k: v for k, v in have.items() if k != '_asked'}
G = ROOT / 'build/graph'


def clean(s):
    return re.sub(r'\s+', ' ', (s or '').strip().strip('.,;')).lower()


def main():
    state = State.load(DEFAULT_DIR)
    db = duckdb.connect(); db.execute('SET enable_progress_bar=false')
    ror = {}
    for s, r in db.execute(f"""SELECT string, ror FROM '{GROUND}' WHERE decision IN ('accepted', 'reviewed') AND ror IS NOT NULL""").fetchall():
        ror[clean(s)] = r.rsplit('/', 1)[-1]
    for s, c, r, name in db.execute(f"""SELECT string, cleaned, ror, ror_name FROM '{SIGG}' WHERE decision = 'accepted' AND ror IS NOT NULL""").fetchall():
        if ' system' in (name or '').lower():
            continue
        ror.setdefault(clean(s), r.rsplit('/', 1)[-1]); ror.setdefault(clean(c), r.rsplit('/', 1)[-1])
    inst = {a[4:]: k for a, k in state.anchor.items() if a.startswith('ror:')}
    rows = collections.defaultdict(lambda: dict(first=None, last=None, n=0, rank=None, department=None, printed=None))
    rep = collections.Counter(); lost = collections.Counter()

    def add(person, institution, source, y0=None, y1=None, rank=None, dept=None):
        if not person:
            rep[f'{source}: person not keyed'] += 1; return
        r = ror.get(clean(institution))
        if not r:
            rep[f'{source}: institution not grounded'] += 1; return
        if r not in inst:
            rep[f'{source}: no institution key'] += 1; lost[r] += 1; return
        k = rows[(person, r, source)]
        ys = [y for y in (y0, y1) if y]
        if ys:
            k['first'] = min([k['first']] + ys) if k['first'] else min(ys)
            k['last'] = max([k['last']] + ys) if k['last'] else max(ys)
        k['n'] += 1
        k['rank'] = k['rank'] or rank; k['department'] = k['department'] or dept; k['printed'] = k['printed'] or institution
        rep[f'{source}: kept'] += 1

    def key_of(anchor):
        r = state.lookup(anchor)
        return r[0] if len(r) == 1 and state.keys[r[0]]['type'] == 'person' else None

    yr = lambda v: int(v) if v not in (None, '') and str(v)[:4].isdigit() else None
    for ref, institution, dept, rank, y0, y1, obs, src in db.execute(f"""SELECT person_ref, institution, department, rank,
            start_year, end_year, observed_year, source FROM '{POS}' WHERE institution IS NOT NULL""").fetchall():
        if src == 'aha_directory':
            y0, y1 = None, 2026
        elif src in ('ihr', 'aha_advisor'):
            y0 = y1 = yr(obs)
        add(key_of(ref), institution, src, yr(y0), yr(y1), rank, dept)

    # review credits ('review-credit:<name>|<institution>'), dated by the reviews filed under the anchor
    wy = dict(db.execute(f"SELECT key, year FROM '{G}/work.parquet' WHERE year IS NOT NULL").fetchall())
    credit_years = collections.defaultdict(set)
    for c, r in state.relation.items():
        if r['subject'].startswith('review-credit:') and state.keys[c]['status'] not in ('withdrawn', 'merged'):
            for w in state.lookup(r['object']):
                if wy.get(w):
                    credit_years[r['subject']].add(wy[w])
    for k, v in state.keys.items():
        if v['type'] != 'person' or v['status'] not in ('active', 'provisional'):
            continue
        for a in v['anchors']:
            if a.startswith('review-credit:') and '|' in a:
                ys = sorted(credit_years.get(a, ()))
                add(k, a.split('|', 1)[1], 'review_credit', ys[0] if ys else None, ys[-1] if ys else None)

    # JSTOR review signatures: the printed institution, for each person credited with the review (authored claim)
    sig = jstor_signatures()
    review_doi = {}
    for w, an in db.execute(f"""SELECT key, an FROM (SELECT key, unnest(anchors) an FROM '{G}/work.parquet') WHERE an LIKE 'doi:%'""").fetchall():
        if an[4:].lower() in sig:
            review_doi[w] = an[4:].lower()
    for p, w in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE "to" IN (SELECT unnest(?))""", [list(review_doi)]).fetchall():
        creator, institution, y = sig[review_doi[w]]
        add(key_of(p) or p, institution, 'jstor_signature', yr(y), yr(y))

    # LC authority 373 (associated institution)
    lc = {a[6:]: k for a, k in state.anchor.items() if a.startswith('lcnaf:') and state.keys[k]['type'] == 'person'}
    if LC_NOTES.exists():
        db.register('want', db.execute('SELECT unnest(?) AS lcid', [list(lc)]).df())
        lcaff = db.execute(f"SELECT lcid, affiliations FROM read_parquet('{LC_NOTES}') JOIN want USING (lcid) WHERE len(affiliations) > 0").fetchall()
        orgs = lc_org_ror({a['org'] for _, affs in lcaff for a in affs if a['org']})
        for o, r in orgs.items():
            ror['lcorg:' + o] = r
        for lcid, affs in lcaff:
            for a in affs:
                if a['org']:
                    add(lc[lcid], 'lcorg:' + a['org'], 'lc_373', yr(str(a['start'] or '')[:4]), yr(str(a['end'] or '')[:4]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['person', 'institution', 'source', 'first_year', 'last_year', 'n', 'rank', 'department', 'printed'])
        for (p, r, s), v in sorted(rows.items()):
            wr.writerow([p, inst[r], s, v['first'] or '', v['last'] or '', v['n'], v['rank'] or '', v['department'] or '', v['printed'] or ''])
    json.dump(dict(counts=dict(sorted(rep.items())), rows=len(rows),
                   rors_without_institution_key=dict(lost.most_common(300))), open(REPORT, 'w'), indent=1)
    print(json.dumps(dict(sorted(rep.items())), indent=1), len(rows), 'rows;', len(lost), 'RORs without an institution key')


if __name__ == '__main__':
    main()
