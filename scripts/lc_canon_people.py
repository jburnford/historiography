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
scripts/lc_resolve_authorities.py. A book is attributed only if every title-agreeing record names the
same authority (otherwise `records_disagree`: namesakes behind one title).

An offline pass runs first: name-compatible authorities whose LC 670 sources cite one of the person's
books (only the closest names: see `closest_names`). A book cited in exactly one such 670 is that
authority's. The catalogue then takes the most-cited books the 670s do not settle, the most-cited book
always, until one confirmed authority holds at least half the citations of the books looked at.

Who the name belongs to (2026-10-31 rerun review, `dominant`): one authority; or one holding at least
75% of the attributed citations, the most-cited book its own or unattributed (the other authorities'
books are listed as `namesake_works`); otherwise `books_disagree`, a pooled name. LC duplicate records
(same name and birth year) count as one.

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
    t = re.sub(r"['\u2018\u2019\u02bc`]", '', t or '').translate(FOLD)
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
# letters NFKD leaves alone; 'œ' had read 'Ricœur' as 'ricur' (2026-10-31)
FOLD = str.maketrans({'ł': 'l', 'Ł': 'L', 'ø': 'o', 'Ø': 'O', 'đ': 'd', 'ß': 'ss', 'ı': 'i', 'œ': 'oe', 'Œ': 'Oe',
                      'æ': 'ae', 'Æ': 'Ae'})


PARTICLES = {'de', 'du', 'des', 'la', 'le', 'von', 'van', 'der', 'den', 'di', 'da', 'del', 'dos'}


def _token_agrees(a, b, nick=True):
    """Two given-name tokens: initials agree on the letter; spelled-out names must match, one must be a
    prefix of the other (Ken/Kenneth, Jan/Janet), share four leading letters with lengths at most one
    apart (Maria/Mariia, not Christine/Christopher), or be a listed nickname or equivalent (`nick`)."""
    if len(a) == 1 or len(b) == 1:
        return a[0] == b[0]
    short, long_ = sorted((a, b), key=len)
    return a == b or (len(short) >= 3 and long_.startswith(short)) \
        or (a[:4] == b[:4] and len(short) >= 4 and len(long_) - len(short) <= 1) \
        or (nick and (NICKNAMES.get(a) == b or NICKNAMES.get(b) == a))


def closest_names(person_given, cands):
    """The candidates whose given names are closest to the person's (2026-10-31 rerun review). `cands`:
    (item, LC given name) pairs, all already compatible. Two narrowings, each applied only when some
    candidate survives it:
    - names that agree without the nickname/translation table beat those that need it ('Jean' is
      'Comaroff, Jean', not 'Comaroff, John L.', though 'john' and 'jean' are listed as one name);
    - when the person spells out a middle name, candidates carrying it beat those without ('Scott, James
      Brown' is not 'Scott, James, 1916-')."""
    p = [t for t in words((person_given or '').translate(FOLD)) if t not in PARTICLES]
    if not p:
        return cands
    def plain(forms):
        return any(given_agrees(person_given, g, nick=False) for g in forms)
    def carries_middle(forms):
        l = [y for g in forms for y in words((g or '').translate(FOLD)) if len(y) > 1]
        return all(any(_token_agrees(x, y, nick=False) for y in l) for x in p[1:] if len(x) > 1)
    out = [c for c in cands if plain(c[1])] or cands
    if any(len(x) > 1 for x in p[1:]):
        out = [c for c in out if carries_middle(c[1])] or out
    return out


def given_agrees(person, lc, nick=True):
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
    if _token_agrees(p[0], l[0], nick):
        rest_p, rest_l = p[1:], l[1:]
    elif len(p[0]) > 1 and len(l[0]) > 1 and (i := next((i for i, b in enumerate(l[1:], 1)
                                                            if len(b) > 1 and _token_agrees(p[0], b, nick)), 0)):
        rest_p, rest_l = p[1:], l[:i] + l[i + 1:]
    else:
        return False
    return not rest_p or not rest_l or any(_token_agrees(x, y, nick) for x in rest_p for y in rest_l)


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


def merge_duplicates(ids, by_id):
    """Two records with the same name and birth year are one person recorded twice by LC ('Miller, Perry,
    1905-1963' and the provisional 'Miller, Perry, 1905-'): each maps to the record with more sources.
    Returns {lcid: kept lcid}."""
    def ident(lcid):
        label = by_id[lcid]['label']
        dates = label_dates(label)
        name = label[:len(label) - len(dates)].rstrip(', ') if dates else label
        born = re.match(r'(\d{4})', dates or '')
        return (name.split(' (')[0], born.group(1) if born else '')
    groups = defaultdict(list)
    for lcid in ids:
        groups[ident(lcid)].append(lcid)
    out = {}
    for (name, born), group in groups.items():
        keep = max(group, key=lambda i: (len(by_id[i]['sources']), i)) if born else None
        out.update({i: keep or i for i in group})
    return out


def dominant(owner_of, person_books):
    """The authority a canon name belongs to when its books are spread over several (2026-10-31 rerun
    review). `owner_of`: work -> authority, from LC 670 notes or the catalogue. One authority wins when it
    holds at least 75% of the attributed citations and the most-cited book is its own or unattributed: the
    key is that person with a namesake's minor works mixed in ('Carter, Sarah, 1954-' and Sarah Anne
    Carter's Tangible things; Norman Davies and Norman de Garis Davies's Rock tombs of El Amarna).
    Otherwise None: a pooled name ('Salmon, John': J. H. M. Salmon and John Salmon, b. 1942)."""
    cites = Counter()
    for b in person_books:
        if b['work_id'] in owner_of:
            cites[owner_of[b['work_id']]] += int(b['cited'] or 0)
    if len(cites) == 1:
        return next(iter(cites))
    if not cites:
        return None
    owner = max(cites, key=lambda i: (cites[i], i))
    top_owner = owner_of.get(person_books[0]['work_id'], '') if person_books else ''
    return owner if top_owner in ('', owner) and cites[owner] >= 0.75 * sum(cites.values()) else None


def bare_name(label):
    """An LC heading without its dates and qualifiers: 'Bender, Thomas, 1944-' -> 'bender thomas'."""
    dates = label_dates(label)
    name = label[:len(label) - len(dates)] if dates else label
    return ' '.join(words(name.split(' (')[0].rstrip(', .')))


def born_before(authority, year, gap=20):
    """True unless LC's birth year shows the person was under `gap` years old when the book appeared."""
    born = re.match(r'-?(\d{4})', str(authority.get('birth') or '')) or re.search(r'(\d{4})-', label_dates(authority['label']) or '')
    y = re.match(r'(\d{4})', str(year or ''))
    return not (born and y) or int(y.group(1)) >= int(born.group(1)) + gap


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
        fams = sorted({' '.join(words(n['label'].partition(', ')[0])) for n in nodes})
        names = load_names(args.names, {r[0] for f in fams for r in db.execute(
            f"SELECT lcid FROM read_parquet('{args.names}') WHERE strip_accents(replace(replace(lower(label), 'œ', 'oe'), "
            "'æ', 'ae')) LIKE ?", [f + ',%']).fetchall()})
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
        person = as_credit(n['label'].translate(FOLD))
        tried, outcome = 0, 'no_book'
        pg = n['label'].partition(', ')[2]
        person_books = books.get(gk, [])
        # Offline first: authorities with a compatible name (the closest names only) whose 670 sources cite
        # one of the person's cited books. LC's own record of what the person wrote; no request needed.
        compat = []
        for lcid in by_surname.get(' '.join(words(family)), ()):
            a = by_id[lcid]
            fam, _, given = a['label'].translate(FOLD).partition(', ')
            given = given.split(', ')[0]
            fuller = given.split(' (')[1].rstrip(')') if ' (' in given else ''
            if (compatible(person, given.split(' (')[0], fam) and given_agrees(pg, given.split(' (')[0])) or \
                    (fuller and compatible(person, fuller, fam) and given_agrees(pg, fuller)):
                compat.append((lcid, [given.split(' (')[0]] + ([fuller] if fuller else [])))
        cited_in_670 = defaultdict(set)         # work -> compatible authorities whose 670 cites it
        for lcid, _ in closest_names(pg, compat):
            for b in person_books:
                if source_names_title(by_id[lcid]['sources'], b['title']):
                    cited_in_670[b['work_id']].add(lcid)
        owner_of, via_of, title_of = {}, {}, {}     # work -> authority, how, LC's wording
        for b in person_books:
            owners = cited_in_670.get(b['work_id'], set())
            if len(owners) == 1:
                lcid = next(iter(owners))
                owner_of[b['work_id']], via_of[b['work_id']] = lcid, 'lc_670'
                title_of[b['work_id']] = next(x for x in by_id[lcid]['sources'] if source_names_title([x], b['title']))
            elif owners:
                outcome = 'offline_670_ambiguous'  # several namesakes cite the same title; try the catalogue

        def confirmed_single(looked):
            """One authority so far, confirmed, and holding at least half the citations of the books
            looked at: then no more books are needed. The most-cited book is always looked at: a 670 hit
            on a lesser book is not enough on its own ('Smith, Jeremy' carried a namesake's Britain and
            Ireland beside the Soviet historian's books)."""
            ids = set(owner_of.values())
            if len(ids) != 1:
                return False
            lcid = next(iter(ids))
            mine = [b for b in person_books if owner_of.get(b['work_id']) == lcid]
            seen = sum(int(b['cited'] or 0) for b in person_books if b['work_id'] in looked or b['work_id'] in owner_of)
            ok = len(mine) >= 2 or any(source_names_title(by_id[lcid]['sources'], b['title']) for b in mine) or \
                (n['qid'] and qid_basis.get(gk) in TITLE_TIERS and
                 n['qid'] in {e.rsplit('/', 1)[-1] for e in by_id[lcid]['external'] if 'wikidata.org/entity/' in e})
            return ok and 2 * sum(int(b['cited'] or 0) for b in mine) >= seen

        # Catalogue: the most-cited books LC's notes do not settle, until one confirmed authority holds
        # the books looked at.
        looked, contested = set(), set()
        for b in person_books[:args.books]:
            if b is not person_books[0] and confirmed_single(looked):
                break
            if b['work_id'] in owner_of:
                continue
            looked.add(b['work_id'])
            q = query(b['title'], family)
            r = fetch.get(SRU5 + urllib.parse.quote(q))
            if r['status'] == 0:
                streak += 1
                if streak >= 3:
                    time.sleep(args.pause)
                outcome = outcome if owner_of else 'unanswered'
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
                match = [(h, [h['given']] + ([h['fuller']] if h['fuller'] else [])) for h in heads
                         if (compatible(person, h['given'], h['family'].translate(FOLD)) and given_agrees(pg, h['given']))
                         or (h['fuller'] and compatible(person, h['fuller'], h['family'].translate(FOLD)) and given_agrees(pg, h['fuller']))]
                match = closest_names(pg, match)       # a joint book: 'Jean' is Jean Comaroff, not John
                if len(match) > 1:
                    ids.add('ambiguous')
                elif match:
                    lcid, via = resolve(match[0][0], names)
                    # A heading matched only by its text can be an old form left on the bib record after
                    # LC created a separate authority (2026-10-31: 'Brooke, Stephen.' on Labour's war
                    # resolves to n84045320, the 1983 author; LC's 670 gives the book to no2025022468,
                    # 'Brooke, Stephen J.'). LC's own source note for this book wins.
                    owners = cited_in_670.get(b['work_id'], set())
                    if via != 'bib_$0' and len(owners) == 1 and lcid not in owners:
                        lcid, via = next(iter(owners)), 'lc_670_over_heading'
                    # The same for an undated record reached by the heading's text alone, when LC's notes
                    # give this name's books to one dated record of the same name ('Bender, Thomas'
                    # resolved to no2023034236, an illustrator; 'Bender, Thomas, 1944-' has His Unfinished
                    # city), born at least 20 years before the book. Not a fuller or different name: that
                    # moved Punishment and modern society to 'Garland, David S.' and Western aristocracies
                    # to a Royal Navy lieutenant (rerun4 review, 2026-10-31).
                    # (An undated record can be the right person: 'Garland, David' is the criminologist.)
                    elif via != 'bib_$0' and lcid and not label_dates(by_id[lcid]['label']) \
                            and len(all_670 := set().union(*cited_in_670.values())) == 1 and lcid not in all_670 \
                            and bare_name(by_id[next(iter(all_670))]['label']) == bare_name(by_id[lcid]['label']) \
                            and born_before(by_id[next(iter(all_670))], b['year']):
                        lcid, via = next(iter(all_670)), 'lc_670_over_heading'
                    if lcid and not by_id[lcid]['undifferentiated']:
                        ids.add(lcid)
                        hit = (lcid, via, facts['title'])
            if len(ids) == 1 and 'ambiguous' not in ids:
                owner_of[b['work_id']], via_of[b['work_id']], title_of[b['work_id']] = hit
            elif ids:
                contested.add(b['work_id'])     # LC names someone of this name, but not one person
            if not (len(ids) == 1 and 'ambiguous' not in ids) and not owner_of:
                outcome = 'records_disagree' if ids else \
                    'person_not_resolved' if seen_title else 'no_title_match' if recs else 'no_lc_record'

        # LC duplicates are one person; then one authority, a dominant one, or a pooled name.
        same = merge_duplicates(set(owner_of.values()), by_id)
        owner_of = {w: same[x] for w, x in owner_of.items()}
        winner = dominant(owner_of, person_books)
        mine = [b for b in person_books if winner and owner_of.get(b['work_id']) == winner]
        # The winner must hold at least half the citations of the books LC gives to someone of this
        # name: a namesake's minor book is not the name's owner when LC gives the most-cited books to
        # other people or to no single person. Books LC does not find at all do not count against it
        # (Le Goff's French titles are mostly not in the catalogue).
        seen = sum(int(b['cited'] or 0) for b in person_books if b['work_id'] in owner_of or b['work_id'] in contested)
        if winner and 2 * sum(int(b['cited'] or 0) for b in mine) < seen:
            winner, mine, outcome = None, [], 'minor_books_only'
        namesakes = ' '.join(f"{owner_of[b['work_id']]}:{b['work_id']}" for b in person_books
                             if b['work_id'] in owner_of and owner_of[b['work_id']] != winner) if winner else ''
        if winner:
            outcome = 'resolved'
        elif owner_of and outcome != 'minor_books_only':
            outcome = 'books_disagree'
        stats[outcome] += 1
        row = dict(namesake_works=namesakes, key=key[0] if len(key) == 1 else '', graph_key=gk, label=n['label'], cited=n['cited'],
                   dissertation_qid=n['qid'] or '', dissertation_qid_basis=qid_basis.get(gk, ''),
                   outcome=outcome, books_tried=tried)
        if outcome == 'books_disagree':
            row.update(via='lc_670_owners' if all(v == 'lc_670' for v in via_of.values()) else 'books',
                       evidence_works=' '.join(f"{owner_of[b['work_id']]}:{b['work_id']}" for b in person_books
                                               if b['work_id'] in owner_of))
        if outcome == 'resolved':
            a = by_id[winner]
            lf = life(a, label_dates(a['label']))
            lc_qids = {e.rsplit('/', 1)[-1] for e in a['external'] if 'wikidata.org/entity/' in e}
            wd = ('' if not lc_qids or not n['qid'] else 'agrees' if n['qid'] in lc_qids else 'disagrees')
            src = any(source_names_title(a['sources'], x['title']) for x in mine)
            confirmations = [c for c, ok in (('second_book', len(mine) >= 2), ('lc_670_names_title', src),
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
            first = mine[0]['work_id']
            row.update(lcnaf=winner, lc_label=a['label'], via=via_of[first], tier=tier,
                       confirmations=' '.join(confirmations), books_agreeing=len(mine),
                       evidence_works=' '.join(x['work_id'] for x in mine),
                       evidence_title=title_of[first],
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
