"""Canon-map people -> LC name authorities and life dates, through the books the theses cite (PID-PLAN.md section 6).

For each person on the canon map (data/dissertation-layer/site/canon-map.json) the script takes their
most-cited books in the dissertation graph (authored.csv.gz + works.csv, kind = book) and searches the
LC catalogue by main title and surname (SRU, `dc.title` and `dc.creator`, up to five records). A record
counts only if:
- its title (245 $a) agrees with the cited title (same main title after normalisation, or token overlap
  of at least 0.8; the cited main title needs two or more content words), and
- exactly one of its personal-name headings is compatible with the person's name
  (identity_routes.compatible, plus `given_agrees`: when both sides spell out a given name, the names
  must be variants of one name, so 'Angus' does not match 'Arlene').
The heading is resolved through the local LC name index (scripts/lc_names_index.py), as in
scripts/lc_resolve_authorities.py. A book resolves only if every title-agreeing record names the same
authority (otherwise `records_disagree`: namesakes behind one title). Books are tried most-cited first,
up to --books, until the authority is confirmed; two books naming different authorities give
`books_disagree`.

An offline pass runs first: a name-compatible authority whose LC 670 sources cite one of the person's
books. When that book is not the person's most-cited one, the most-cited book is still checked in the
catalogue, because a canon key can carry a namesake's book (2026-10-31: 'Billig, Michael' carried a
book by Michael S. Billig); a different authority there gives `books_disagree`.

**Tiers** (reviewed by a Fable agent on 2026-10-30). A canon key is a name cluster from bibliography
parsing, so one book only shows that *a* person of that name wrote it:
- `exact`: the key has a full given name and at least one confirmation: a second book naming the same
  authority, an LC 670 source citing the title, or LC's own Wikidata link equal to a title-verified
  dissertation QID. Only this tier may become an `lcnaf:` anchor in the key log.
- `candidate_single_book`, `candidate_initials_only` (a single initial: 'Taylor, A.' mixes people;
  two or more initials, 'Thompson, E. P.', count as a full name),
  `candidate_wikidata_disagrees`: recorded for review, never anchors.
Life dates are read with their source (046 or heading) and precision.

Read-only against the repository; LC responses are cached.

    python3 scripts/lc_canon_people.py --cache /mnt/e/lc-authorities/sru-canon \\
        --names /mnt/e/lc-authorities/personal-names.parquet --out data/field-research/lc-authorities-2026-10-30/canon
"""
import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import State  # noqa: E402
from identity_routes import compatible  # noqa: E402
from key_canon_map import CANON, D, TITLE_TIERS, canon_keys  # noqa: E402
from lc_authority_pilot import MARC, SRU, Fetcher, bib_headings  # noqa: E402
from lc_catalogue_harvest import record_facts  # noqa: E402
from lc_resolve_authorities import label_dates, life, load_names, resolve  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRU5 = SRU.replace('maximumRecords=1', 'maximumRecords=5')
STOP = {'the', 'a', 'an', 'of', 'and', 'in', 'on', 'to', 'for', 'la', 'le', 'les', 'de', 'des', 'du', 'et', 'l', 'd'}


def words(t):
    # Apostrophes are dropped, not split on, so a straight and a curly one give the same words: LC's
    # "Labour's war" and a cited "Labour’s War" both read 'labours war' (found 2026-10-31, Stephen Brooke).
    t = re.sub(r"['\u2018\u2019\u02bc`]", '', t or '')
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.findall(r'[a-z0-9]+', t)


def main_title(t):
    """The title before its subtitle. Periods are not split on ('St. Louis', 'U.S. Foreign Policy')."""
    return re.split(r'\s*[:;=/]\s*', t or '', maxsplit=1)[0].strip(' .,')


def content(t):
    return [w for w in words(main_title(t)) if w not in STOP]


def titles_agree(cited, record):
    """Same main title after normalisation, or token overlap >= 0.8; at least two content words."""
    a, b = words(main_title(cited)), words(main_title(record))
    sa, sb = set(content(cited)), set(content(record))
    if len(sa) < 2 or not b:
        return False
    return a == b or len(sa & sb) / len(sa | sb) >= 0.8


# A 670 that denies authorship names the title too: 'Email from author ...: not author of Households of
# faith, Engendering the state' (Christie, Nancy, 1954-, 2026-10-31). Such notes never count.
DENIAL = re.compile(r"\bnot (?:the )?(?:author|same|to be confused|identical)\b|\bnot\b[^.;]{0,40}\bauthor of\b", re.I)


def source_names_title(sources, cited):
    """An LC 670 source citation that contains the cited main title (three or more words). A two-word
    title ('Labour's war') counts only when the citation opens with it, after 'His'/'Her'/'Their', and a
    year or the end follows: the form LC uses for the person's own book ('His Labour's war, 1992:')."""
    w = words(main_title(cited))
    if len([x for x in w if x not in STOP]) < 2:
        return False
    sources = [s for s in sources if not DENIAL.search(s)]
    needle = ' '.join(w)
    if len(w) >= 3:
        return any(needle in ' '.join(words(s)) for s in sources)
    for s in sources:
        sw = words(s)
        sw = sw[1:] if sw[:1] in (['his'], ['her'], ['their']) else sw
        rest = sw[len(w):]
        if sw[:len(w)] == w and (not rest or re.fullmatch(r'1[5-9]\d\d|20\d\d', rest[0])):
            return True
    return False


NICKNAMES = {'tom': 'thomas', 'mike': 'michael', 'ted': 'theodore', 'wm': 'william', 'bill': 'william',
             'bob': 'robert', 'dick': 'richard', 'jim': 'james', 'jack': 'john', 'harry': 'henry',
             'terry': 'terence', 'tony': 'anthony', 'ned': 'edward', 'sandy': 'alexander', 'peggy': 'margaret',
             'kate': 'katherine', 'betty': 'elizabeth', 'chuck': 'charles', 'hank': 'henry', 'nick': 'nicholas',
             # the same name in another language, as LC headings give it
             'georg': 'gyorgy', 'pieter': 'petrus', 'john': 'jean'}
FOLD = str.maketrans({'ł': 'l', 'Ł': 'L', 'ø': 'o', 'Ø': 'O', 'đ': 'd', 'ß': 'ss', 'ı': 'i'})


PARTICLES = {'de', 'du', 'des', 'la', 'le', 'von', 'van', 'der', 'den', 'di', 'da', 'del', 'dos'}


def _token_agrees(a, b):
    """Two given-name tokens: initials agree on the letter; spelled-out names must match, one must be a
    prefix of the other (Ken/Kenneth, Jan/Janet), share four leading letters with lengths at most one
    apart (Maria/Mariia, not Christine/Christopher), or be a listed nickname or equivalent."""
    if len(a) == 1 or len(b) == 1:
        return a[0] == b[0]
    short, long_ = sorted((a, b), key=len)
    return a == b or (len(short) >= 3 and long_.startswith(short)) \
        or (a[:4] == b[:4] and len(short) >= 4 and len(long_) - len(short) <= 1) \
        or NICKNAMES.get(a) == b or NICKNAMES.get(b) == a


def given_agrees(person, lc):
    """Given names as variants of one name (2026-10-31; 'Angus' had matched 'Arlene', 'Mary Frances' had
    matched 'Mary Elizabeth').
    - First names: the person's first name must agree with LC's first, or with any later LC given name
      when both are spelled out ('Jane' in 'Errington, Elizabeth Jane').
    - Middle names: when both sides have more given names (particles such as 'de' set aside), at least
      one pair must agree ('Charles-Louis de Secondat' and 'Charles de Secondat' do; 'John Henry' and
      'John Paul' do not)."""
    p, l = words((person or '').translate(FOLD)), words((lc or '').translate(FOLD))
    p, l = p[:1] + [t for t in p[1:] if t not in PARTICLES], l[:1] + [t for t in l[1:] if t not in PARTICLES]   # 'Van Gosse'
    if not p or not l:
        return False
    if _token_agrees(p[0], l[0]):
        rest_p, rest_l = p[1:], l[1:]
    elif len(p[0]) > 1 and len(l[0]) > 1 and (i := next((i for i, b in enumerate(l[1:], 1)
                                                            if len(b) > 1 and _token_agrees(p[0], b)), 0)):
        rest_p, rest_l = p[1:], l[:i] + l[i + 1:]
    else:
        return False
    return not rest_p or not rest_l or any(_token_agrees(x, y) for x in rest_p for y in rest_l)


def initials_only(label):
    """A single initial ('Taylor, A.'): such keys pool several people. Two or more initials
    ('Thompson, E. P.') are specific enough to be treated like a full name."""
    toks = re.findall(r'[^\W\d_]+', label.partition(', ')[2])
    return len(toks) < 2 and all(len(x) == 1 for x in toks)


def records(xml):
    """Each MARC record of an SRU response, wrapped so bib_headings/record_facts can read it alone."""
    out = []
    for rec in ET.fromstring(xml).iter(f'{MARC}record'):
        wrap = ET.Element('wrap')
        wrap.append(rec)
        s = ET.tostring(wrap, encoding='unicode')
        out.append((bib_headings(s)[0], record_facts(s)))
    return out


def as_credit(label):
    """'Thompson, E. P.' -> 'E. P. Thompson' (the form identity_routes.compatible expects)."""
    family, comma, given = label.partition(', ')
    return f'{given} {family}' if comma else label


# 'book_or_serial' works are books unless the title reads as a serial (2026-10-31: Brooke's Sexual Politics,
# OUP 2011, was book_or_serial and never tried; 'Journal of Social History' is the same kind).
SERIAL = re.compile(r'\b(journal|review|quarterly|bulletin|annals|proceedings|transactions|magazine|newsletter|'
                    r'revue|zeitschrift|rivista|annales|gazette|yearbook)\b', re.I)


def books_by_person(keys, per_person):
    db = duckdb.connect()
    db.execute("CREATE TABLE k(person_key VARCHAR)")
    db.executemany("INSERT INTO k VALUES (?)", [(k,) for k in keys])
    db.execute(f"""CREATE TABLE a AS SELECT person_key, work_id FROM read_csv('{D / 'authored.csv.gz'}', all_varchar=true)
                   WHERE person_key IN (SELECT person_key FROM k)""")
    rows = db.execute(f"""
        SELECT a.person_key, w.work_id, w.title, w.year, CAST(w.cited_by_dissertations AS INTEGER) AS n
        FROM a JOIN read_csv('{D / 'works.csv'}', all_varchar=true, max_line_size=10000000) w USING (work_id)
        WHERE w.kind IN ('book', 'book_or_serial') AND w.title IS NOT NULL
        ORDER BY a.person_key, n DESC, w.work_id""").fetchall()
    out = defaultdict(list)
    for key, wid, title, year, n in rows:
        if len(out[key]) < per_person and len(content(title)) >= 2 and not SERIAL.search(main_title(title)):
            out[key].append(dict(work_id=wid, title=title, year=year or '', cited=n))
    return out


def settle_owners(offline, person_books, by_id):
    """Authorities whose LC 670s own different books of one canon name (2026-10-31 review of the rerun).

    - Two records with the same name and birth year are one person recorded twice by LC ('Miller, Perry,
      1905-1963' and the provisional 'Miller, Perry, 1905-'): kept as the record with more sources.
    - When one authority owns at least 75% of the owned citations, and the most-cited book is its own or in
      no 670, the canon key is
      that person with a namesake's minor works mixed in ('Carter, Sarah, 1954-' and Sarah Anne Carter's
      Tangible things): the key resolves to the dominant authority and the other works are returned as
      namesake works to split later.
    Otherwise the owners are left as they are (a pooled name).
    Returns (owners, namesake_works as 'lcid:work_id ...').
    """
    if len(offline) < 2:
        return offline, ''
    def ident(lcid):
        label = by_id[lcid]['label']
        dates = label_dates(label)
        name = label[:len(label) - len(dates)].rstrip(', ') if dates else label
        born = re.match(r'(\d{4})', dates or '')
        return (name.split(' (')[0], born.group(1) if born else '')
    groups = defaultdict(list)
    for lcid in offline:
        groups[ident(lcid)].append(lcid)
    merged = {}
    for (name, born), ids in groups.items():
        if born or len(ids) == 1:
            keep = max(ids, key=lambda i: (len(by_id[i]['sources']), i))
            merged[keep] = [h for i in ids for h in offline[i]]
        else:
            merged.update({i: offline[i] for i in ids})
    if len(merged) < 2:
        return merged, ''
    cites = {lcid: sum(int(h['cited'] or 0) for h in hits) for lcid, hits in merged.items()}
    top = person_books[0]['work_id'] if person_books else ''
    top_owner = next((lcid for lcid, hits in merged.items() if any(h['work_id'] == top for h in hits)), '')
    owner = max(cites, key=lambda i: (cites[i], i))
    # The most-cited book must not belong to another authority (it may belong to none: Carter's Lost
    # harvests is in no 670).
    if top_owner in ('', owner) and cites[owner] >= 0.75 * sum(cites.values()):
        minor = ' '.join(f"{lcid}:{h['work_id']}" for lcid, hits in sorted(merged.items()) if lcid != owner for h in hits)
        return {owner: merged[owner]}, minor
    return merged, ''


def query(title, family):
    t = ' '.join(words(main_title(title))[:8])
    f = (words(family) or [''])[0]
    return f'dc.title="{t}" and dc.creator={f}' if t and f else ''


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--books', type=int, default=5, help='books tried in the catalogue per person')
    ap.add_argument('--offline-books', type=int, default=8, help='books checked against LC 670 sources per person')
    ap.add_argument('--delay', type=float, default=2.0)
    ap.add_argument('--pause', type=float, default=60)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--people', help="only these canon labels, ';'-separated ('Brooke, Stephen;Coates, Colin'); "
                    'loads only their surnames from the name index, so it needs little memory')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    canon = json.loads(CANON.read_text(encoding='utf-8'))
    nodes = sorted(canon['nodes'], key=lambda n: -n['cited'])
    if args.limit:
        nodes = nodes[:args.limit]
    if args.people:
        wanted_labels = {x.strip() for x in args.people.split(';')}
        nodes = [n for n in nodes if n['label'] in wanted_labels or n['name'] in wanted_labels]
    graph_key = canon_keys(canon['nodes'])
    state = State.load(ROOT / 'data/identifiers/events.jsonl')
    books = books_by_person({graph_key[n['name'], n['qid']] for n in nodes}, max(args.books, args.offline_books))
    qid_basis = {}
    with (D / 'cited-people.csv').open(newline='', encoding='utf-8') as f:
        wanted = set(graph_key.values())
        for r in csv.DictReader(f):
            if r['person_key'] in wanted:
                qid_basis[r['person_key']] = r['qid_basis']
    if args.people:
        db = duckdb.connect()
        fams = sorted({n['label'].partition(', ')[0] for n in nodes})
        names = load_names(args.names, {r[0] for f in fams for r in db.execute(
            f"SELECT lcid FROM read_parquet('{args.names}') WHERE label ILIKE ?", [f + ',%']).fetchall()})
    else:
        names = load_names(args.names)
    by_id = names[0]
    print(f'{len(nodes)} canon people; {sum(map(len, books.values()))} books to try; {len(by_id):,} LC names', flush=True)
    fetch = Fetcher(args.cache, args.delay)
    surnames = {' '.join(words(n['label'].partition(', ')[0])) for n in nodes}
    by_surname = defaultdict(list)          # live, differentiated personal names with a canon surname
    for lcid, a in by_id.items():
        s = ' '.join(words(a['label'].partition(', ')[0]))
        if s in surnames and not a['deprecated'] and not a['undifferentiated'] and a['sources']:
            by_surname[s].append(lcid)

    rows, stats, streak = [], Counter(), 0
    for k, n in enumerate(nodes, 1):
        gk = graph_key[n['name'], n['qid']]
        key = state.lookup(f'diss-person:{gk}')
        family = n['label'].partition(', ')[0]
        person = as_credit(n['label'])
        found, tried, outcome = [], 0, 'no_book'
        # Offline first: an authority with a compatible name whose 670 sources cite one of the person's
        # cited books. LC's own record of what the person wrote; no catalogue request needed.
        offline = {}
        for lcid in by_surname.get(' '.join(words(family)), ()):
            a = by_id[lcid]
            fam, _, given = a['label'].partition(', ')
            given = given.split(', ')[0]
            fuller = given.split(' (')[1].rstrip(')') if ' (' in given else ''
            pg = n['label'].partition(', ')[2]
            if not ((compatible(person, given.split(' (')[0], fam) and given_agrees(pg, given.split(' (')[0])) or
                    (fuller and compatible(person, fuller, fam) and given_agrees(pg, fuller))):
                continue
            hits = [b for b in books.get(gk, []) if source_names_title(a['sources'], b['title'])]
            if hits:
                offline[lcid] = hits
        offline, namesakes = settle_owners(offline, books.get(gk, []), by_id)
        cited_in_670 = defaultdict(set)         # work -> compatible authorities whose 670 cites it
        for lcid, hits in offline.items():
            for h in hits:
                cited_in_670[h['work_id']].add(lcid)
        if len(offline) == 1:
            lcid, hits = next(iter(offline.items()))
            src = by_id[lcid]['sources']
            found = [dict(lcid=lcid, via='lc_670', book=h,
                          record_title=next((s for s in src if source_names_title([s], h['title'])), ''))
                     for h in hits]
        elif offline and not set.intersection(*({h['work_id'] for h in hits} for hits in offline.values())) \
                and all(len(owners) == 1 for owners in cited_in_670.values()):
            # LC's own notes give different books of this name to different people: the canon key pools
            # namesakes ('Salmon, John': Renaissance and revolt is J. H. M. Salmon's, Wealthy Corinth John
            # Salmon's, b. 1942). No authority can be the key's.
            outcome = 'books_disagree'
            stats[outcome] += 1
            rows.append(dict(key=key[0] if len(key) == 1 else '', graph_key=gk, label=n['label'], cited=n['cited'],
                             dissertation_qid=n['qid'] or '', dissertation_qid_basis=qid_basis.get(gk, ''),
                             outcome=outcome, books_tried=0, via='lc_670_owners', namesake_works=namesakes,
                             evidence_works=' '.join(f"{lcid}:{h['work_id']}" for lcid, hits in sorted(offline.items())
                                                     for h in hits)))
            continue
        elif offline:
            outcome = 'offline_670_ambiguous'      # several namesakes cite the same title; try the catalogue
        # Catalogue: every book when the offline pass found nothing; otherwise the most-cited book, when
        # the offline hit rests on a lesser one.
        top = books.get(gk, [])[:1]
        catalogue = books.get(gk, [])[:args.books] if not found else \
            [b for b in top if b['work_id'] not in {f['book']['work_id'] for f in found}]
        for b in catalogue:
            q = query(b['title'], family)
            r = fetch.get(SRU5 + urllib.parse.quote(q))
            if r['status'] == 0:
                streak += 1
                if streak >= 3:
                    time.sleep(args.pause)
                outcome = outcome if found else 'unanswered'
                continue
            streak, tried = 0, tried + 1
            try:
                recs = records(r['body'])
            except ET.ParseError:
                continue
            ids, seen_title = set(), False
            for heads, facts in recs:
                if not titles_agree(b['title'], facts.get('title', '')):
                    continue
                seen_title = True
                pg = n['label'].partition(', ')[2]
                match = [h for h in heads if (compatible(person, h['given'], h['family']) and given_agrees(pg, h['given']))
                         or (h['fuller'] and compatible(person, h['fuller'], h['family']) and given_agrees(pg, h['fuller']))]
                if len(match) > 1:
                    ids.add('ambiguous')
                elif match:
                    lcid, via = resolve(match[0], names)
                    # A heading matched only by its text can be an old form left on the bib record after
                    # LC created a separate authority (2026-10-31: 'Brooke, Stephen.' on Labour's war
                    # resolves to n84045320, the 1983 author; LC's 670 gives the book to no2025022468,
                    # 'Brooke, Stephen J.'). LC's own source note for this book wins.
                    owners = cited_in_670.get(b['work_id'], set())
                    if via != 'bib_$0' and len(owners) == 1 and lcid not in owners:
                        lcid, via = next(iter(owners)), 'lc_670_over_heading'
                    if lcid and not by_id[lcid]['undifferentiated']:
                        ids.add(lcid)
                        hit = dict(lcid=lcid, via=via, book=b, record_title=facts['title'])
            if len(ids) == 1 and 'ambiguous' not in ids:
                found.append(hit)
            elif ids:
                outcome = outcome if found else 'records_disagree'      # namesakes behind one title
                continue
            else:
                outcome = outcome if found else ('person_not_resolved' if seen_title else
                                                 'no_title_match' if recs else 'no_lc_record')
                continue
            lcids = {f['lcid'] for f in found}
            if len(lcids) > 1:
                break
            a = by_id[found[0]['lcid']]
            lc_qids = {e.rsplit('/', 1)[-1] for e in a['external'] if 'wikidata.org/entity/' in e}
            if (n['qid'] and n['qid'] in lc_qids and qid_basis.get(gk) in TITLE_TIERS) or \
                    any(source_names_title(a['sources'], f['book']['title']) for f in found) or len(found) >= 2:
                break           # confirmed: no need for more books
        lcids = {f['lcid'] for f in found}
        if len(lcids) > 1:
            outcome = 'books_disagree'
        elif lcids:
            outcome = 'resolved'
        stats[outcome] += 1
        row = dict(namesake_works=namesakes, key=key[0] if len(key) == 1 else '', graph_key=gk, label=n['label'], cited=n['cited'],
                   dissertation_qid=n['qid'] or '', dissertation_qid_basis=qid_basis.get(gk, ''),
                   outcome=outcome, books_tried=tried)
        if outcome == 'resolved':
            f, a = found[0], by_id[found[0]['lcid']]
            lf = life(a, label_dates(a['label']))
            lc_qids = {e.rsplit('/', 1)[-1] for e in a['external'] if 'wikidata.org/entity/' in e}
            wd = ('' if not lc_qids or not n['qid'] else 'agrees' if n['qid'] in lc_qids else 'disagrees')
            src = any(source_names_title(a['sources'], x['book']['title']) for x in found)
            confirmations = [c for c, ok in (('second_book', len(found) >= 2), ('lc_670_names_title', src),
                                             ('wikidata_agrees', wd == 'agrees' and
                                              qid_basis.get(gk) in TITLE_TIERS)) if ok]
            if initials_only(n['label']):
                tier = 'candidate_initials_only'
            elif wd == 'disagrees':
                tier = 'candidate_wikidata_disagrees'
            elif confirmations:
                tier = 'exact'
            else:
                tier = 'candidate_single_book'
            row.update(lcnaf=f['lcid'], lc_label=a['label'], via=f['via'], tier=tier,
                       confirmations=' '.join(confirmations), books_agreeing=len(found),
                       evidence_works=' '.join(x['book']['work_id'] for x in found),
                       evidence_title=f['record_title'],
                       birth_year=lf['birth'][0], birth_value=lf['birth'][1], birth_source=lf['birth'][2],
                       birth_precision=lf['birth'][3], death_year=lf['death'][0], death_value=lf['death'][1],
                       death_source=lf['death'][2], death_precision=lf['death'][3],
                       external=' '.join(e for e in a['external'] if 'viaf.org/en/viaf/LC' not in e),
                       lc_wikidata=' '.join(sorted(lc_qids)), wikidata_check=wd)
        rows.append(row)
        if k % 100 == 0:
            print(f'{k}/{len(nodes)} people, {fetch.requests} requests, {dict(stats)}', flush=True)

    fields = ['key', 'graph_key', 'label', 'cited', 'dissertation_qid', 'dissertation_qid_basis', 'outcome',
              'books_tried', 'lcnaf', 'lc_label', 'via', 'tier', 'confirmations', 'books_agreeing', 'evidence_works',
              'evidence_title', 'birth_year', 'birth_value', 'birth_source', 'birth_precision', 'death_year',
              'death_value', 'death_source', 'death_precision', 'external', 'lc_wikidata', 'wikidata_check', 'namesake_works']
    with open(args.out / 'canon-people-lc.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    res = [r for r in rows if r['outcome'] == 'resolved']
    summary = dict(canon_snapshot=canon['snapshot'], people=len(rows), requests=fetch.requests,
                   outcomes=dict(stats.most_common()),
                   with_birth_year=sum(1 for r in res if r['birth_year']),
                   with_death_year=sum(1 for r in res if r['death_year']),
                   wikidata_check=dict(Counter(r['wikidata_check'] or 'not_checkable' for r in res)),
                   tiers=dict(Counter(r['tier'] for r in res).most_common()),
                   birth_source=dict(Counter(r['birth_source'] or 'none' for r in res)),
                   unresolved_keys_reached=sum(1 for r in res if r['key'] and
                                               state.keys[r['key']]['resolution'] == 'unresolved'))
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
