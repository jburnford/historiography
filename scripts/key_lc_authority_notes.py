"""A keyed person's LC name authority found through the titles its 670 source notes name (2026-11-14; ARCHITECTURE.md
section 8, class 40). Writes a key-log PROPOSAL (not applied), a review tier, a possible-duplicate list and the notes'
titles for the missing-books table (scripts/lc_note_books.py).

Probe: Valerie Deacon (p-37340: AHA PhD 2011, thesis "The 'Other' Resistance: The Extreme Right in France during the
Second World War") has LC authority n2016049415 'Deacon, Valerie, 1981-' whose only 670 is "Her The extreme Right in the
French Resistance, 2016:". The 11-12 pass (key_lc_authority_ties.py, class 34) found the pair but left it name-only: its
title tie needs the key's whole main title inside the 670 ("the other resistance" is not there), and a thesis becomes
a book under a new title. A reader ties them by the rare words the two titles share (extreme, right, resistance) and the
dates (born 1981, PhD 2011, book 2016).

Record linkage, one key and one authority at a time:
- **Population**: live person keys with no `lcnaf:` anchor holding at least one titled work: the AHA PhD record's title
  (`aha-phd:` anchor), key-log AUTHORED / EDITED works other than reviews (thesis, book, article, chapter, other). A key
  printed with initials only never qualifies.
- **Authorities**: live, differentiated LC personal names (id.loc.gov dump of 2026-10-30) with 670 notes, whose
  authorised form (its fuller form included) or a 400 variant agrees with the key's label or an alias under the strict
  rule (propose_person_dup_merges.names_agree: same family, the first written-out given name identical, other given
  names compatible, Jr/Sr block; never a nickname, never initials alone).
- **Notes**: each 670 source citation is read as a work: 'His/Her/Their <title>, <year>:' (own), 'Family, Given. <title>,
  <year>:' with the authority's family (own, older style), the same with another family (another's work, e.g. a
  co-authored or contributed book), or a bare '<title>, <year>:' (the catalogued item). Database, web, mail and
  telephone sources, and notes denying authorship, are skipped.
- **Title ties** (on key-log titles only; linked credits are never evidence):
  - `same`: the note names a title the key holds: main titles agree (lc_canon_people.titles_agree), or the key's main
    title (3+ words) runs inside the note (key_lc_authority_ties.title_cited);
  - `thesis-book`: the key's thesis and a book in the note, published T-1..T+20 (T = the thesis year), sharing the rare
    words: rarity weights are idf over every work title in the graph and the notes' titles (stemmed, stop words of
    five languages out); at least two shared words with idf >= RARE, the shared weight >= MIN_SHARED, and the shared
    weight covers >= COVER of the note title's weight or of the thesis title's weight.
- **Dates** (the pair is refused): LC birth and the thesis year outside ages 22-70; a note year before birth + 18; key-log
  works before birth + 15; the thesis after the LC death year, key-log works more than 3 years after it; key life
  years differing from LC's by more than 2; a tied note year outside T-9..T+50 (`same`).
- **Name group**: bearers = live authorities whose name agrees with the key's (date-possible ones) and live person keys
  whose name agrees with the authority's (keys holding a different `lcnaf:` anchor are separated and do not count).
  `closed`: the key is the only unseparated key for the authority; `rare`: at most RARE_LC date-possible authorities
  bear the key's name.
- **Tiers**: `strict` = a title tie, no date contradiction, the name group closed or rare, the given names written the
  same on both sides (not only through a variant or an alias), one authority for the key and one key for the
  authority; `review` = every other title-tied pair (a weaker overlap, an open name group, a tie through an alias or
  variant, two authorities or two keys). An authority already anchored on another key is never attached: when a title
  ties it to this key the pair goes to possible-duplicates.csv.gz (the two keys may be one person, class 9).

Outputs (data/identifiers/lc-authority-notes-2026-11-14/): proposal.json (attach + status ops, decided_by rule, NOT
applied; validated by `identifiers.py apply --dry-run`), review-tier.csv.gz, possible-duplicates.csv.gz, ties.csv.gz
(every title-tied pair with its facts), sample-checked.csv (hand check, verdict column filled by hand), report.json.

    python3 scripts/key_lc_authority_notes.py              # NOTES_REUSE=1 reuses the cached name pairs
"""
import csv
import gzip
import json
import math
import os
import pickle
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from key_lc_authority_ties import lc_years, name_forms, title_cited  # noqa: E402
from lc_canon_people import DENIAL, main_title, titles_agree, words  # noqa: E402
from link_cited_work_authors import fam_norm, forms  # noqa: E402
from propose_person_dup_merges import names_agree  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / 'build/graph'
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
NOTES = Path('/mnt/e/lc-authorities/personal-notes.parquet')
AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
OUT = ROOT / 'data/identifiers/lc-authority-notes-2026-11-14'
SCRATCH = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/lcnotes')

RARE = 6.0          # idf of a distinctive word (about 1 title in 400)
MIN_SHARED = 16.0   # shared rare weight (about two or three distinctive words)
COVER = 0.5         # share of the note title's (or the thesis title's) weight the shared words carry
RARE_LC = 2         # a name borne by at most this many date-possible authorities is rare

STOPW = set('''the a an of and in on to for from by with at as or its his her their this that these those into upon
toward towards during between among under over through after before since until about against without within
la le les de des du et l d un une au aux en dans par pour sur sous avec entre
der die das den dem des und im in zum zur von vom fur fuer mit auf aus bei als ein eine einer eines einem einen uber ueber
el los las del y en por para con sobre entre lo al una unos unas
il lo gli i della delle dei degli di e nel nella sul sulla tra fra da do da dos das e o os as no na nos nas um uma
new study studies some'''.split())
NONWORK = re.compile(r'data ?base|wikipedia|e-?mail|\bphone|telephone|web ?site|\bwww\b|viewed|\bnuc\b|copac|oclc|viaf|'
                     r'info\. from|information from|correspondence|google|\bisni\b|orcid|linkedin|facebook|obituar|'
                     r'letter from|\bcall to\b|conversation|personal communication|internet|homepage|blog|\burl\b|'
                     r'nucmc|national register|authority file|name authority|\blcsh\b|\bdnb\b|\bbnf\b|\bgnd\b', re.I)
YEAR_END = re.compile(r'^(.*?)[,.]?\s*\[?(?:c|p|©|cop\.)?\s*(1[5-9]\d\d|20[0-2]\d)\??\]?(?:-\d{2,4})?\s*[:.]?\s*$')


def yr(v):
    m = re.match(r'-?(\d{4})', str(v or ''))
    return int(m.group(1)) if m else None


def stem(w):
    if len(w) > 4 and w.endswith('ies'):
        return w[:-3] + 'y'
    if len(w) > 4 and w.endswith('s') and not w.endswith('ss') and not w.endswith('us') and not w.endswith('is'):
        return w[:-1]
    return w


def toks(title):
    return {stem(w) for w in words(title) if w not in STOPW and len(w) > 1 and not w.isdigit()}


def initials_only(label):
    fs = forms(label)
    return not fs or all(all(len(w) == 1 for w in g) for _, _, g in fs)


def parse_source(src, fam, given=()):
    """a 670 source citation -> (form, title, year) or None. form: own / own-name / other-author / bare. `given`: the
    authority's given names (folded), so 'Rice, M. Elizabeth Ann. The diplomatic ...' loses 'Elizabeth Ann.' too."""
    s = (src or '').strip()
    if not s or DENIAL.search(s) or NONWORK.search(s):
        return None
    form = 'bare'
    s = re.sub(r'^(?:nuc\s?[\d-]+|LCCN\s+\S+|\S+\s+data)\s*:\s*', '', s, flags=re.I)   # 'nuc87-52716: Her ...' (NUC reports)
    m = re.match(r'^(?:His|Her|Their|Its)\s+(.*)$', s)
    if m:
        form, s = 'own', m.group(1)
    else:
        m = re.match(r"^([^\W\d][^,.:;()]{0,40}),\s*([^,.:;()]{1,40}?)\.\s+(\S.*)$", s)
        if m and len(m.group(1).split()) <= 4 and len(m.group(2).split()) <= 4:
            form = 'own-name' if fam_norm(m.group(1)) == fam else 'other-author'
            s = m.group(3)
            if re.fullmatch(r'(?:.*\s)?[A-Z]', m.group(2)):            # 'Smith, J. A. The history': the second initial
                s = re.sub(r'^[A-Z]\.\s+(?=\S)', '', s)
            g = re.match(r'^((?:[^\W\d][\w\'-]*\s?){1,3})\.\s+(\S.*)$', s)
            if g and given and all(w in given for w in words(g.group(1))):
                s = g.group(2)
    s = re.sub(r'\s*\[[^\]]*\]\s*', ' ', s).strip()                  # '[ER]', '[microform]'
    m = YEAR_END.match(s)
    if not m:
        return None
    title, year = m.group(1).strip(' ,.;:/'), int(m.group(2))
    if len(words(title)) < 2:
        return None
    return form, title, year


def con():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(str(SCRATCH / 'notes.duckdb'))
    c.execute(f"SET memory_limit='5GB'; SET threads=4; SET preserve_insertion_order=false; SET temp_directory='{SCRATCH}/tmp'")
    return c


def load_keys(c):
    q = lambda s, *a: c.execute(s, *a).fetchall()
    people = {k: dict(label=l or '', resolution=r, anchors=list(a or []), lcnaf=lc)
              for k, l, r, a, lc in q(f"SELECT key, label, resolution, anchors, lcnaf FROM '{G}/person.parquet'")}
    titles = defaultdict(list)                                    # key -> (title, year, kind, source)
    for k, title, y, kind in q(f"""SELECT a."from", w.label, w.year, w.kind
            FROM (SELECT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog' UNION
                  SELECT "from", "to" FROM '{G}/edited.parquet' WHERE evidence = 'keylog') a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.kind NOT IN ('review') AND w.label IS NOT NULL"""):
        titles[k].append((title, y, kind, 'keylog'))
    aha = {}
    for line in open(AHA, encoding='utf-8'):
        r = json.loads(line)
        aha['aha-phd:' + r['id']] = (r.get('year'), r.get('department') or '', r.get('title') or '')
    phd, schools = {}, defaultdict(set)
    for k, p in people.items():
        for a in p['anchors']:
            if a in aha:
                y, dep, t = aha[a]
                y = int(y) if y else None
                if y:
                    phd[k] = min(phd.get(k, y), y)
                if dep:
                    schools[k].add(dep)
                if t and t != '[No title]':
                    titles[k].append((t, y, 'thesis', 'aha'))
    for k, ts in titles.items():
        for t, y, kind, _ in ts:
            if kind == 'thesis' and y:
                phd[k] = min(phd.get(k, y), y)
    s = sqlite3.connect(f"file:{ROOT / 'build/keylog-state.sqlite'}?mode=ro", uri=True)
    aliases = defaultdict(list)
    for k, al in s.execute("SELECT key, aliases FROM keys WHERE type = 'person' AND aliases IS NOT NULL AND aliases <> '[]'"):
        if k in people:
            try:
                aliases[k] = [a for a in json.loads(al) if a and ':' not in a[:12]]
            except (TypeError, ValueError):
                pass
    anchored = dict(s.execute("SELECT substr(anchor, 7), key FROM anchor WHERE anchor LIKE 'lcnaf:%'").fetchall())
    s.close()
    life = {}
    with gzip.open(LIFE, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            life[r['key']] = (yr(r['birth']), yr(r['death']))
    pop = {k for k, p in people.items() if not p['lcnaf'] and not any(a.startswith('lcnaf:') for a in p['anchors'])
           and titles.get(k) and not initials_only(p['label'])}
    return people, titles, phd, schools, aliases, anchored, life, pop


def name_pairs(c, people, aliases, pop):
    """(key, lcid) -> (label agrees, form) for keys in pop; and lcid -> (label, birth, death)"""
    q = lambda s, *a: c.execute(s, *a).fetchall()
    kidx = defaultdict(list)        # (family, first written-out given name) -> (key, name, is_label); names_agree needs both
    for k in pop:
        for i, n in enumerate([people[k]['label']] + aliases.get(k, [])):
            for f, _, g in forms(n):
                w1 = next((w for w in g if len(w) > 1), None)
                if w1:
                    kidx[f, w1].append((k, n, i == 0))
    c.execute('CREATE OR REPLACE TABLE kf AS SELECT unnest(?) f', [sorted({f for f, _ in kidx})])
    fexpr = "trim(regexp_replace(lower(strip_accents(replace(split_part(nm, ',', 1), '''', ''))), '[^a-z]+', ' ', 'g'))"
    rows = q(f"""WITH a AS (SELECT n.lcid, n.label, n.birth, n.death, unnest(list_prepend(n.label, coalesce(n.variants, []))) nm,
                        generate_subscripts(list_prepend(n.label, coalesce(n.variants, [])), 1) i
                 FROM '{NAMES}' n SEMI JOIN '{NOTES}' t ON t.lcid = n.lcid AND len(t.notes) > 0
                 WHERE NOT n.deprecated AND NOT coalesce(n.undifferentiated, false))
        SELECT lcid, label, birth, death, nm, i FROM a WHERE nm LIKE '%,%' AND {fexpr} IN (SELECT f FROM kf)""")
    print(len(rows), 'authority name forms with a key family', flush=True)
    pairs, auth = {}, {}
    for lcid, label, birth, death, nm, i in rows:
        auth[lcid] = (label, birth, death)
        for form in name_forms(nm):
            for f, _, g in forms(form):
                w1 = next((w for w in g if len(w) > 1), None)
                for k, n, is_label in kidx.get((f, w1), ()) if w1 else ():
                    if names_agree(n, form):
                        main = is_label and i == 1
                        old = pairs.get((k, lcid))
                        if not old or (main and not old[0]):
                            pairs[k, lcid] = (main, f'{n} ~ {form}')
    return pairs, auth


def idf_table(c, extra_titles):
    q = lambda s: c.execute(s).fetchall()
    df, n = Counter(), 0
    cur = c.execute(f"SELECT label FROM '{G}/work.parquet' WHERE label IS NOT NULL")
    while True:
        rows = cur.fetchmany(200000)
        if not rows:
            break
        for (t,) in rows:
            n += 1
            df.update(toks(t))
    for t in extra_titles:
        n += 1
        df.update(toks(t))
    return {w: math.log(n / (1 + d)) for w, d in df.items()}, math.log(n)


def overlap(a, b, idf, top):
    ta, tb = toks(a), toks(b)
    w = lambda x: idf.get(x, top)
    sh = ta & tb
    s = sum(w(x) for x in sh)
    wa, wb = sum(w(x) for x in ta) or 1, sum(w(x) for x in tb) or 1
    rare = [x for x in sh if w(x) >= RARE]
    return dict(shared=' '.join(sorted(sh, key=lambda x: -w(x))), shared_w=round(s, 1), n_rare=len(rare),
                cover_note=round(s / wb, 2), cover_key=round(s / wa, 2))


def main():
    c = con()
    q = lambda s, *a: c.execute(s, *a).fetchall()
    people, titles, phd, schools, aliases, anchored, life, pop = load_keys(c)
    print(len(pop), 'keys in the population', flush=True)
    cache = SCRATCH / 'pairs.pkl'
    if cache.exists() and os.environ.get('NOTES_REUSE'):
        pairs, auth = pickle.loads(cache.read_bytes())
    else:
        pairs, auth = name_pairs(c, people, aliases, pop)
        cache.write_bytes(pickle.dumps((pairs, auth)))
    print(len(pairs), 'name-agreeing pairs on', len({k for k, _ in pairs}), 'keys', flush=True)
    c.execute('CREATE OR REPLACE TABLE pl AS SELECT unnest(?) AS lcid', [sorted({a for _, a in pairs})])
    notes = {lcid: n or [] for lcid, n in q(f"SELECT lcid, notes FROM '{NOTES}' WHERE lcid IN (SELECT lcid FROM pl)")}
    parsed = {}
    for lcid, ns in notes.items():
        fam = next((f for f, _, _ in forms(auth[lcid][0])), '')
        giv = {w for _, _, g in forms(auth[lcid][0]) for w in g}
        parsed[lcid] = [(p, x) for x in ns if (p := parse_source(x.split(' :: ', 1)[0], fam, giv))]
    idf, top = idf_table(c, [t for ps in parsed.values() for (_, t, _), _ in ps])
    print('idf over', len(idf), 'words', flush=True)

    # name bands: date-possible authorities per key; unseparated keys per authority
    rows = []
    by_key_auth = defaultdict(list)
    by_auth_key = defaultdict(list)
    for (k, lcid), (main, form) in pairs.items():
        label, birth, death = auth[lcid]
        b, d = lc_years(label, birth, death)
        T = phd.get(k)
        ys = [y for _, y, kind, _ in titles[k] if y and 1400 < y < 2030]
        lo, hi = (min(ys), max(ys)) if ys else (None, None)
        bad = []
        if b and T and not b + 22 <= T <= b + 70:
            bad.append(f'thesis-{T}-vs-birth-{b}')
        if b and lo and lo < b + 15:
            bad.append(f'work-{lo}-before-age-15')
        if d and T and T > d:
            bad.append(f'thesis-after-death-{d}')
        if d and hi and hi > d + 3:
            bad.append(f'work-{hi}-after-death-{d}')
        kb, kd = life.get(k, (None, None))
        if b and kb and abs(b - kb) > 2:
            bad.append(f'birth-{kb}-vs-{b}')
        if d and kd and abs(d - kd) > 2:
            bad.append(f'death-{kd}-vs-{d}')
        if not bad:
            by_key_auth[k].append(lcid)
            if not anchored.get(lcid) or anchored.get(lcid) == k:
                by_auth_key[lcid].append(k)
        # title ties
        best = None
        for (form_, ntitle, ny), raw in parsed.get(lcid, []):
            if b and ny < b + 18:
                continue
            for t, y, kind, src in titles[k]:
                tie = None
                if titles_agree(t, ntitle) or (len(words(main_title(t))) >= 3 and title_cited([raw.split(' :: ', 1)[0]], t, y)):
                    if T is None or T - 9 <= ny <= T + 50:
                        tie, ov = 'same', overlap(t, ntitle, idf, top)
                elif kind == 'thesis' and y and y - 1 <= ny <= y + 20:
                    ov = overlap(t, ntitle, idf, top)
                    if ov['n_rare'] >= 2 and ov['shared_w'] >= MIN_SHARED and max(ov['cover_note'], ov['cover_key']) >= COVER:
                        tie = 'thesis-book'
                    elif ov['n_rare'] >= 1 and ov['shared_w'] >= 8:
                        tie = 'weak-overlap'
                if tie:
                    rank = {'same': 3, 'thesis-book': 2, 'weak-overlap': 1}[tie]
                    if not best or rank > best[0] or (rank == best[0] and ov['shared_w'] > best[1]['shared_w']):
                        best = (rank, ov, dict(tie=tie, key_title=t, key_year=y or '', key_kind=kind, key_title_source=src,
                                              note_form=form_, note_title=ntitle, note_year=ny, note=raw[:300]))
        if best:
            rows.append(dict(person=k, person_label=people[k]['label'], lcnaf=lcid, lc_label=label, label_agrees=main,
                             name_match=form, lc_birth=b or '', lc_death=d or '', thesis_year=T or '',
                             contradictions=' '.join(bad), anchored_on=anchored.get(lcid, ''), **best[2], **best[1],
                             resolution=people[k]['resolution']))
    print(len(rows), 'title-tied pairs', flush=True)
    # same name across all keys (for 'closed'): keys whose label agrees with the authority's heading, not separated
    fam_keys = defaultdict(list)
    need = {f for r in rows for f, _, _ in forms(r['lc_label'])}
    for k, p in people.items():
        for f, _, _ in forms(p['label']):
            if f in need:
                fam_keys[f].append(k)
    for r in rows:
        k, lcid = r['person'], r['lcnaf']
        others = set()
        for f, _, _ in forms(r['lc_label']):
            for k2 in fam_keys.get(f, ()):
                p2 = people[k2]
                if k2 == k or (p2['lcnaf'] and p2['lcnaf'] != lcid):
                    continue
                if names_agree(p2['label'], r['lc_label']):
                    others.add(k2)
        r['other_keys'] = ' '.join(sorted(others)[:8])
        r['n_other_keys'] = len(others)
        r['lc_bearers'] = len(by_key_auth.get(k, []))
        r['closed'] = not others
        r['rare'] = r['lc_bearers'] <= RARE_LC
        r['band'] = 'unique' if r['lc_bearers'] <= 1 else '2-5' if r['lc_bearers'] <= 5 else '6-25' if r['lc_bearers'] <= 25 else '26+'
    # decisions
    rank = {'same': 3, 'thesis-book': 2, 'weak-overlap': 1}
    tied = [r for r in rows if not r['contradictions'] and r['tie'] in ('same', 'thesis-book')]
    tk, ta = defaultdict(list), defaultdict(list)
    for r in tied:
        if not r['anchored_on']:
            tk[r['person']].append(r)
            ta[r['lcnaf']].append(r)
    for r in rows:
        if r['contradictions']:
            r['decision'] = 'refused:dates'
        elif r['tie'] == 'weak-overlap':
            r['decision'] = 'not-tied:weak-overlap'
        elif r['anchored_on'] and r['anchored_on'] != r['person']:
            r['decision'] = 'possible-duplicate'
        elif len(tk[r['person']]) > 1:
            r['decision'] = 'review:key-has-two-authorities'
        elif len(ta[r['lcnaf']]) > 1:
            r['decision'] = 'review:authority-fits-two-keys'
        elif not (r['closed'] or r['rare']):
            r['decision'] = 'review:name-group-open'
        elif not r['label_agrees']:
            r['decision'] = 'review:variant-or-alias-only'
        else:
            r['decision'] = 'strict'
    strict = [r for r in rows if r['decision'] == 'strict']
    review = [r for r in rows if r['decision'].startswith('review')]
    dups = [r for r in rows if r['decision'] == 'possible-duplicate']
    OUT.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())

    def dump(path, rs):
        with gzip.open(path, 'wt', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(sorted(rs, key=lambda r: (r['person'], r['lcnaf'])))
    dump(OUT / 'ties.csv.gz', rows)
    dump(OUT / 'review-tier.csv.gz', review)
    dump(OUT / 'possible-duplicates.csv.gz', dups)
    ops = []
    for r in sorted(strict, key=lambda r: (r['person'], r['lcnaf'])):
        ops.append(dict(event='attach', key=r['person'], anchors=[f"lcnaf:{r['lcnaf']}"], aliases=[], members=[],
                        decided_by='rule',
                        basis=f"LC authority {r['lcnaf']} '{r['lc_label']}' is {r['person_label']}: its 670 names "
                              f"'{r['note_title'][:90]}' ({r['note_year']}), {r['tie']} of the key's {r['key_kind']} "
                              f"'{r['key_title'][:90]}' ({r['key_year']}); shared words: {r['shared'][:60]}; dates fit; "
                              f"name {'closed' if r['closed'] else 'rare'} (scripts/key_lc_authority_notes.py)"))
        if r['resolution'] != 'established':
            ops.append(dict(event='status', key=r['person'], resolution='established', decided_by='rule',
                            basis='a public identifier (LC name authority) tied by a title in its source notes'))
    (OUT / 'proposal.json').write_text(json.dumps(dict(
        basis="Keyed people with a titled work and no LC anchor joined to their LC name authority: names agree in full, "
              "a 670 source note names the key's work or the book of its thesis (rare words shared), dates fit, the name "
              "group closed or rare; scripts/key_lc_authority_notes.py",
        decided_by='rule', ops=ops), indent=1, ensure_ascii=False) + '\n')
    # hand-check sample: stratified by name band and tie
    strata = defaultdict(list)
    for r in strict:
        strata[f"{r['tie']}|{r['band']}"].append(r)
    per = max(1, 130 // max(1, len(strata)))
    import hashlib
    hk = lambda r: hashlib.md5(f"{r['person']}|{r['lcnaf']}".encode()).hexdigest()    # stable across reruns
    sample = []
    for s_ in sorted(strata):
        sample += sorted(strata[s_], key=hk)[:per]
    left = sorted((r for r in strict if r not in sample), key=hk)
    sample += left[:max(0, 130 - len(sample))]
    sc = OUT / 'sample-checked.csv'
    old = {}
    if sc.exists():
        with open(sc, encoding='utf-8') as f:
            old = {(r['person'], r['lcnaf']): (r['verdict'], r['note_by_hand']) for r in csv.DictReader(f)}
    with open(sc, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['stratum', 'person', 'person_label', 'lcnaf', 'lc_label', 'tie', 'key_kind', 'key_title', 'key_year',
                    'note_title', 'note_year', 'shared', 'shared_w', 'cover_note', 'lc_bearers', 'n_other_keys', 'note',
                    'verdict', 'note_by_hand'])
        for r in sorted(sample, key=lambda r: (r['tie'], r['band'], r['person'])):
            v = old.get((r['person'], r['lcnaf']), ('', ''))
            w.writerow([f"{r['tie']}|{r['band']}", r['person'], r['person_label'], r['lcnaf'], r['lc_label'], r['tie'],
                        r['key_kind'], r['key_title'][:200], r['key_year'], r['note_title'][:200], r['note_year'], r['shared'],
                        r['shared_w'], r['cover_note'], r['lc_bearers'], r['n_other_keys'], r['note'][:250], *v])
    rep = dict(
        population_keys=len(pop), name_agreeing_pairs=len(pairs), keys_with_a_name_agreeing_authority=len({k for k, _ in pairs}),
        title_tied_pairs=len(rows), pairs_by_tie=dict(Counter(r['tie'] for r in rows)),
        pairs_by_decision=dict(Counter(r['decision'] for r in rows)),
        strict=len(strict), strict_by_tie=dict(Counter(r['tie'] for r in strict)),
        strict_by_band=dict(Counter(r['band'] for r in strict)),
        strict_by_key_title_source=dict(Counter(r['key_title_source'] for r in strict)),
        strict_status_ops=sum(1 for o in ops if o['event'] == 'status'),
        review_tier=len(review), possible_duplicates=len(dups),
        thresholds=dict(RARE=RARE, MIN_SHARED=MIN_SHARED, COVER=COVER, RARE_LC=RARE_LC),
        lc_name_file='id.loc.gov names dump of 2026-10-30', applied='no')
    if not os.environ.get('NOTES_NO_VALIDATE'):
        import identifiers as I
        import keylog_snapshot as KS
        I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
        state = KS.read_state()
        events, _ = I.materialise(state, json.loads((OUT / 'proposal.json').read_text()), 'dry-run', 'dry-run', inplace=True)
        rep['dry_run_events'] = len(events)
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))
    for r in rows:
        if r['person'] == 'p-37340':
            print('PROBE', {x: r[x] for x in ('lcnaf', 'tie', 'decision', 'shared', 'shared_w', 'cover_note', 'band', 'closed')})


if __name__ == '__main__':
    main()
