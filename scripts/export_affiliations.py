"""Person -> institution affiliations, dated, for the graph (2026-11-08; user on York, i-1143: "this node and other
departments should feature the faculty who taught there; we should have everyone who advised a PhD at very least and
I think we're expanding that with the reviews"). Writes data/graph/affiliations.csv.gz, one row per person key,
institution (ROR) and source, with the first and last year seen:

- `aha_directory`: the AHA Directory of History Departments (2026 snapshot: last year 2026);
- `aha_advisor`: AHA dissertation records naming the advisor and department (years of the theses);
- `ihr`: IHR 'Teachers of History' staff lists (years of the lists);
- `orcid`, `wikidata`: employment with start and end (data/field-research/historian-positions-2026-10-29), and from
  2026-11-14 the record of EVERY key that holds the identifier (scripts/pid_records.py -> data/graph/pid-records/
  affiliations.csv.gz: ORCID employments, educations, qualifications and invited positions; Wikidata P108 employer,
  P69 educated at, P39 offices with their organisation), §8 class 42;
- `review_credit`: the institution printed with a review the person wrote (H-Net, Reviews in History; review years);
- `jstor_signature`: the institution printed under a JSTOR review the person is credited with (review year);
- `lc_373`: the LC authority's associated institution (an LC corporate name, reaching ROR through Wikidata items
  that carry both ids; start/end where LC gives them).
Institution names reach ROR through the reviewed groundings (data/field-research/institutions-2026-10-31/
institution-strings.csv; the JSTOR session's signature-institutions.csv, accepted only). University systems
('University of California System') place nobody. The person column is the key at export time; scripts/build_graph.py
follows later merges. Rows whose institution has no institution key are counted in the report (by ROR) for minting.

`kind` (2026-11-14) keeps the nature of the tie apart: `employment` (AHA directory and advising, IHR lists, ORCID
employment, Wikidata P108), `education` (ORCID educations and qualifications, Wikidata P69: never mixed into
employment), `position` (ORCID invited positions, Wikidata P39 offices), `affiliation` (a printed institution: review
credits, JSTOR signatures, LC 373). PID rows are grounded by the ROR the record gives (ORCID disambiguated organisation,
the employer item's P6782), then GRID or the item's QID through the ROR dump (a department-level ROR rolls up to its
parent university when only the parent has a key), then by the reviewed name groundings. A ROR with no institution key
is written as `ror:<id>` and listed in data/graph/institutions-unkeyed.csv.gz: the build makes it an unkeyed
Institution node until a key-log proposal (scripts/key_pid_records.py) keys it.

AHA directory rows whose listed rank names another institution ('Canada Research Chair, UPEI' under the University of
New Brunswick) do not assert employment at the listing department and are dropped (rule `aha_rank_names_other`:
an acronym of 4+ letters or a 'University of X' / 'X University' phrase in the rank that resolves, among US and Canadian education records in
the ROR dump, to exactly one organisation that is neither the listing's nor its parent or child).

    python3 scripts/export_affiliations.py
"""
import collections, csv, gzip, json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckdb
from identifiers import State, DEFAULT_DIR
from key_review_credit_merges import jstor_signatures, LC_NOTES
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

ROOT = Path(__file__).resolve().parents[1]
POS = ROOT / 'data/field-research/historian-positions-2026-10-29/positions.csv'
GROUND = ROOT / 'data/field-research/institutions-2026-10-31/institution-strings.csv'
SIGG = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/signature-institutions/signature-institutions.csv'
OUT = ROOT / 'data/graph/affiliations.csv.gz'
REPORT = ROOT / 'data/graph/affiliations-report.json'
LC_ORG_ROR = ROOT / 'data/graph/lc-org-ror.json'      # LC corporate name id -> ROR, via Wikidata (P244 + P6782)
PID_AFF = ROOT / 'data/graph/pid-records/affiliations.csv.gz'   # scripts/pid_records.py (2026-11-14)
UNKEYED = ROOT / 'data/graph/institutions-unkeyed.csv.gz'
ROR_DUMP = Path('/mnt/e/ror/v2.15-2026-10-20/v2.15-2026-10-20-ror-data.csv')
KIND = {'aha_directory': 'employment', 'aha_advisor': 'employment', 'ihr': 'employment', 'orcid': 'employment',
        'wikidata': 'employment', 'review_credit': 'affiliation', 'jstor_signature': 'affiliation', 'lc_373': 'affiliation'}
PID_KIND = {'employment': 'employment', 'education': 'education', 'qualification': 'education', 'position': 'position'}


def lc_org_ror(ids):
    """LC corporate name ids -> ROR ids through Wikidata items carrying both (QLever); cached in data/graph."""
    have = json.loads(LC_ORG_ROR.read_text()) if LC_ORG_ROR.exists() else {}
    want = sorted(set(ids) - set(have.get('_asked', [])))
    if want:
        from held_lc_rules import qlever
        P = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/> '
        asked = []
        for i in range(0, len(want), 100):
            vs = ' '.join(f'"{x}"' for x in want[i:i + 100])
            try:
                got = qlever(P + 'SELECT ?lc ?ror WHERE { VALUES ?lc {%s} ?item wdt:P244 ?lc ; wdt:P6782 ?ror }' % vs)
            except SystemExit:          # QLever down: keep the cache, ask again on the next run
                print('lc_org_ror: QLever failed; these LC ids are asked again next run', file=sys.stderr)
                continue
            for b in got:
                have[b['lc']['value']] = b['ror']['value']
            asked += want[i:i + 100]
        have['_asked'] = sorted(set(have.get('_asked', [])) | set(asked))
        LC_ORG_ROR.write_text(json.dumps(have, indent=0, sort_keys=True))
    return {k: v for k, v in have.items() if k != '_asked'}
G = ROOT / 'build/graph'


def ror_dump(path=ROR_DUMP):
    """The ROR dump: {id: record} with names, acronyms, country, types, status, wikidata, grid and relationships."""
    out = {}
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            k = r['id'].rsplit('/', 1)[-1]
            rel = collections.defaultdict(list)
            for x in (r['relationships'] or '').split(';'):
                if ':' in x:
                    t, _, u = x.strip().partition(': ')
                    rel[t.strip()].append(u.strip().rsplit('/', 1)[-1])
            strip = lambda v: [re.sub(r'^[a-z_]{2,12}: ', '', x.strip()) for x in (v or '').split(';') if x.strip()]
            out[k] = dict(name=r['names.types.ror_display'], country=r['locations.geonames_details.country_code'],
                          types=r['types'], status=r['status'], rel=dict(rel),
                          names=strip(r['names.types.ror_display']) + strip(r['names.types.label']) + strip(r['names.types.alias']),
                          acronyms=strip(r['names.types.acronym']),
                          wikidata=[x.strip() for x in (r['external_ids.type.wikidata.all'] or '').split(';') if x.strip()],
                          grid=[x.strip() for x in (r['external_ids.type.grid.all'] or '').split(';') if x.strip()])
    return out


ACRONYM = re.compile(r'\b[A-Z][A-Z&]{3,7}\b')     # 4+ letters: 'SBS' (a school of the listing) is not 'Stony Brook School'
# universities only: 'Baker College' in a Rice rank is a residential college of Rice, not Baker College (Michigan)
INST_PHRASE = re.compile(r"\b(?:(?:Univ\.?|University) of (?:[A-Z][\w'.&-]*\s?)+|(?:[A-Z][\w'.&-]*\s)+(?:Univ\.?|University)(?=\W|$))")


def rank_names_other(rank, listing_ror, rors, index):
    """The ROR of another institution the AHA directory rank names ('Canada Research Chair, UPEI'), or None."""
    if not rank or not listing_ror:
        return None
    found = set()
    for m in ACRONYM.findall(rank):
        found |= index['acr'].get(m, set()) if len(index['acr'].get(m, ())) == 1 else set()
    for m in INST_PHRASE.findall(rank):
        t = re.sub(r'\bUniv\.?(?=\W|$)', 'University', m.strip())
        t = re.sub(r'\bColl\.?(?=\W|$)', 'College', t).strip().lower()
        if len(index['name'].get(t, ())) == 1:
            found |= index['name'][t]
    near = {listing_ror} | set(sum(((rors.get(listing_ror) or {}).get('rel') or {}).values(), []))
    other = {r for r in found if r not in near and listing_ror not in sum(((rors.get(r) or {}).get('rel') or {}).values(), [])}
    return sorted(other)[0] if len(other) == 1 else None


def nkey(s):
    """An organisation name for exact matching: accents, case, punctuation and a leading 'The' dropped."""
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    return re.sub(r'^the ', '', s)


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
    rors = ror_dump()
    rows = collections.defaultdict(lambda: dict(first=None, last=None, n=0, rank=None, department=None, printed=None))
    rep = collections.Counter(); lost = collections.Counter(); unkeyed = collections.defaultdict(collections.Counter)

    def place(r):
        """An institution node for a ROR: its key, else a keyed parent (a department-level ROR rolls up), else ror:<id>."""
        if r in inst:
            return inst[r]
        rec = rors.get(r) or {}
        for succ in rec.get('rel', {}).get('successor', []):
            if succ in inst:
                return inst[succ]
        par = [x for x in rec.get('rel', {}).get('parent', []) if x in inst]
        if len(par) == 1 and 'education' not in rec.get('types', ''):
            return inst[par[0]]
        return None

    def add(person, institution, source, y0=None, y1=None, rank=None, dept=None, kind=None, r=None, unkeyed_ok=False,
            open_end=False):
        kind = kind or KIND.get(source, 'affiliation')
        if not person:
            rep[f'{source}: person not keyed'] += 1; return
        r = r or ror.get(clean(institution))
        if not r:
            rep[f'{source}: institution not grounded'] += 1; return
        node = place(r)
        if not node:
            lost[r] += 1
            if not unkeyed_ok or r not in rors:
                rep[f'{source}: no institution key'] += 1; return
            node = f'ror:{r}'
            unkeyed[r][institution] += 1
            rep[f'{source}: kept on an unkeyed institution'] += 1
        k = rows[(person, node, source, kind)]
        if open_end:                    # a post with a start and no end stays open ('2014–'), not '2014' (2026-11-14)
            if y0:
                k['first'] = min(k['first'], y0) if k['first'] else y0
            if y1:
                k['last'] = max(k['last'], y1) if k['last'] else y1
        else:
            ys = [y for y in (y0, y1) if y]
            if ys:
                k['first'] = min([k['first']] + ys) if k['first'] else min(ys)
                k['last'] = max([k['last']] + ys) if k['last'] else max(ys)
        k['n'] += 1
        k['rank'] = k['rank'] or rank; k['department'] = k['department'] or dept; k['printed'] = k['printed'] or institution
        rep[f'{source}: kept'] += 1
        rep[f'{source}:{kind}: kept'] += 1

    def key_of(anchor):
        r = state.lookup(anchor)
        return r[0] if len(r) == 1 and state.keys[r[0]]['type'] == 'person' else None

    yr = lambda v: int(v) if v not in (None, '') and str(v)[:4].isdigit() else None
    rank_index = dict(acr=collections.defaultdict(set), name=collections.defaultdict(set))
    for k, rec in rors.items():
        if rec['status'] == 'active' and rec['country'] in ('US', 'CA') and 'education' in rec['types']:
            for a in rec['acronyms']:
                rank_index['acr'][a].add(k)
            for n in rec['names']:
                rank_index['name'][n.lower()].add(k)
    aha_other = []
    pid_ungrounded = collections.Counter()
    for ref, institution, dept, rank, y0, y1, obs, src in db.execute(f"""SELECT person_ref, institution, department, rank,
            start_year, end_year, observed_year, source FROM '{POS}' WHERE institution IS NOT NULL""").fetchall():
        if src == 'aha_directory':
            y0, y1 = None, 2026
            other = rank_names_other(rank, ror.get(clean(institution)), rors, rank_index)
            if other:
                rep['aha_directory: rank names another institution (dropped)'] += 1
                aha_other.append(dict(person=key_of(ref) or '', ref=ref, institution=institution, rank=rank, other_ror=other,
                                      other_name=rors[other]['name']))
                continue
        elif src in ('ihr', 'aha_advisor'):
            y0 = y1 = yr(obs)
        add(key_of(ref), institution, src, yr(y0), yr(y1), rank, dept, open_end=src in ('orcid', 'wikidata'))

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
    for p, w in db.execute(f"""SELECT "from", "to" FROM {keylog(G, 'authored')} WHERE "to" IN (SELECT unnest(?))""", [list(review_doi)]).fetchall():
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

    # every key's own ORCID record and Wikidata item (scripts/pid_records.py, 2026-11-14; §8 class 42)
    if PID_AFF.exists():
        grid = {g: k for k, rec in rors.items() for g in rec['grid']}
        wdmap = collections.defaultdict(set)
        for k, rec in rors.items():
            for q in rec['wikidata']:
                wdmap[q].add(k)
        how = collections.Counter()
        exact = collections.defaultdict(set)
        for k, rec in rors.items():
            if rec['status'] == 'active':
                for n in set(rec['names']):
                    exact[nkey(n)].add(k)
        with gzip.open(PID_AFF, 'rt', newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                kind = PID_KIND.get(r['kind'], r['kind'])
                cand = [x for x in r['org_ror'].split(';') if x in rors]
                via = 'ror'
                if not cand and r['org_grid'] in grid:
                    cand, via = [grid[r['org_grid']]], 'grid'
                if not cand and len(wdmap.get(r['org_wd'], ())) == 1:
                    cand, via = list(wdmap[r['org_wd']]), 'wikidata-qid'
                if not cand and ror.get(clean(r['org_name'])):
                    cand, via = [ror[clean(r['org_name'])]], 'name'
                    # the name groundings carry no country: an ORCID row in GB is not Universidade Aberta (PT) by
                    # 'Open University' (hand check 2026-11-14)
                    if len(r['country']) == 2 and rors.get(cand[0], {}).get('country') not in (r['country'], None):
                        how[f"{r['source']}:{kind}: name grounding refused on country"] += 1
                        cand = []
                if not cand:            # the exact name (or alias) of one active ROR organisation, in the row's country
                    hit = [x for x in exact.get(nkey(r['org_name']), ()) if len(r['country']) != 2 or rors[x]['country'] == r['country']]
                    if len(hit) == 1:
                        cand, via = hit, 'ror-exact-name'
                if not cand:
                    how[f"{r['source']}:{kind}: not grounded" + (' (ringgold only)' if r['org_ringgold'] else '')] += 1
                    pid_ungrounded[(r['source'], r['org_name'], r['org_wd'] or r['org_ringgold'] or r['org_grid'], r['country'])] += 1
                    rep[f"{r['source']}: institution not grounded"] += 1
                    continue
                how[f"{r['source']}:{kind}: by {via}"] += 1
                rank = r['role'] if kind != 'education' else ('; '.join(x for x in (r['degree'], r['role']) if x))
                add(r['person'], r['org_name'] or rors[cand[0]]['name'], r['source'], yr(r['start_year']), yr(r['end_year']),
                    rank or None, r['department'] or None, kind=kind, r=cand[0], unkeyed_ok=True, open_end=True)
        rep.update({f'pid grounding {k}': v for k, v in how.items()})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['person', 'institution', 'source', 'kind', 'first_year', 'last_year', 'n', 'rank', 'department', 'printed'])
        for (p, node, s, kind), v in sorted(rows.items()):
            wr.writerow([p, node, s, kind, v['first'] or '', v['last'] or '', v['n'], v['rank'] or '', v['department'] or '', v['printed'] or ''])
    with gzip.open(UNKEYED, 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['ror', 'name', 'country', 'types', 'wikidata', 'rows', 'printed'])
        for r, names in sorted(unkeyed.items(), key=lambda x: -sum(x[1].values())):
            rec = rors[r]
            wr.writerow([r, rec['name'], rec['country'], rec['types'], ';'.join(rec['wikidata']), sum(names.values()),
                         ' | '.join(n for n, _ in names.most_common(8))])
    with gzip.open(ROOT / 'data/graph/pid-records/ungrounded-institutions.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['source', 'name', 'id', 'country', 'rows'])
        for (src, name, i, c), n in pid_ungrounded.most_common():
            wr.writerow([src, name, i, c, n])
    with open(ROOT / 'data/graph/aha-rank-names-other.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=['person', 'ref', 'institution', 'rank', 'other_ror', 'other_name'])
        wr.writeheader(); wr.writerows(aha_other)
    json.dump(dict(counts=dict(sorted(rep.items())), rows=len(rows),
                   rows_by_kind=dict(collections.Counter(k[3] for k in rows)),
                   unkeyed_institutions=len(unkeyed), unkeyed_institution_rows=sum(sum(v.values()) for v in unkeyed.values()),
                   pid_ungrounded_names=len(pid_ungrounded), pid_ungrounded_rows=sum(pid_ungrounded.values()),
                   rors_without_institution_key=dict(lost.most_common(300))), open(REPORT, 'w'), indent=1)
    print(json.dumps(dict(sorted(rep.items())), indent=1), len(rows), 'rows;', len(lost), 'RORs without an institution key')

if __name__ == '__main__':
    main()
