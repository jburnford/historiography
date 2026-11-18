"""Place layer, step 4: the tracked tables in data/graph/places/ (2026-11-18).

Places are a derived layer, not key-log keys: place identity is the Wikidata QID, the LC authority id and heading
are kept as anchors and provenance. Place facts attach to works, never to people (user 2026-11-18); a person's
places are computed from their works at query time. Places only: no nations or peoples.

Inputs (git-ignored working files; see data/graph/places/README.md for how each was made):
  build/places/uses.parquet        every LC place heading on a graph book, grounded (scripts/places_lc.py on spark)
  build/places/auth.parquet        NAF and LCSH geographic authorities (labels, variants, QIDs)
  build/places/wd*/                Wikidata facts by QID (scripts/places_wikidata.py)
  build/places/title-tags.parquet  title-rule tags (scripts/places_titles.py tag)
  data/field-research/place-nodes-scoping-2026-11-18/*-works-checked.csv   the pilot's full hand reading
Outputs (tracked): data/graph/places/
  work-places.csv.gz      work -> place rows: work, qid, place_label, source, heading, lc_id, confidence
  places.csv.gz           one row per place QID
  place-hierarchy.csv.gz  child, parent, basis
  ungrounded.csv.gz       LC place headings on graph books that did not ground to a place QID, with counts
  report.json             counts

    python3 scripts/places_build.py
"""
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build/places'
OUT = ROOT / 'data/graph/places'
PILOT = ROOT / 'data/field-research/place-nodes-scoping-2026-11-18'

# kind classes (scripts/places_wikidata.py CLASSES), in order of precedence
COUNTRY = {'Q6256', 'Q3624078', 'Q1763527'}
SETTLEMENT = {'Q486972', 'Q515'}
HISTORICAL = {'Q3024240', 'Q133156', 'Q164142', 'Q417175', 'Q19953632'}
ADMIN = {'Q10864048', 'Q107390', 'Q56061'}
FEATURE = {'Q15324', 'Q4022', 'Q23442', 'Q8502', 'Q46831', 'Q271669', 'Q473972', 'Q839954'}
REGION = {'Q82794', 'Q1620908', 'Q5107'}
STRUCTURE = {'Q34442', 'Q83620', 'Q41176', 'Q811979'}
PEOPLES = {'Q41710', 'Q2472587', 'Q33829'}
NATION_LABEL = re.compile(r'\b(Nation|Tribe|Band|Indians|people)\b')

FICTION = re.compile(r'(?i) -- (juvenile )?(fiction|drama|poetry|comic books, strips, etc|graphic novels)\b')

# LC abbreviations used as qualifiers (LC rule: AACR2 Appendix B / LC-PCC PS 16.2.2.9)
ABBR = {
    'Alta.': 'Alberta', 'B.C.': 'British Columbia', 'Man.': 'Manitoba', 'N.B.': 'New Brunswick', 'N.L.': 'Newfoundland and Labrador',
    'Nfld.': 'Newfoundland and Labrador', 'N.S.': 'Nova Scotia', 'N.W.T.': 'Northwest Territories', 'Ont.': 'Ontario',
    'P.E.I.': 'Prince Edward Island', 'Québec': 'Québec (Province)', 'Sask.': 'Saskatchewan', 'Yukon': 'Yukon',
    'Ala.': 'Alabama', 'Ariz.': 'Arizona', 'Ark.': 'Arkansas', 'Calif.': 'California', 'Colo.': 'Colorado', 'Conn.': 'Connecticut',
    'Del.': 'Delaware', 'D.C.': 'Washington (D.C.)', 'Fla.': 'Florida', 'Ga.': 'Georgia', 'Ill.': 'Illinois', 'Ind.': 'Indiana',
    'Kan.': 'Kansas', 'Ky.': 'Kentucky', 'La.': 'Louisiana', 'Me.': 'Maine', 'Md.': 'Maryland', 'Mass.': 'Massachusetts',
    'Mich.': 'Michigan', 'Minn.': 'Minnesota', 'Miss.': 'Mississippi', 'Mo.': 'Missouri', 'Mont.': 'Montana', 'Neb.': 'Nebraska',
    'Nev.': 'Nevada', 'N.H.': 'New Hampshire', 'N.J.': 'New Jersey', 'N.M.': 'New Mexico', 'N.Y.': 'New York (State)',
    'N.C.': 'North Carolina', 'N.D.': 'North Dakota', 'Okla.': 'Oklahoma', 'Or.': 'Oregon', 'Pa.': 'Pennsylvania',
    'R.I.': 'Rhode Island', 'S.C.': 'South Carolina', 'S.D.': 'South Dakota', 'Tenn.': 'Tennessee', 'Tex.': 'Texas',
    'Vt.': 'Vermont', 'Va.': 'Virginia', 'Wash.': 'Washington (State)', 'W. Va.': 'West Virginia', 'Wis.': 'Wisconsin',
    'Wyo.': 'Wyoming', 'A.C.T.': 'Australian Capital Territory', 'N.S.W.': 'New South Wales', 'N.T.': 'Northern Territory',
    'Qld.': 'Queensland', 'S. Aust.': 'South Australia', 'Tas.': 'Tasmania', 'Vic.': 'Victoria', 'W.A.': 'Western Australia',
}

# the pilot's checked matches (gazetteer names) -> the place they tag. The renamed island is tagged to the territory
# (Sri Lanka, as LC does); the period polity only when the title names it (Kandyan / Kingdom of Kandy).
CHECKED_PLACES = {
    'Sri Lanka': 'Q854', 'British Ceylon': 'Q854', 'Ceylon (other languages)': 'Q854', 'Taprobane/Serendib': 'Q854',
    'Kingdom of Kandy': 'Q1530762', 'Kandy': 'Q203197', 'Colombo': 'Q35381', 'Jaffna': 'Q215277', 'Galle': 'Q319366',
    'Trincomalee': 'Q323873', 'Batticaloa': 'Q810963', 'Anuradhapura': 'Q5724', 'Polonnaruwa': 'Q394443',
    'Kotte': 'Q41963', 'Nuwara Eliya': 'Q1340579', 'Uva': 'Q876293', 'Sabaragamuwa': 'Q853272', 'Matara': 'Q13360574',
    'Negombo': 'Q668616', 'Badulla': 'Q390096', 'Ratnapura': 'Q508753', 'Kurunegala': 'Q776887', 'Mannar': 'Q1280127',
    'Sigiriya': 'Q272153', "Adam's Peak": 'Q60789', 'Vanni': 'Q15076760',
    'Saskatchewan': 'Q1989', 'Prince Albert': 'Q671431', 'Saskatoon': 'Q10566', 'Regina': 'Q2123', 'Moose Jaw': 'Q1019496',
    'Batoche': 'Q810869', 'Duck Lake': 'Q1427938', 'Battleford': 'Q619597', 'Swift Current': 'Q619937', 'Yorkton': 'Q1639696',
    'Estevan': 'Q1018271', 'Weyburn': 'Q1904554', 'Lloydminster': 'Q985674', "Qu'Appelle": 'Q391566',
    'Cypress Hills': 'Q1148229', 'Cumberland House': 'Q5193906', 'Île-à-la-Crosse': 'Q3496338', 'La Ronge': 'Q2782497',
    'Fort Carlton': 'Q164074', 'Wood Mountain': 'Q22634142', 'Gravelbourg': 'Q994920', 'Humboldt': 'Q1904018',
    'Assiniboia (district)': 'Q18100035', 'Lake Athabasca': 'Q272463',
}
# rows the pilot read as another place of the same name family that the demo still wants, tagged to that place
CHECKED_OTHER = {('river', 'Saskatchewan'): 'Q3047',                                    # Saskatchewan River
                 ('other_place', 'Prince Albert'): 'Q1122878'}                          # Prince Albert National Park
# period nodes Wikidata does not link into the succession chain (pilot SCOPING 3.3)
# period polities linked to their territory by hand, with the basis (2026-11-18). Wikidata's succession chain for Sri Lanka
# runs Kandy -> British Ceylon -> Dominion -> Sri Lanka and leaves out the Portuguese and Dutch periods (pilot SCOPING
# 3.3); Canada's chain is broken up by partial successions (P1366 of New France and Rupert's Land name several units).
# Under the territory design (user 2026-11-18) these are period nodes of the territory LC files their history under.
CURATED_PERIODS = {
    'Q1709007': ('Q854', 'Portuguese Ceylon (1505-1658): the coastal territory of the island; LC files its history under Sri Lanka -- History -- 1505-1658'),
    'Q1841483': ('Q854', 'Dutch Ceylon (1640-1796): the same; LC Sri Lanka -- History -- 1505-1796'),
    'Q170604':  ('Q16', 'New France: LC files it under Canada -- History -- To 1763 (New France)'),
    'Q251668':  ('Q16', 'Province of Quebec (1763-1791): LC Canada -- History -- 1763-1791'),
    'Q1121436': ('Q16', 'Province of Canada (1841-1867): LC Canada -- History -- 1841-1867'),
    'Q738395':  ('Q16', "Rupert's Land (1670-1870): transferred whole to Canada in 1870 (Rupert's Land Act 1868)"),
    'Q1998931': ('Q16', 'North-Western Territory (to 1870): transferred whole to Canada in 1870'),
    'Q795427':  ('Q1904', 'Upper Canada (1791-1841): became Canada West and then Ontario; LC Ontario -- History -- 1791-1841'),
    'Q1134180': ('Q176', 'Lower Canada (1791-1841): became Canada East and then Quebec; LC Québec (Province) -- History -- 1791-1841'),
    'Q2032545': ('Q1948', 'Red River Colony (1812-1870): its land became Manitoba in 1870'),
}


def tsv(*paths):
    for p in paths:
        if p.exists():
            yield from csv.DictReader(open(p, encoding='utf-8'), delimiter='\t')


def wd_tables():
    d = [B / 'wd', B / 'wd-extra', B / 'wd-extra2', B / 'wd-extra3']
    basic = {r['i']: r for r in tsv(*[x / 'basic.tsv' for x in d])}
    kinds, p131, anc, p17, alias, peoples = (defaultdict(set) for _ in range(6))
    for r in tsv(*[x / 'kinds.tsv' for x in d]):
        kinds[r['i']].add(r['c'])
    for r in tsv(*[x / 'p131.tsv' for x in d]):
        p131[r['i']].add(r['a'])
    for r in tsv(*[x / 'anc.tsv' for x in d]):
        anc[r['i']].add(r['a'])
    for r in tsv(*[x / 'p17.tsv' for x in d]):
        p17[r['i']].add(r['a'])
    for r in tsv(*[x / 'aliases.tsv' for x in d]):
        alias[r['i']].add(r['a'])
    for r in tsv(*[x / 'peoples.tsv' for x in d]):
        if r['c'] in PEOPLES:
            peoples[r['i']].add(r['c'])
    succ = defaultdict(lambda: defaultdict(set))
    for r in tsv(*[x / 'succ.tsv' for x in d]):
        succ[r['i']][r['rel']].add(r['a'])
    preds = defaultdict(set)
    for r in tsv(B / 'wd-preds/preds.tsv'):
        preds[r['i']].add(r['a'])
    return basic, kinds, p131, anc, p17, alias, peoples, succ, preds


def kind_of(q, kinds, basic):
    k = kinds.get(q, set())
    dissolved = bool((basic.get(q) or {}).get('dissolved'))
    if k & COUNTRY and not dissolved and not (k & {'Q10864048', 'Q107390'} and 'Q3624078' not in k):
        return 'country'                # (a state of India is a first-level division, not a country)
    if k & SETTLEMENT:
        return 'settlement'
    if k & HISTORICAL or (k & COUNTRY and dissolved):
        return 'historical polity'
    if k & ADMIN:
        return 'administrative unit'
    if k & FEATURE:
        return 'physical feature'
    if k & REGION:
        return 'region'
    if k & STRUCTURE:
        return 'structure'
    return 'other'


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def latin(s):
    return s and all(ord(ch) < 0x370 or 0x1E00 <= ord(ch) <= 0x1EFF for ch in s)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    basic, kinds, p131, anc, p17, alias, peoples, succ, preds = wd_tables()
    label = {q: (r.get('label') or q) for q, r in basic.items()}
    sitelinks = {q: int(num(r.get('sitelinks')) or 0) for q, r in basic.items()}
    area = {q: num(r.get('area')) for q, r in basic.items()}
    kind = {q: kind_of(q, kinds, basic) for q in basic}
    rep = Counter()

    def excluded(q):
        """Not a place for this layer: a people, nation or band (user 2026-11-18: places only), or no geographic or
        built class at all (planets, lists, alliances)."""
        if peoples.get(q) and (kind.get(q) in ('other', 'structure') or NATION_LABEL.search(label.get(q, ''))):
            return 'a people, nation or band, not a place'
        if kind.get(q, 'other') == 'other':
            return 'no geographic class in Wikidata'
        return None

    def primary(qids, lc_qids):
        """One QID per heading: LC's own recorded QID when it is one; else not a period polity of another candidate,
        current over historical, then the most sitelinks."""
        qids = [q for q in qids if q]
        good = [q for q in qids if q in basic and (basic[q].get('label') or '') and not excluded(q)]
        qids = good or qids
        if len(qids) <= 1:
            return qids[0] if qids else None
        if lc_qids and len(set(lc_qids) & set(qids)) == 1:
            return (set(lc_qids) & set(qids)).pop()
        hist = {'historical polity'}
        return sorted(qids, key=lambda q: (kind.get(q) in hist, any(q in preds.get(o, ()) for o in qids if o != q),
                                           -sitelinks.get(q, 0), q))[0]

    c = duckdb.connect()
    c.execute("SET memory_limit='4GB'; SET threads=4")
    c.execute(f"CREATE TABLE u AS SELECT * FROM '{B}/uses.parquet'")
    c.execute(f"CREATE TABLE auth AS SELECT file, id, label, variants FROM '{B}/auth.parquet'")
    c.execute(f"CREATE TABLE auth2 AS SELECT file, id, qids, lc_qids FROM '{B}/auth.parquet'")
    auth_label = {f'{f}:{i}': l for f, i, l, v in c.execute('SELECT file, id, label, variants FROM auth').fetchall()}
    auth_var = {f'{f}:{i}': v for f, i, l, v in c.execute('SELECT file, id, label, variants FROM auth').fetchall()}
    label_auth = defaultdict(list)
    for k, l in auth_label.items():
        label_auth[l].append(k)

    # ---- LC rows ---------------------------------------------------------------------------------------------
    pairs = c.execute("""SELECT heading, parent, route, auth_file, auth_id, qids, lc_qids, count(*) uses, count(DISTINCT key) books
                         FROM u WHERE used GROUP BY ALL""").fetchall()
    ground = {}                 # (heading, parent) -> (qid, auth key, route) or (None, reason)
    unground = []
    # hand groundings with a stated basis (data/graph/places/overrides.csv, 2026-11-18): lc rows for headings with no
    # QID or no authority match, fr rows for Canadiana French headings (second indicator 6)
    ovr = {}
    for r in csv.DictReader(open(OUT / 'overrides.csv', encoding='utf-8')):
        ovr[(r['heading'], r['parent'] or None, r['thesaurus'])] = r['qid']
    # an indirect $z pair whose LC qualifier is the parent's LC abbreviation ('Vancouver' under 'British Columbia' ->
    # 'Vancouver (B.C.)'): the pilot's rule only compared the qualifier's letters with the parent's start
    abbr_of = defaultdict(set)
    for a, full in ABBR.items():
        abbr_of[full].add(a)
        abbr_of[re.sub(r'\s*\(.*\)$', '', full)].add(a)
    abbr_of['Québec (Province)'].add('Québec')
    abbr_of['Quebec (Province)'].add('Québec')
    by_base = defaultdict(list)
    for k, l in auth_label.items():
        m = re.match(r'^(.*?)\s*\(([^)]*)\)$', l)
        if m:
            by_base[m.group(1)].append((k, m.group(2).split(' : ')[0], ' : ' in m.group(2)))
    auth_qids = {f'{f}:{i}': (q, lq) for f, i, q, lq in c.execute('SELECT file, id, qids, lc_qids FROM auth2').fetchall()}
    rep['indirect_abbr_pairs'] = 0
    for h, p, route, af, ai, qids, lcq, uses, books in pairs:
        if (h, p, 'lc') in ovr:
            q = ovr[(h, p, 'lc')]
            if q in basic:
                ground[(h, p)] = (q, f'{af}:{ai}' if ai else None, 'override')
                continue
        if route.startswith('ambiguous') and p:
            cands = [(k, sub) for k, qual, sub in by_base.get(h, []) if qual in abbr_of.get(p, ())]
            if len(cands) > 1:          # 'Halifax (N.S.)' over 'Halifax (N.S. : Regional municipality)': the plain form
                cands = [x for x in cands if not x[1]]
            cands = [k for k, _ in cands]
            if len(cands) == 1 and auth_qids.get(cands[0], ([],))[0]:
                q = primary(auth_qids[cands[0]][0], auth_qids[cands[0]][1] or [])
                if q and q in basic and not excluded(q):
                    ground[(h, p)] = (q, cands[0], 'indirect')
                    rep['indirect_abbr_pairs'] += 1
                    continue
        ak = f'{af}:{ai}' if ai else None
        if re.search(r'\bcountries\b', h, re.I):
            unground.append((h, p, route, ak, uses, books, 'a category of countries (developing, Arab, Islamic ...), not a place'))
            continue
        if route not in ('exact', 'indirect'):
            unground.append((h, p, route, None, uses, books, 'several LC authorities fit' if route.startswith('ambiguous') else 'no LC geographic authority with this heading'))
            continue
        q = primary(qids or [], lcq or [])
        if not q:
            unground.append((h, p, route, ak, uses, books, 'LC authority without a Wikidata QID'))
            continue
        if q not in basic:
            unground.append((h, p, route, ak, uses, books, f'QID {q} not found in Wikidata (redirected or deleted)'))
            continue
        why = excluded(q)
        if why:
            unground.append((h, p, route, ak, uses, books, f'{why} ({q} {label.get(q)})'))
            continue
        ground[(h, p)] = (q, ak, route)
    rows = {}
    form_src = {'651': 'lc-651', 'z': 'lc-z', '610-jurisdiction': 'lc-610'}
    fr = {(h, p): q for (h, p, t), q in ovr.items() if t == 'fr' and q in basic}
    rep['fr_override_uses'] = 0
    for key, form, h, p, full, fiction, used in c.execute(
            "SELECT key, form, heading, parent, full_heading, fiction, used FROM u ORDER BY key, tag, occ").fetchall():
        if not used:
            if (h, p) not in fr:
                continue
            g = (fr[(h, p)], None, 'override')
            rep['fr_override_uses'] += 1
        else:
            g = ground.get((h, p))
        if not g:
            continue
        q, ak, route = g
        src = form_src[form]
        # fiction: the $v form subdivision (places_lc.py), or the same words as any later part of the heading string
        # (older records carry 'Fiction' in $x: 'Kentucky -- Fiction'; fiction audit 2026-11-18)
        fiction = fiction or bool(FICTION.search(full or ''))
        conf = 'lc-fiction' if fiction else {'exact': 'lc-exact', 'override': 'lc-override'}.get(route, 'lc-indirect')
        k = (key, q, src)
        old = rows.get(k)
        rank = {'lc-exact': 0, 'lc-indirect': 1, 'lc-override': 2, 'lc-fiction': 3}
        if old is None or rank[conf] < rank[old['confidence']]:
            rows[k] = dict(work=key, qid=q, source=src, heading=full, lc_id=ak.split(':', 1)[1] if ak else '', confidence=conf)
    rep['lc_rows'] = len(rows)
    rep['lc_books'] = len({k[0] for k in rows})
    # unused thesauri (French Canadiana, $2 thesauri): counted with the ungrounded headings
    for h, p, uses, books in c.execute("""SELECT heading, parent, count(*), count(DISTINCT key) FROM u WHERE NOT used
                                          GROUP BY ALL""").fetchall():
        if (h, p) in fr:
            continue
        unground.append((h, p, 'not-used', None, uses, books, 'heading from a non-LC thesaurus (French Canadiana, $2 fast/swd/...), not used to tag'))

    # ---- title rows --------------------------------------------------------------------------------------------
    checked = 0
    for f in ('ceylon-works-checked.csv', 'saskatchewan-works-checked.csv'):
        for r in csv.DictReader(open(PILOT / f, encoding='utf-8')):
            places = r['matched_places'].split('+')
            if r['verdict'] == 'right':
                qs = {CHECKED_PLACES.get(pl) for pl in places}
            else:
                qs = {CHECKED_OTHER.get((r['verdict'], pl)) for pl in places}
                if r['verdict'] == 'other_place' and 'National Park' not in r['note']:
                    qs = set()
            for q in qs - {None}:
                rows[(r['work'], q, 'title-checked')] = dict(work=r['work'], qid=q, source='title-checked', heading=r['title'][:300],
                                                             lc_id='', confidence='title-checked')
                checked += 1
    rep['title_checked_rows'] = checked
    tr = 0
    for w, q, src, rule, matched in c.execute(f"SELECT * FROM '{B}/title-tags.parquet'").fetchall():
        if (w, q, 'title-checked') in rows:
            continue
        rows[(w, q, 'title-rule')] = dict(work=w, qid=q, source='title-rule', heading=f'{matched} (rule: {rule})', lc_id='',
                                          confidence='title-rule-gated' if 'gated' in rule else 'title-rule')
        tr += 1
    rep['title_rule_rows'] = tr

    # ---- the place set -----------------------------------------------------------------------------------------
    tagged = Counter(r['qid'] for r in rows.values())
    P = set(tagged)
    lc_of = {}                          # QID -> the most used LC authority
    lc_uses = defaultdict(Counter)
    for r in rows.values():
        if r['lc_id']:
            lc_uses[r['qid']][r['lc_id']] += 1
    for q, cnt in lc_uses.items():
        lc_of[q] = cnt.most_common(1)[0][0]
    auth_by_id = {k.split(':', 1)[1]: k for k in auth_label}

    # ---- hierarchy -----------------------------------------------------------------------------------------------
    H = {}                              # (child, parent) -> basis

    def add(ch, pa, basis):
        if ch != pa and (ch, pa) not in H:
            H[(ch, pa)] = basis

    def lc_place(text):
        """An LC qualifier part -> a place QID, by the authority label (or LC's abbreviation of a state or province)."""
        text = text.strip()
        for cand in (text, ABBR.get(text), ABBR.get(text, '') + '' if text in ABBR else None):
            if not cand:
                continue
            for ak in label_auth.get(cand, []):
                g = ground.get((cand, None))
                if g:
                    return g[0]
        return None

    # periods: walk back from a territory through its direct predecessors (P1365, or P1366 on the predecessor) while
    # each predecessor's only successor is the node already reached (Kingdom of Kandy -> British Ceylon -> Dominion of
    # Ceylon -> Sri Lanka); a direct predecessor with several successors is a part-predecessor (the NWT districts of
    # Saskatchewan), shown as a link only. Every period node points at the final territory.
    def nexts(x):
        return {y for y in succ[x]['replaced_by'] if y in basic} | {y for y in rev_replaces.get(x, ()) if y in basic}

    rev_replaces = defaultdict(set)
    for y, rel in succ.items():
        for x in rel['replaces']:
            rev_replaces[x].add(y)
    direct_preds = defaultdict(set)
    for x in basic:
        for y in nexts(x):
            direct_preds[y].add(x)
    period_of = {}
    PERIOD_KINDS = ('historical polity', 'administrative unit', 'country', 'region')
    for t in sorted(P, key=lambda q: int(q[1:])):
        if t in period_of:
            continue
        todo, seen = [t], {t}
        while todo:
            y = todo.pop()
            for x in direct_preds.get(y, ()):
                if x in seen or x in P and x != t and kind.get(x) == 'country' or excluded(x) or kind.get(x) not in PERIOD_KINDS:
                    continue
                seen.add(x)
                if nexts(x) == {y}:
                    if x not in period_of and x != t:
                        period_of[x] = t
                        todo.append(x)
                elif y == t:
                    add(x, t, 'part-predecessor')
    for x, (t, _) in CURATED_PERIODS.items():
        period_of[x] = t
        H.pop((x, t), None)
    for x, t in period_of.items():
        while t in period_of and period_of[t] != x:
            t = period_of[t]
        period_of[x] = t
    for x, t in period_of.items():
        cur = CURATED_PERIODS.get(x, (None, ''))
        add(x, t, 'period-of (curated: ' + cur[1] + ')' if cur[0] == t else 'period-of')
    P |= {x for (x, _), b in H.items()}

    for q in sorted(P):
        # LC qualifier
        ak = auth_by_id.get(lc_of.get(q, ''))
        lab = auth_label.get(ak, '') if ak else ''
        m = re.search(r'\(([^)]*)\)$', lab)
        if m:
            qual = m.group(1).split(' : ')[0]
            parts = [x for x in re.split(r'\s+and\s+|,\s*', qual) if x]
            found = [lc_place(x) for x in parts]
            found = [x for x in found if x and x != q]
            if len(parts) == 1 and found:
                add(q, found[0], 'lc-qualifier')
            elif len(parts) > 1:
                for f in found:
                    add(q, f, 'overlaps (lc-qualifier)')
        if kind.get(q) in ('country', 'other', 'historical polity') or q in period_of:
            continue
        # Wikidata P131, filtered
        direct = {a for a in p131.get(q, ()) if a in basic}
        A = {a for a in anc.get(q, ()) if a in P and a != q}
        # the direct P131 values that are not ancestors of another direct value: two or more = a straddler
        minimal = {a for a in direct if not any(a in anc.get(b, ()) for b in direct if b != a)}
        if len(minimal) >= 2:
            # straddles several units: a feature or settlement overlaps them; a larger region contains them
            near = set()
            for d in minimal:
                near |= {d} if d in P else {a for a in anc.get(d, ()) if a in P and kind.get(a) in ('administrative unit', 'country')}
            for p in near:
                ar, ap = area.get(q), area.get(p)
                if kind.get(q) == 'region' and (ar is None or ap is None or ar > ap):
                    if kind.get(p) != 'country':
                        add(p, q, 'region-contains (wd-p131)')
                elif ar is not None and ap is not None and ar >= ap:
                    continue
                else:
                    add(q, p, 'overlaps (wd-p131)')
            continue
        keep = set()
        for a in A:
            if area.get(q) is not None and area.get(a) is not None and area[q] >= area[a]:
                rep['hierarchy_dropped_container'] += 1
                continue
            if kind.get(a) in ('settlement',) and kind.get(q) not in ('settlement', 'structure', 'physical feature', 'administrative unit'):
                continue
            keep.add(a)
        for a in keep:
            if not any(a in anc.get(b, ()) for b in keep if b != a):
                add(q, a, 'wd-p131')
        cs = {x for x in p17.get(q, ()) if x in P and kind.get(x) == 'country'}
        if len(cs) == 1:
            ctry = cs.pop()
            if ctry not in keep and not any(ctry in anc.get(b, ()) for b in keep):
                add(q, ctry, 'wd-country')
        elif len(cs) > 1 and kind.get(q) in ('physical feature', 'region'):
            for ctry in cs:
                add(q, ctry, 'overlaps (wd-country)')
    # parents named in the hierarchy are places too (a country with no tagged work still gets a node)
    P |= {p for (_, p) in H}
    # remove a containment row the other way round (a cycle from conflicting sources): keep the smaller as child
    CONTAIN = ('lc-qualifier', 'wd-p131', 'wd-country', 'region-contains (wd-p131)')
    for (a, b), basis in list(H.items()):
        if basis in CONTAIN and H.get((b, a)) in CONTAIN:
            ra, rb = area.get(a), area.get(b)
            drop = (a, b) if (ra is not None and rb is not None and ra > rb) else (b, a)
            H.pop(drop, None)
            rep['hierarchy_cycles_removed'] += 1

    # ---- places ----------------------------------------------------------------------------------------------
    def variants(q):
        names = [label.get(q, q)]
        ak = auth_by_id.get(lc_of.get(q, ''))
        if ak:
            names.append(re.sub(r'\s*\([^)]*\)$', '', auth_label[ak]))
            names += [v for v in (auth_var.get(ak) or []) if latin(v) and len(v) > 2 and not re.fullmatch(r'[A-Z.]+', v)]
        names += [a for a in sorted(alias.get(q, ())) if latin(a) and len(a) > 2]
        for x, t in period_of.items():           # a territory is found by its period names (Ceylon -> Sri Lanka)
            if t == q:
                names.append(label.get(x, ''))
                names += [a for a in sorted(alias.get(x, ())) if latin(a) and len(a) > 2]
        out, seen = [], set()
        for n in names:
            n = (n or '').strip()
            if n and n.lower() not in seen:
                seen.add(n.lower())
                out.append(n)
        return out[:60]

    places = []
    for q in sorted(P, key=lambda x: int(x[1:])):
        ak = auth_by_id.get(lc_of.get(q, ''))
        cs = sorted(x for x in p17.get(q, ()) if kind.get(x) == 'country')
        places.append(dict(qid=q, label=label.get(q, q), kind=kind.get(q, 'other'), country=cs[0] if len(cs) == 1 else ';'.join(cs),
                           lc_id=lc_of.get(q, ''), lc_heading=auth_label.get(ak, '') if ak else '',
                           variants='|'.join(variants(q)), period_of=period_of.get(q, ''),
                           sitelinks=sitelinks.get(q, 0), inception=(basic.get(q) or {}).get('inception', ''),
                           dissolved=(basic.get(q) or {}).get('dissolved', ''), works=tagged.get(q, 0)))
    rep['places'] = len(places)
    rep['places_with_works'] = sum(1 for p in places if p['works'])
    rep['places_by_kind'] = dict(Counter(p['kind'] for p in places).most_common())
    rep['hierarchy_rows'] = len(H)
    rep['hierarchy_by_basis'] = dict(Counter(H.values()).most_common())

    # ---- write ---------------------------------------------------------------------------------------------------
    def wcsv(name, fields, data):
        with gzip.open(OUT / name, 'wt', newline='', encoding='utf-8', compresslevel=9) as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)

    out_rows = sorted(rows.values(), key=lambda r: (r['work'], r['qid'], r['source']))
    for r in out_rows:
        r['place_label'] = label.get(r['qid'], r['qid'])
    wcsv('work-places.csv.gz', ['work', 'qid', 'place_label', 'source', 'heading', 'lc_id', 'confidence'], out_rows)
    wcsv('places.csv.gz', list(places[0]), places)
    wcsv('place-hierarchy.csv.gz', ['child', 'parent', 'basis'],
         [dict(child=a, parent=b, basis=v) for (a, b), v in sorted(H.items())])
    ug = Counter()
    ug_rows = []
    for h, p, route, ak, uses, books, reason in sorted(unground, key=lambda x: -x[4]):
        ug[reason.split(' (')[0]] += uses
        ug_rows.append(dict(heading=h, parent=p or '', route=route, lc_id=(ak or '').split(':', 1)[-1], uses=uses, books=books, reason=reason))
    wcsv('ungrounded.csv.gz', ['heading', 'parent', 'route', 'lc_id', 'uses', 'books', 'reason'], ug_rows)
    rep['rows'] = len(out_rows)
    rep['rows_by_source'] = dict(Counter(r['source'] for r in out_rows).most_common())
    rep['rows_by_confidence'] = dict(Counter(r['confidence'] for r in out_rows).most_common())
    rep['works'] = len({r['work'] for r in out_rows})
    rep['works_by_source'] = {s: len({r['work'] for r in out_rows if r['source'] == s}) for s in rep['rows_by_source']}
    rep['ungrounded_uses_by_reason'] = dict(ug.most_common())
    rep['ungrounded_headings'] = len(ug_rows)
    rep['lc_uses_total'] = c.execute('SELECT count(*) FROM u').fetchone()[0]
    rep['lc_uses_grounded'] = sum(n for (h, p), n in Counter(
        {(h, p): uses for h, p, *_r, uses, books in [(x[0], x[1], x[7], x[8]) for x in pairs]}).items() if (h, p) in ground)
    (OUT / 'report.json').write_text(json.dumps(dict(sorted(rep.items())), indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(dict(sorted(rep.items())), indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
