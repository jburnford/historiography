"""Place layer, step 3: title tags, conservative (2026-11-18).

Two kinds of title tag, both on works that are not books (articles, chapters, theses, reviews, `other`, and the
unkeyed Crossref works); books take their places from LC subject headings (places_lc.py):
- title-checked: the pilot's full hand reading of every Ceylon-family and Saskatchewan-family title match
  (data/field-research/place-nodes-scoping-2026-11-18/{ceylon,saskatchewan}-works-checked.csv), rows read right, on
  every kind including books (the reading covered them). A row read `river` is the Saskatchewan River, not the
  province; Prince Albert National Park rows are the park.
- title-rule: a name rule applied to every non-book work, kept only when a hand reading of 40 random matches (or
  the pilot's full reading) found at least 95% right. Names short, common or personal (London, Regina, Prince Albert,
  Colombo, Prairies, Normandy...) get no rule. Each rule drops citation tails (a place of publication: 'Toronto:',
  '(London', 'University of Manitoba Press', 'Toronto and Buffalo:'). A gated rule needs a regional word in the
  title as well (Canada / Canadian / a province; Ceylon / Sri Lanka / Sinhala / Tamil ...). Works the pilot read
  wrong are never tagged by a rule.

    python3 scripts/places_titles.py sample NAME [--gated] [--n 40]   # print a reading sample (seed 20261118)
    python3 scripts/places_titles.py precision                        # gated rules on the pilot's full reading
    python3 scripts/places_titles.py tag --out build/places/title-tags.parquet
Rules and their reading results are in RULES below; readings are in data/graph/places/title-readings/.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
PILOT = ROOT / 'data/field-research/place-nodes-scoping-2026-11-18'
READ = ROOT / 'data/graph/places/title-readings'

CANADA_WORDS = (r"\b(Canad(a|ian|iens?|ienne)|Ontario|Qu[eé]bec|Manitoba|Saskatchewan|Alberta|British Columbia|Nova Scotia|"
                r"New Brunswick|Newfoundland|Labrador|Prince Edward Island|Yukon|Nunavut|North-?[Ww]est Territor|"
                r"Upper Canada|Lower Canada|Prairie|Maritime|Acadi[ae])")
LANKA_WORDS = r"\b(Ceylon|Sri Lanka|Lanka|Kandy|Kandyan|Sinhal|Tamil|VOC|Dutch|Buddhis)"

# name -> (QID, regex, gate or None, status, reading). status: 'rule' (>= 95% on the reading), 'no-rule'.
# QIDs are the ones the LC headings ground to (places_lc.py), so title and LC tags meet on one place.
RULES = {
    # pilot readings (SCOPING.md 2.2): full reading for Ceylon/Sri Lanka/Kandy, 40-title samples for the others
    'Ceylon':        ('Q854', r'\bCeylon\b', None, 'rule', 'pilot full reading: 391/395 right (99.0%)'),
    'Sri Lanka':     ('Q854', r'\bSri Lanka|\bLanka\b', None, 'rule', 'pilot full reading: 646/667 right (96.9%)'),
    'Kandy':         ('Q203197', r'\bKandy\b', None, 'rule', 'pilot full reading: all right (Kandy and Kingdom of Kandy 49/49)'),
    'Kingdom of Kandy': ('Q1530762', r'\bKandyan|\bKingdom of Kandy', None, 'rule', 'pilot full reading: all right'),
    'Jamaica':       ('Q766', r'\bJamaica', None, 'rule', 'pilot sample: 40/40 right'),
    'Mediterranean': ('Q72499', r'\b(Mediterranean|Méditerranée|Mediterráneo|Mittelmeer)', None, 'rule', 'pilot sample: 39/40 right (97.5%)'),
    'Jaffna':        ('Q215277', r'\bJaffna', None, 'rule', 'pilot full reading: 6/6 right after the citation-tail rule (7 matches)'),
    'Anuradhapura':  ('Q5724', r'\bAnuradhapura', None, 'rule', 'pilot full reading: 7/7 right'),
    'Gdańsk':        ('Q1792', r'\b(Danzig|Gdańsk|Gdansk|Dantzig)\b', None, 'rule', 'pilot sample: 38/40 right (95%); the two wrong were a venue and a place of publication (the citation-tail rule drops the second)'),
}
# names that need a reading before a rule is allowed (provinces, territories, larger cities): raw first, then gated
CANDIDATES = {
    'Manitoba': ('Q1948', r'\bManitoba\b'), 'Alberta': ('Q1951', r'\bAlberta\b'),
    'British Columbia': ('Q1973', r'\bBritish Columbia'), 'Nova Scotia': ('Q1952', r'\bNova Scotia'),
    'New Brunswick': ('Q1965', r'\bNew Brunswick'), 'Newfoundland': ('Q2003', r'\bNewfoundland'),
    'Prince Edward Island': ('Q1979', r'\bPrince Edward Island'), 'Yukon': ('Q2009', r'\bYukon'),
    'Nunavut': ('Q2023', r'\bNunavut'), 'Northwest Territories': ('Q2007', r'\bNorth-?[Ww]est Territories'),
    'Ontario': ('Q1904', r'(?<!Lake )\bOntario\b'), 'Quebec': ('Q176', r'\bQu[eé]bec\b'), 'Saskatchewan': ('Q1989', r'\bSaskatchewan\b'),
    'Toronto': ('Q172', r'\bToronto\b'), 'Montreal': ('Q340', r'\bMontr[eé]al\b'), 'Vancouver': ('Q24639', r'\bVancouver\b'),
    'Winnipeg': ('Q2135', r'(?<!Lake )\bWinnipeg\b(?! River)'), 'Ottawa': ('Q1930', r'\bOttawa\b'), 'Halifax': ('Q2141', r'\bHalifax\b'),
    'Calgary': ('Q36312', r'\bCalgary\b'), 'Edmonton': ('Q2096', r'\bEdmonton\b'), 'Saskatoon': ('Q10566', r'\bSaskatoon\b'),
    'Regina': ('Q2123', r'\bRegina\b'),
    # Canada as a whole (coordinator 2026-11-18): the country, the adjective, regions and period polities
    'Canada': ('Q16', r'\bCanada\b'), 'Canadian': ('Q16', r'\bCanadi(an|en|enne)s?\b'),
    # the adjective without the institution names that read wrong in the raw sample (a journal, an association, a
    # publisher, the Dictionary of Canadian Biography)
    'Canadian (no institutions)': ('Q16', r'(?<!Dictionary of )\bCanadi(an|en|enne)s?\b(?! (Institute|Association|Society|Journal|Biography|Museum|Historical Association|Historical Review|Political Science|Press|Broadcasting|Medical Association|Pacific Railway|Studies|Review))'),
    'New France': ('Q170604', r'\bNew France\b|\bNouvelle-France\b|\bNueva Francia\b'),
    'Upper Canada': ('Q795427', r'\bUpper Canada\b|\bHaut-Canada\b'), 'Lower Canada': ('Q1134180', r'\bLower Canada\b|\bBas-Canada\b'),
    "Rupert's Land": ('Q738395', r"\bRupert['’]?s Land\b"), 'Acadia': ('Q207353', r'\bAcadi(a|e)\b'),
    'Klondike': ('Q602965', r'\bKlondike\b'), 'Maritimes': ('Q731613', r'\bMaritime Provinces\b(?! of (Ceylon|Sri Lanka))|\bthe Maritimes\b'),
    'Atlantic Canada': ('Q246972', r'\bAtlantic Canada\b|\bAtlantic Provinces\b'),
    'Canadian Prairies': ('Q1364746', r'\bPrairie Provinces\b|\bCanadian Prairies\b|\bPrairie West\b'),
    'Northern Canada': ('Q764146', r'\bCanadian North\b|\bNorthern Canada\b|\bCanadian Arctic\b'),
    # without 'Canadian North-West' (the prairie North-West, another region: 3 of the 40 read)
    'Northern Canada (not North-West)': ('Q764146', r'\bCanadian North\b(?!-?[Ww]est)|\bNorthern Canada\b|\bCanadian Arctic\b'),
    'British North America': ('Q248452', r'\bBritish North America\b'),
    'Great Lakes': ('Q7347', r'\bGreat Lakes\b'), 'St. Lawrence': ('Q134750', r'\b(St\.?|Saint)[ -]Lawrence (River|Valley)\b'),
    'Victoria': ('Q2132', r'\bVictoria, B\.? ?C\b|\bVictoria\b'), 'Kingston': ('Q202973', r'\bKingston\b'),
    'Hamilton': ('Q133116', r'\bHamilton\b'),
    # larger Canadian cities by pattern (2026-11-18): the bare names failed (places of publication, namesakes); a city
    # counts when the title says 'in/of/at ... <city>', '<city>'s', or '<city>, <province or Canada>', without the
    # institution names (University of, Press, Studies, Star) and the namesakes read in the bare-name samples
    'Toronto (pattern)': ('Q172', r"(?<!University )(?<!Université )\b(in|of|at|from|across|around|to|for) (the )?(city of |metropolitan |Metropolitan |Greater |early |postwar |modern |colonial |nineteenth-century |twentieth-century |Victorian )?Toronto\b(?! (Press|University|Studies|Italian Studies|Star|Board))|\bToronto['’]s\b|\bToronto,? (Ont|Ontario|Canada|Upper Canada)\b"),
    'Montreal (pattern)': ('Q340', r"(?<!Université )(?<!University )\b(in|of|at|from|across|around|to|for|à|de|du) (la ville de |the city of |early |postwar |nineteenth-century |)Montr[eé]al\b(?! (Press|University|Gazette|Studies))|\bMontr[eé]al['’]s\b|\bMontr[eé]al,? (Qu[eé]bec|Canada|Lower Canada)\b"),
    'Vancouver (pattern)': ('Q24639', r"\b(in|of|at|from|across|around|to|for) (the city of |early |postwar |Greater |)Vancouver\b(?! (Island|Press))|\bVancouver['’]s\b(?! Island)|\bVancouver,? (B\.? ?C|British Columbia|Canada)\b"),
    'Ottawa (pattern)': ('Q1930', r"\b(in|of|at|from|across|around|for) (the city of |early |)Ottawa\b(?! (Agreements?|Conference|Convention|River|Valley|Indians|people|Press|Treaty))|\bOttawa['’]s\b|\bOttawa,? (Ont|Ontario|Canada)\b"),
    'Halifax (pattern)': ('Q2141', r"\bHalifax,? (N\.? ?S|Nova Scotia)\b|\bHalifax (Explosion|explosion|Harbour|harbour|Citadel)\b|\bVictorian Halifax\b"),
    'Calgary (pattern)': ('Q36312', r"(?<!University )\b(in|of|at|from|across|around|to|for) (the city of |early |)Calgary\b(?! (Press|Herald))|\bCalgary['’]s\b|\bCalgary,? (Alta|Alberta|Canada)\b|\bCalgary Stampede\b"),
    'Edmonton (pattern)': ('Q2096', r"(?<!Witch )(?<!University )\b(in|at|from|across|around|to|for) (the city of |early |)Edmonton\b(?! Press)|\bEdmonton['’]s\b|\bEdmonton,? (Alta|Alberta|Canada)\b"),
    'Quebec City (pattern)': ('Q2145', r"\bQu[eé]bec City\b|\b(ville|Ville) de Qu[eé]bec\b|\bcity of Qu[eé]bec\b"),
    'Victoria (pattern)': ('Q2132', r"\bVictoria,? (B\.? ?C\b|British Columbia)"),
    # Sri Lankan child places: gated rules measured on the pilot's full reading (precision())
    'Colombo': ('Q35381', r'\bColombo\b'), 'Jaffna': ('Q215277', r'\bJaffna'), 'Galle': ('Q319366', r'\bGalle\b'),
    'Trincomalee': ('Q323873', r'\bTrincomal'), 'Batticaloa': ('Q810963', r'\bBatticaloa'),
    'Anuradhapura': ('Q5724', r'\bAnuradhapura'), 'Polonnaruwa': ('Q394443', r'\bPolonnaruw'),
}


PATTERN_RX = {rx for n, (q, rx) in CANDIDATES.items() if n.endswith('(pattern)')}


def cite_tail(name_rx):
    """A place of publication or a press: the name followed by ':' (optionally 'and <Place>'), preceded by '(' or
    '<Place> and', inside 'University of <name> Press' / '<name> University Press', or before ', <year>' in a title
    that carries Press/pp./ISBN."""
    n = '(?:' + name_rx.replace(r'\b', '') + ')'
    return re.compile(rf'({n}(\s*(and|&)\s*[A-Z][\w.]+)?\s*:|\(\s*{n}|[A-Z][\w.]+\s*(and|&)\s*{n}\s*[:,]|University of {n}\b[^.]*Press|'
                      rf'{n} University Press|{n} Press|{n},\s*[A-Z][\w\'’.-]+( [A-Z][\w\'’.-]+)?,\s*(1[5-9]|20)\d\d\b(?!\s*[-–])|'
                      rf'{n},? N\.? ?J\.?|{n}, New Jersey)')


CITE_CTX = re.compile(r'(Press|\bpp\.|\bPp\.|ISBN|£|\$\d)')


# city pattern rules also drop meeting reports (a venue), acknowledgement text that leaked into a title, and a city as
# place of publication followed by a publisher and a year ('Montréal, Québec Amérique, 2000')
PATTERN_DROP = re.compile(r"(?i)\b(annual meeting|meetings? (in|at)|conference|congress|symposium|colloque|proceedings)\b|(?i:we thank)|"
                          r"\b(Montr[eé]al|Toronto|Vancouver|Ottawa|Calgary|Edmonton|Qu[eé]bec|Halifax|Victoria)\s*[,:]\s*[^,;]{2,40},\s*(1[89]|20)\d\d\b")


def keep(title, name_rx, gate):
    """True when the title names the place outside a citation tail (and, for a gated rule, has a regional word too)."""
    rx = re.compile(name_rx)
    if not rx.search(title):
        return False
    if name_rx in PATTERN_RX and PATTERN_DROP.search(title):
        return False
    ct = cite_tail(name_rx)
    stripped = ct.sub(' ', title)
    if CITE_CTX.search(title):
        stripped = re.sub('(?:' + name_rx.replace(r'\b', '') + r')\s*,\s*(19|20)\d\d', ' ', stripped)
    if not rx.search(stripped):
        return False
    if gate:
        return bool(re.search(gate, rx.sub(' ', stripped)))
    return True


def con():
    c = duckdb.connect()
    c.execute("SET memory_limit='4GB'; SET threads=4")
    return c


def works(c):
    c.execute(f"""CREATE TABLE IF NOT EXISTS w AS SELECT key, label, kind, year, resolution FROM '{G}/work.parquet'
                  WHERE label IS NOT NULL AND kind <> 'book'""")


def sql_rx(rx):
    """The regex for DuckDB's prefilter (RE2 has no lookaround): lookarounds dropped; keep() applies the full one."""
    out, i = [], 0
    while i < len(rx):
        if rx.startswith(('(?!', '(?=', '(?<!', '(?<='), i):
            depth = 0
            while i < len(rx):              # skip the balanced group
                if rx[i] == '\\':
                    i += 2
                    continue
                depth += {'(': 1, ')': -1}.get(rx[i], 0)
                i += 1
                if depth == 0:
                    break
            continue
        out.append(rx[i])
        i += 1
    return ''.join(out)


def gate_for(name):
    return LANKA_WORDS if CANDIDATES.get(name, ('',))[0] in {
        'Q35381', 'Q215277', 'Q319366', 'Q323873', 'Q810963', 'Q5724', 'Q394443'} else CANADA_WORDS


def sample(name, gated, n):
    c = con()
    works(c)
    qid, rx = CANDIDATES[name]
    gate = gate_for(name) if gated else None
    rows = c.execute("""SELECT key, kind, year, label FROM w WHERE regexp_matches(label, ?)
                        ORDER BY hash(key || '20261118')""", [sql_rx(rx)]).fetchall()
    kept = [r for r in rows if keep(r[3], rx, gate)]
    print(f'# {name} {"gated" if gated else "raw"}: {len(rows)} matches, {len(kept)} kept after the citation-tail rule'
          f'{" and the gate" if gated else ""}')
    for i, (k, kind, y, t) in enumerate(kept[:n]):
        print(f'{i}\t{k}\t{kind}\t{y}\t{t[:230]}')


def precision():
    """Gated rules for child places on the pilot's full reading (every match read)."""
    for f in ('ceylon-works-checked.csv', 'saskatchewan-works-checked.csv'):
        rows = list(csv.DictReader(open(PILOT / f)))
        for name, (qid, rx) in CANDIDATES.items():
            hits = [r for r in rows if re.search(rx, r['title'])]
            if not hits:
                continue
            for gated in (False, True):
                gate = gate_for(name) if gated else None
                k = [r for r in hits if keep(r['title'], rx, gate)]
                right = sum(r['verdict'] == 'right' for r in k)
                print(f"{f[:6]} {name:14s} {'gated' if gated else 'raw  '} read {len(hits):4d} kept {len(k):4d} right {right:4d} "
                      f"precision {100 * right / max(1, len(k)):5.1f}%")


def readings():
    """Reading results: data/graph/places/title-readings/<name>-<raw|gated>.csv (idx, key, verdict, note)."""
    out = {}
    for p in sorted(READ.glob('*.csv')):
        rows = list(csv.DictReader(open(p)))
        name, mode = p.stem.rsplit('-', 1)
        right = sum(r['verdict'] == 'right' for r in rows)
        out[(name, mode)] = (right, len(rows))
    return out


def active_rules():
    """RULES plus the candidates whose reading reached 95% (at least 10 titles read: a sample of 40, or every match
    when there are fewer). When both the raw and the gated rule pass, the more precise one is used (a tie: raw)."""
    rules = {k: (q, rx, g) for k, (q, rx, g, st, _) in RULES.items() if st == 'rule'}
    rd = readings()
    for name, (qid, rx) in CANDIDATES.items():
        ok = []
        for mode in ('raw', 'gated'):
            r = rd.get((name.replace(' ', '_'), mode))
            if r and r[1] >= 10 and r[0] / r[1] >= 0.95:
                ok.append((r[0] / r[1], mode == 'raw', mode))
        if ok:
            mode = max(ok)[2]
            rules[name] = (qid, rx, gate_for(name) if mode == 'gated' else None)
    return rules


# the places the pilot's full reading covered: a work read wrong there is never tagged to them by a rule
PILOT_FAMILY = {'Q854', 'Q203197', 'Q1530762', 'Q215277', 'Q5724', 'Q1989'}


def tag(out):
    c = con()
    works(c)
    rules = active_rules()
    wrong = set()
    checked = []
    for f in ('ceylon-works-checked.csv', 'saskatchewan-works-checked.csv'):
        for r in csv.DictReader(open(PILOT / f)):
            if r['verdict'] != 'right':
                wrong.add(r['work'])
            checked.append(r)
    # a work read wrong for a name in its 40-title reading is never tagged by that name's rules
    read_wrong = set()
    for path in READ.glob('*.csv'):
        name = path.stem.rsplit('-', 1)[0].replace('_', ' ')
        for r in csv.DictReader(open(path)):
            if r['verdict'] != 'right':
                read_wrong.add((r['key'], CANDIDATES.get(name, (None,))[0]))
    rows = []
    for name, (qid, rx, gate) in rules.items():
        for key, label in c.execute('SELECT key, label FROM w WHERE regexp_matches(label, ?)', [sql_rx(rx)]).fetchall():
            if (key in wrong and qid in PILOT_FAMILY) or (key, qid) in read_wrong or not keep(label, rx, gate):
                continue
            m = re.search(rx, label)
            rows.append((key, qid, 'title-rule', name + (' (gated)' if gate else ''), m.group(0)))
    print({n: sum(1 for r in rows if r[3].split(' (gated)')[0] == n) for n in rules})
    import pyarrow as pa
    import pyarrow.parquet as pq
    pq.write_table(pa.table({k: [r[i] for r in rows] for i, k in enumerate(('work', 'qid', 'source', 'rule', 'matched'))}), out)
    print(len(rows), 'title-rule rows ->', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['sample', 'precision', 'tag'])
    ap.add_argument('name', nargs='?')
    ap.add_argument('--gated', action='store_true')
    ap.add_argument('--n', type=int, default=40)
    ap.add_argument('--out', type=Path, default=ROOT / 'build/places/title-tags.parquet')
    a = ap.parse_args()
    if a.cmd == 'sample':
        sample(a.name, a.gated, a.n)
    elif a.cmd == 'precision':
        precision()
    else:
        tag(a.out)


if __name__ == '__main__':
    main()
