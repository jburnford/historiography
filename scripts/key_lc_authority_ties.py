"""A keyed person's own LC name authority, not anchored on the key (2026-11-12; ARCHITECTURE.md section 8, class 34).
Writes a key-log proposal of `attach` operations (not applied) and a derived table the linkers read now.

Probe: Brittany Luby (p-81610: AHA, thesis, review credit; no PID) has LC authority n2018033278 'Luby, Brittany,
1984-', which no key holds, so the author linker counts it as a namesake (`lc_others=1`) and holds her works back.
Earlier routes attached authorities only through a catalogue record of the person's dissertation as a book
(key_aha_lc_books.py) or a 670 citing the dissertation or the doctorate (key_aha_lc_notes.py).

Record linkage, one key and one authority at a time:
- **Population**: keys with scholarly evidence (a thesis or AHA anchor, a key-log thesis, a directory anchor, a
  supervision, a key-log review or a review-credit anchor) and no `lcnaf:` anchor; authorities in the LC name file
  (id.loc.gov bulk download of 2026-10-30, so authorities made after 2016 are held) that are live, not
  undifferentiated, whose authorised form or a 400 variant agrees with the key's label or an alias: same family name,
  given names agreeing as names both ways (key_aha_career.same_person_name; nicknames as that rule allows).
- **Facts from the authority** (scripts/lc_names_index.py, lc_notes_index.py): birth and death (046 or the heading),
  670 source citations, 670 data, 373 affiliations, 372 fields. 374 occupation is not in the index.
- **Facts from the key**: titles of works credited to it (key-log AUTHORED / EDITED, the thesis included; linked
  credits kept apart by how they were made), PhD year (AHA record, key-log thesis), PhD school, dated affiliations
  (AFFILIATED_WITH), life years (data/person-facts/life-years.csv.gz), LCCNs of its key-log works.
- **Ties** (each is evidence the authority is this person):
  - `lc-record`: an LC record (2016 index) of a key-log credited work names the authority (heading $0 or its unique
    authorised form);
  - `title-keylog`: a 670 source cites a title the key log credits to the key, thesis included (three or more words
    as lc_canon_people.source_names_title; a one- or two-word main title only when the source opens with it and
    gives a year within two of the work's);
  - `title-identifier`: the same on a linked credit made by an identifier (an ORCID printed on the work, an LC
    heading), `title-rule`: on a linked credit made by a rule (prize winner, name-only linker, review signature);
  - `inst`: a 373 affiliation or the 670 data names an institution the key is affiliated with, or its PhD school
    (all distinctive words of the institution's name, aha_links.school);
  - `field-history` (372 or 670 data names history): support only, never a tie by itself.
- **Contradictions** (the pair is refused): LC birth year and the key's PhD outside ages 20-75, key-log works before
  age 15, PhD or key-log works more than 10 years after the LC death year, life years differing by more than 2.
- **Tiers**: strong = `lc-record` or `title-keylog`, or a title tie on a linked credit (`title-identifier`,
  `title-rule`) with `inst`; medium = a title tie on a linked credit alone, or `inst` alone when it is a 373 or the
  authority says history (372 / 670), and in both cases the name is unique (the authority's name and the key's are
  each borne by at most one live authority and one key) and the first given name is written the same on both sides;
  everything else is name only (held, counted). Hand check of the first run (2026-11-12): 57/60; the three wrong
  (an inst match on a forester and a communications scholar whose first names only began alike; a credit by
  identifier on a namesake's book) made these rules; the second (59/60: an ORCID record's namesake book seven years
  before the PhD) made the career window on linked-credit titles (a work more than five years before the PhD does
  not count).
- **Uniqueness**: a key with two authorities at its best tier, or an authority reaching two keys at its best tier,
  is held. An authority already anchored on another key is never attached; when it has a tie it is listed (the two
  keys may be one person: class 9).

Outputs (data/identifiers/lc-authority-anchors-2026-11-12/):
- proposal.json: attach `lcnaf:<id>` (and a status op to established for recorded keys) for strong and medium ties,
  decided_by rule, NOT applied;
- ties.csv.gz (every name-fitting pair with its facts and tier), held.csv.gz, report.json, hand-check.csv (60:
  stratified by tie type and name frequency; verdict column filled by hand);
- data/graph/lc-authority-ties.csv.gz: person, lcnaf, tier, ties, basis for strong and medium ties. Linked evidence,
  not key-log: scripts/link_cited_work_authors.People reads it so a tied authority is the key's own (not a namesake)
  and scripts/lc_catalogue_credits.py credits LC records under it (source lc-catalogue:tied-<tag>).

    python3 scripts/key_lc_authority_ties.py
"""
import csv
import gzip
import json
import os
import pickle
import random
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aha_links import first_and_family, fold, school  # noqa: E402
from key_aha_career import same_person_name  # noqa: E402
from lc_canon_people import DENIAL, STOP, main_title, words  # noqa: E402
from lc_resolve_authorities import label_dates  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / 'build/graph'
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
NOTES = Path('/mnt/e/lc-authorities/personal-notes.parquet')
ORGS = Path('/mnt/e/lc-authorities/organisations.parquet')
LC16 = Path('/mnt/e/lc-bib-2016/index')
OUT = ROOT / 'data/identifiers/lc-authority-anchors-2026-11-12'
TABLE = ROOT / 'data/graph/lc-authority-ties.csv.gz'
SCRATCH = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/lcties')
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'
IDENTIFIER_SOURCES = ('author-works:raw-orcid', 'lc-catalogue:', 'jstor-matched:lc', 'edition-roles:lc-main-entry',
                      'cited-works:lc-full:exact', 'cited-works:openalex:exact')
YEAR = re.compile(r'(1[5-9]\d\d|20[0-2]\d)')
HISTORY = re.compile(r'\bhistor', re.I)


def yr(v):
    m = re.match(r'-?(\d{4})', str(v or ''))
    return int(m.group(1)) if m else None


def lc_years(label, birth, death):
    b, d = yr(birth), yr(death)
    if b is None or d is None:
        ds = label_dates(label)
        m = re.match(r'(?:b\.\s*)?(\d{4})\??-(\d{4})?', ds or '')
        if m:
            b = b if b is not None else int(m.group(1))
            d = d if d is not None else (int(m.group(2)) if m.group(2) else None)
        elif (m2 := re.match(r'd\.\s*(\d{4})', ds or '')):
            d = d if d is not None else int(m2.group(1))
    return b, d


def name_form(label):
    """authorised heading without dates or qualifiers: 'Luby, Brittany, 1984-' -> 'Luby, Brittany'"""
    ds = label_dates(label)
    s = label[:len(label) - len(ds)] if ds else label
    return re.sub(r'\s*\([^)]*\)', '', s).strip(' ,.')


def name_forms(label):
    """the forms a heading is matched under: without dates and qualifiers, and with LC's fuller form of the given
    names in their place ('Barickman, B. J. (Bert Jude)' -> 'Barickman, B. J', 'Barickman, Bert Jude')"""
    out = [name_form(label)]
    m = re.match(r'([^,]+),\s*[^(]*\(([^)]+)\)', label or '')
    if m and re.search(r'[A-Za-z]{2}', m.group(2)):
        out.append(f'{m.group(1).strip()}, {m.group(2).strip()}')
    return [x for x in out if x]


def title_cited(sources, title, year):
    """a 670 source citation names this title. Three or more words: the run of words inside the citation (as
    lc_canon_people.source_names_title); one or two content words: the citation opens with the main title (after
    His/Her/Their) and a year within two of the work's year follows."""
    w = words(main_title(title))
    while len(w) > 3 and re.fullmatch(r'1[0-9]{3}|20[0-9]{2}', w[-1]):
        w = w[:-1]
    cw = [x for x in w if x not in STOP]
    if not cw:
        return False
    srcs = [s for s in sources if not DENIAL.search(s)]
    if len(w) >= 3 and len(cw) >= 2:
        needle = ' '.join(w)
        return any(needle in ' '.join(words(s)) for s in srcs)
    if len(''.join(cw)) < 5:
        return False
    for s in srcs:
        sw = words(s)
        sw = sw[1:] if sw[:1] in (['his'], ['her'], ['their']) else sw
        rest = sw[len(w):]
        if sw[:len(w)] == w and rest and re.fullmatch(r'1[5-9]\d\d|20\d\d', rest[0]) and \
                (year is None or abs(int(rest[0]) - year) <= 2):
            return True
    return False


def inst_named(insts, texts):
    """an institution of the key whose distinctive name words all appear in one of the texts (373 labels, 670 data)"""
    out = []
    tw = [school(t) for t in texts if t]
    for name in insts:
        s = school(name)
        if s and any(s <= t for t in tw):
            out.append(name)
    return out


def con():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(str(SCRATCH / 'ties.duckdb'))
    c.execute(f"SET memory_limit='4GB'; SET threads=3; SET preserve_insertion_order=false; SET temp_directory='{SCRATCH}/tmp'")
    return c


def load(c):
    q = lambda s, *a: c.execute(s, *a).fetchall()
    c.execute(f"""CREATE OR REPLACE TABLE keys AS SELECT key, label, resolution FROM '{G}/person.parquet'
        WHERE lcnaf IS NULL AND len(list_filter(anchors, a -> a LIKE 'lcnaf:%')) = 0 AND (
              len(list_filter(anchors, a -> a LIKE 'aha-phd:%' OR a LIKE 'diss-author:%' OR a LIKE 'capes-person:%'
                                          OR a LIKE 'ihr:%' OR a LIKE 'aha:%' OR a LIKE 'repo-advisor:%' OR a LIKE 'review-credit%')) > 0
           OR key IN (SELECT "from" FROM '{G}/supervised.parquet')
           OR key IN (SELECT "from" FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w ON w.key = a."to"
                      WHERE a.evidence = 'keylog' AND w.kind IN ('review', 'thesis')))""")
    keys = {k: dict(label=l, resolution=r, names=[l]) for k, l, r in q('SELECT key, label, resolution FROM keys')}
    s = sqlite3.connect(f"file:{ROOT / 'build/keylog-state.sqlite'}?mode=ro", uri=True)
    for k, al in s.execute('SELECT key, aliases FROM keys WHERE type = ? AND aliases IS NOT NULL AND aliases <> ?', ('person', '[]')):
        if k in keys:
            try:
                keys[k]['names'] += [a for a in json.loads(al) if a]
            except (TypeError, ValueError):
                pass
    anchored = dict(s.execute("SELECT substr(anchor, 7), key FROM anchor WHERE anchor LIKE 'lcnaf:%'").fetchall())
    s.close()
    # families of the keys' names
    fam = defaultdict(set)
    for k, d in keys.items():
        for n in d['names']:
            ff = first_and_family(n)
            if ff:
                fam[ff[1]].add(k)
    c.execute('CREATE OR REPLACE TABLE kf AS SELECT unnest(?) f', [sorted(fam)])
    # authorities whose authorised form or a variant has one of these families
    fexpr = "trim(regexp_replace(lower(strip_accents(replace(split_part({0}, ',', 1), '''', ''))), '[^a-z]+', ' ', 'g'))"
    c.execute(f"""CREATE OR REPLACE TABLE an AS
        WITH f AS (SELECT lcid, label, birth, death, nm, {fexpr.format('nm')} f FROM
                   (SELECT lcid, label, birth, death, unnest(list_prepend(label, coalesce(variants, []))) nm
                    FROM '{NAMES}' WHERE NOT deprecated AND NOT coalesce(undifferentiated, false)))
        SELECT * FROM f WHERE f IN (SELECT f FROM kf) AND nm LIKE '%,%'""")
    print('authority name forms with a key family', q('SELECT count(*), count(DISTINCT lcid) FROM an')[0], flush=True)
    return keys, fam, anchored


def main():
    c = con()
    q = lambda s, *a: c.execute(s, *a).fetchall()
    keys, fam, anchored = load(c)
    print(len(keys), 'keys', flush=True)
    # name agreement
    cache = SCRATCH / 'pairs.pkl'
    if cache.exists() and os.environ.get('TIES_REUSE_PAIRS'):
        pairs, auth = pickle.loads(cache.read_bytes())
    else:
        pairs, auth = name_pairs(q, keys)
        cache.write_bytes(pickle.dumps((pairs, auth)))
    print(len(pairs), 'name-fitting pairs', len({k for k, _ in pairs}), 'keys', flush=True)
    rest(c, q, keys, fam, anchored, pairs, auth)


def name_pairs(q, keys):
    pairs = defaultdict(set)                     # (key, lcid) -> name forms that agree
    auth = {}
    kidx = defaultdict(list)                     # (family, first letter of the first given name) -> (key, name)
    for k, d in keys.items():
        for n in d['names']:
            kf = first_and_family(n)
            if kf:
                kidx[kf[1], kf[0][:1]].append((k, n))
    for lcid, label, birth, death, nm, f in q('SELECT lcid, label, birth, death, nm, f FROM an'):
        auth[lcid] = (label, birth, death)
        for form in name_forms(nm):
            ff = first_and_family(form)
            if not ff:
                continue
            for k, n in kidx.get((ff[1], ff[0][:1]), ()):
                if (k, lcid) not in pairs and same_person_name(n, form):
                    pairs[k, lcid].add(form)
    return pairs, auth


def rest(c, q, keys, fam, anchored, pairs, auth):
    # name frequency: live authorities and person keys bearing (first given, family)
    nfa = Counter()
    for lcid, (label, _, _) in auth.items():
        ff = first_and_family(name_form(label))
        if ff:
            nfa[ff] += 1
    nfk = Counter()
    for k, l in q(f"SELECT key, label FROM '{G}/person.parquet'"):
        ff = first_and_family(l or '')
        if ff and ff[1] in fam:
            nfk[ff] += 1
    pk = sorted({k for k, _ in pairs})
    pl = sorted({a for _, a in pairs})
    c.execute('CREATE OR REPLACE TABLE pk AS SELECT unnest(?) AS key', [pk])
    c.execute('CREATE OR REPLACE TABLE pl AS SELECT unnest(?) AS lcid', [pl])
    # authority facts
    notes = {lcid: (n or [], a or [], f or []) for lcid, n, a, f in q(f"""SELECT lcid, notes, affiliations, fields FROM '{NOTES}'
                                                                        WHERE lcid IN (SELECT lcid FROM pl)""")}
    orgs = dict(q(f"""SELECT id, label FROM '{ORGS}' WHERE id IN (SELECT DISTINCT unnest(affiliations).org FROM '{NOTES}'
                     WHERE lcid IN (SELECT lcid FROM pl))"""))
    # key facts: credited works by evidence kind
    works = defaultdict(list)                    # key -> (title, year, kind, how)
    for k, title, y, kind, ev, src in q(f"""SELECT a."from", w.label, w.year, w.kind, a.evidence, coalesce(a.source, '')
            FROM (SELECT "from", "to", evidence, source FROM '{G}/authored.parquet' UNION ALL
                  SELECT "from", "to", evidence, source FROM '{G}/edited.parquet') a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE a."from" IN (SELECT key FROM pk)"""):
        how = 'keylog' if ev == 'keylog' else ('identifier' if src.startswith(IDENTIFIER_SOURCES) else 'rule')
        works[k].append((title or '', y, kind, how))
    aha = {}
    for line in open(AHA, encoding='utf-8'):
        r = json.loads(line)
        aha['aha-phd:' + r['id']] = (r.get('year'), r.get('department') or '', r.get('title') or '')
    phd, schools = {}, defaultdict(set)
    for k, an in q(f"SELECT key, anchors FROM '{G}/person.parquet' WHERE key IN (SELECT key FROM pk)"):
        for a in an or []:
            if a in aha:
                y, dep, t = aha[a]
                if y:
                    phd[k] = min(phd.get(k, int(y)), int(y))
                if dep:
                    schools[k].add(dep)
                if t and t != '[No title]':
                    works[k].append((t, int(y) if y else None, 'thesis', 'keylog'))
    for k, y, inst in q(f"""SELECT a."from", w.year, i.label FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w ON w.key = a."to"
            LEFT JOIN '{G}/awarded_by.parquet' b ON b."from" = w.key LEFT JOIN '{G}/institution.parquet' i ON i.key = b."to"
            WHERE a.evidence = 'keylog' AND w.kind = 'thesis' AND a."from" IN (SELECT key FROM pk)"""):
        if y:
            phd[k] = min(phd.get(k, y), y)
        if inst:
            schools[k].add(inst)
    affs = defaultdict(set)
    for k, lab in q(f"""SELECT a."from", i.label FROM '{G}/affiliated_with.parquet' a JOIN '{G}/institution.parquet' i ON i.key = a."to"
                      WHERE a."from" IN (SELECT key FROM pk)"""):
        if lab:
            affs[k].add(lab)
    kl_years = {k: (lo, hi) for k, lo, hi in q(f"""SELECT a."from", min(w.year), max(w.year) FROM '{G}/authored.parquet' a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE a.evidence = 'keylog' AND w.year BETWEEN 1400 AND 2027
            AND w.kind <> 'review' AND a."from" IN (SELECT key FROM pk) GROUP BY 1""")}
    life = {}
    with gzip.open(ROOT / 'data/person-facts/life-years.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            life[r['key']] = (yr(r['birth']), yr(r['death']))
    # lc-record: LC 2016 records of key-log credited works naming the authority
    c.execute(f"""CREATE OR REPLACE TABLE kw AS SELECT DISTINCT a."from" AS key, lower(regexp_replace(coalesce(w.lccn, substr(x, 6)), '\\s', '', 'g')) lccn
        FROM '{G}/authored.parquet' a JOIN (SELECT key, lccn, unnest(list_append(anchors, NULL)) x FROM '{G}/work.parquet') w ON w.key = a."to"
        WHERE a.evidence = 'keylog' AND a."from" IN (SELECT key FROM pk) AND (w.lccn IS NOT NULL OR x LIKE 'lccn:%')""")
    c.execute(f"""CREATE OR REPLACE TABLE kwh AS SELECT kw.key, h.heading, h.uri FROM kw JOIN '{LC16}/records-*.parquet' r
        ON r.lccn = kw.lccn OR trim(r.control) = kw.lccn JOIN '{LC16}/headings-*.parquet' h ON trim(h.control) = trim(r.control)""")
    lcrec = defaultdict(set)
    labmap = defaultdict(set)
    for lcid, (label, _, _) in auth.items():
        labmap[label.rstrip(' .')].add(lcid)
    for k, heading, uri in q('SELECT key, heading, uri FROM kwh'):
        m = re.search(r'([a-z]+[0-9]+)/?$', uri or '')
        ids = {m.group(1)} if m else (labmap.get((heading or '').rstrip(' .'), set()) if len(labmap.get((heading or '').rstrip(' .'), ())) == 1 else set())
        for i in ids:
            lcrec[k].add(i)
    print('facts loaded', flush=True)

    rows = []
    for (k, lcid), forms in pairs.items():
        label, birth, death = auth[lcid]
        b, d = lc_years(label, birth, death)
        n, aff, fields = notes.get(lcid, ([], [], []))
        sources = [x.split(' :: ', 1)[0] for x in n]
        data = [x.split(' :: ', 1)[1] if ' :: ' in x else '' for x in n]
        aff_labels = [orgs.get(a['org'], '') for a in aff]
        bad = []
        p = phd.get(k)
        lo_hi = kl_years.get(k)
        if b and p and not b + 20 <= p <= b + 75:
            bad.append(f'phd-{p}-vs-birth-{b}')
        if b and lo_hi and lo_hi[0] < b + 15:
            bad.append(f'work-{lo_hi[0]}-before-age-15')
        if d and p and p > d:
            bad.append(f'phd-after-death-{d}')
        if d and lo_hi and lo_hi[1] > d + 10:
            bad.append(f'work-{lo_hi[1]}-after-death-{d}')
        kb, kd = life.get(k, (None, None))
        if b and kb and abs(b - kb) > 2:
            bad.append(f'birth-{kb}-vs-{b}')
        if d and kd and abs(d - kd) > 2:
            bad.append(f'death-{kd}-vs-{d}')
        ties, basis = [], []
        if lcid in lcrec.get(k, ()):
            ties.append('lc-record')
        for how in ('keylog', 'identifier', 'rule'):
            # a linked credit counts only inside the key's career: not more than five years before its PhD (an ORCID
            # record can carry a namesake's earlier book: Luke Ritter, PhD 2014, 'Securing global transportation
            # networks', 2006)
            hit = next((t for t, y, kind, h in works.get(k, []) if h == how and title_cited(sources, t, y)
                        and (how == 'keylog' or not (y and p and y < p - 5))), None)
            if hit:
                ties.append(f'title-{how}')
                basis.append(f'670 cites "{hit[:80]}" ({how})')
        kinst = sorted(affs.get(k, set()) | schools.get(k, set()))
        inst373, inst670 = inst_named(kinst, aff_labels), inst_named(kinst, data)
        if inst373 or inst670:
            ties.append('inst')
            basis.append(f"LC {'373' if inst373 else '670'} names {(inst373 or inst670)[0][:60]}")
        support = bool(HISTORY.search(' '.join(data + list(fields))))
        ff = first_and_family(name_form(label))
        kff = first_and_family(keys[k]['label'])
        freq_a, freq_k = nfa.get(ff, 0), nfk.get(ff, 0)
        # unique: the authority's name and the key's own name are each borne by at most one authority and one key
        unique = freq_a <= 1 and freq_k <= 1 and (not kff or (nfa.get(kff, 0) <= 1 and nfk.get(kff, 0) <= 1))
        # the first given name written out the same on both sides (not Jenn / Jennifer, Philip / Phillip)
        same_first = bool(kff and ff and kff[0] == ff[0]) or any(
            (x := first_and_family(n)) and ff and x[0] == ff[0] for n in keys[k]['names'])
        t = set(ties)
        if bad:
            tier = 'contradicted'
        elif {'lc-record', 'title-keylog'} & t or ({'title-identifier', 'title-rule'} & t and 'inst' in t):
            tier = 'strong'
        elif unique and same_first and ({'title-identifier', 'title-rule'} & t or
                                        ('inst' in t and (support or inst373))):
            tier = 'medium'
        else:
            tier = 'name-only'
        rows.append(dict(person=k, person_label=keys[k]['label'], lcnaf=lcid, lc_label=label, name_forms='; '.join(sorted(forms)),
                         tier=tier, ties=' '.join(ties), support='field-history' if support else '', contradictions=' '.join(bad),
                         basis='; '.join(basis), lc_birth=b or '', lc_death=d or '', phd_year=p or '',
                         anchored_on=anchored.get(lcid, ''), name_freq_lc=freq_a, name_freq_keys=freq_k,
                         sources=' | '.join(sources)[:400], resolution=keys[k]['resolution']))
    rank = {'strong': 3, 'medium': 2, 'name-only': 1, 'contradicted': 0}
    byk, bya = defaultdict(list), defaultdict(list)
    for r in rows:
        byk[r['person']].append(r)
        bya[r['lcnaf']].append(r)
    for r in rows:
        r['decision'] = ''
        if r['tier'] in ('strong', 'medium'):
            if r['anchored_on']:
                r['decision'] = 'held:authority-on-another-key'
            elif sum(1 for x in byk[r['person']] if rank[x['tier']] >= rank[r['tier']] and not x['anchored_on']) > 1:
                r['decision'] = 'held:key-has-two-authorities'
            elif sum(1 for x in bya[r['lcnaf']] if rank[x['tier']] >= rank[r['tier']]) > 1:
                r['decision'] = 'held:authority-fits-two-keys'
            elif any(rank[x['tier']] > rank[r['tier']] for x in byk[r['person']]):
                r['decision'] = 'held:key-has-a-stronger-authority'
            else:
                r['decision'] = 'attach'
    att = [r for r in rows if r['decision'] == 'attach']
    # outputs
    OUT.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with gzip.open(OUT / 'ties.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        wr.writerows(sorted(rows, key=lambda r: (r['person'], r['lcnaf'])))
    with gzip.open(OUT / 'held.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        wr.writerows(sorted([r for r in rows if r['decision'].startswith('held')], key=lambda r: (r['person'], r['lcnaf'])))
    with gzip.open(TABLE, 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['person', 'lcnaf', 'tier', 'ties', 'basis'])
        for r in sorted(att, key=lambda r: (r['person'], r['lcnaf'])):
            wr.writerow([r['person'], r['lcnaf'], r['tier'], r['ties'], r['basis']])
    ops = []
    for r in sorted(att, key=lambda r: (r['person'], r['lcnaf'])):
        ops.append(dict(event='attach', key=r['person'], anchors=[f"lcnaf:{r['lcnaf']}"], aliases=[], members=[],
                        decided_by='rule', basis=f"LC authority {r['lcnaf']} '{r['lc_label']}' is {r['person_label']} "
                                                 f"({r['tier']}: {r['ties']}; {r['basis']})"))
        if r['resolution'] != 'established':
            ops.append(dict(event='status', key=r['person'], resolution='established', decided_by='rule',
                            basis='a public identifier (LC name authority) tied by evidence'))
    (OUT / 'proposal.json').write_text(json.dumps(dict(
        basis='Keyed people with scholarly evidence and no LC anchor joined to their LC name authority by record linkage: '
              'names agree, no date contradiction, and a tie from the authority\'s own data (an LC record of a key-log work, '
              'a 670 citing a credited title, a 373/670 institution of the key); scripts/key_lc_authority_ties.py',
        decided_by='rule', ops=ops), indent=1, ensure_ascii=False) + '\n')
    # hand check sample: stratified by tie type and name frequency
    rnd = random.Random(1112)

    def stratum(r):
        t = 'lc-record' if 'lc-record' in r['ties'] else 'title' if 'title' in r['ties'] else 'inst'
        return f"{r['tier']}|{t}|{'unique' if r['name_freq_lc'] <= 1 and r['name_freq_keys'] <= 1 else 'shared'}"
    strata = defaultdict(list)
    for r in att:
        strata[stratum(r)].append(r)
    sample, per = [], max(1, 60 // max(1, len(strata)))
    for s in sorted(strata):
        sample += rnd.sample(strata[s], min(per, len(strata[s])))
    rest = [r for r in att if r not in sample]
    sample += rnd.sample(rest, min(60 - len(sample), len(rest))) if len(sample) < 60 else []
    hc = OUT / 'hand-check.csv'
    old = {}
    if hc.exists():
        with open(hc, encoding='utf-8') as f:
            old = {(r['person'], r['lcnaf']): (r['verdict'], r['note']) for r in csv.DictReader(f)}
    with open(hc, 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['stratum', 'person', 'person_label', 'lcnaf', 'lc_label', 'tier', 'ties', 'basis', 'phd_year', 'lc_birth',
                     'sources', 'verdict', 'note'])
        for r in sample[:60]:
            v = old.get((r['person'], r['lcnaf']), ('', ''))
            wr.writerow([stratum(r), r['person'], r['person_label'], r['lcnaf'], r['lc_label'], r['tier'], r['ties'], r['basis'],
                         r['phd_year'], r['lc_birth'], r['sources'][:300], *v])
    # class size
    k_one = Counter()
    free = defaultdict(list)
    for r in rows:
        if not r['anchored_on'] and r['tier'] != 'contradicted':
            free[r['person']].append(r)
    for k, rs in free.items():
        k_one['exactly_one' if len(rs) == 1 else 'several'] += 1
    rep = dict(
        population_keys=len(keys), keys_with_name_fitting_authority=len({r['person'] for r in rows}),
        keys_with_free_name_fitting_authority=dict(k_one), pairs=len(rows), pairs_by_tier=dict(Counter(r['tier'] for r in rows)),
        pairs_by_decision=dict(Counter(r['decision'] or 'not-tied' for r in rows)),
        attach=len(att), attach_by_tier=dict(Counter(r['tier'] for r in att)),
        attach_by_tie=dict(Counter(stratum(r) for r in att)),
        attach_status_ops=sum(1 for o in ops if o['event'] == 'status'),
        authority_on_another_key_with_tie=sum(1 for r in rows if r['decision'] == 'held:authority-on-another-key'),
        lc_name_file='id.loc.gov names.madsrdf.jsonld.gz downloaded 2026-10-30 (authorities to that date; post-2016 held)',
        note='name-only pairs are not proposed; contradicted pairs are refused; applied: no')
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
