"""Sol's verdicts on much-cited works -> a crosswalk and a proposal, after checking every identifier (2026-11-03).

A round directory (data/identifiers/translation-check-2026-11-03b) holds groups.json (translation_check_groups.py)
and one g*/verdicts.json per group (BRIEF.md there), or round folders laid out the same way (pilot/, r1/, r2/: later folders' verdicts win). For each verdict:
- a graph `work` that is one of the item's candidate works, with relation translation, edition or same: the cited
  work maps to it (as in round one's apply-verdicts.py);
- otherwise the identifier Sol gave for the work is checked before anything is written:
  - `lccn`: the record is in LC's 2016 file (local index) and its title agrees with the original's or the cited
    title (key_lc_works.title_key: equal, or one the start of the other) and a 100/700 heading on it has a cited
    author's family name;
  - `isbn`: an ISBN LC's file holds is its record (checked as above); else LC's catalogue now (SRU, cached; also
    for an LCCN the 2016 file lacks), else Open Library's record, with the same title and author checks;
  - `doi`: Crossref's record, with the same title and author checks (a chapter record with no title: its book);
  - `url`: the publisher's or repository's page, by its citation_* metadata, with the same checks; a reviewed
    thesis, article or chapter whose only home is a file without metadata is kept at the lower tier;
  - a valid ISBN no catalogue here holds, for a book, with the page Sol confirmed it on (`source_url`): kept at the
    lower tier (`recorded`, the basis names the page);
  - `catalogued_as` (a second-pass answer: the family name LC files the author under) counts as a cited author;
  - `unresolvable` and `part` (no one work, or a chapter without an identifier of its own) are listed, not applied;
  - an `oclc` number alone, or a failed check, goes to review.json, not the proposal; a verdict marked
    `decided_by: review` (checked by hand: Hebe Mattos catalogued as Castro, a chapter DOI with no authors) skips the
    author check.
  A checked identifier that a key already holds maps the cited work to that key; otherwise the work is minted
  (`lccn:`, `isbn:<13 digits>` or `doi:` anchor, member `year:`), and each key holding a cited author's corpus id
  gets an `authored` claim (`verdict-authored:<anchor>:<corpus id>`, recorded).
Writes crosswalk.csv.gz (work_id, key or anchor) for export_citations, proposal.json, review.json, report.json.

    python3 scripts/apply_work_verdicts.py --dir data/identifiers/translation-check-2026-11-03b
"""
import argparse
import csv
import gzip
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_lc_works import title_key
from lc_authority_pilot import SRU, Fetcher, bib_headings
from lc_catalogue_harvest import record_facts

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
LC_INDEX = Path('/mnt/e/lc-bib-2016/index')
SRU_CACHE = Path('/mnt/e/lc-authorities/sru')
UA = 'historiography-research/1.0 (mailto:jic823@usask.ca)'


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip(' ,.')


def titles_agree(record_title, *wanted):
    dash = lambda t: re.sub('[\u2010-\u2015]', '-', t or '')
    record_title, wanted = dash(record_title), [dash(w) for w in wanted]
    r = title_key((record_title or '').split(':')[0]), title_key(record_title or '')
    for w in wanted:
        for k in (title_key((w or '').split(':')[0]), title_key(w or '')):
            if not k:
                continue
            for x in r:
                if x and (x == k or (len(min(x, k, key=len).split()) >= 2 and (x.startswith(k) or k.startswith(x)))):
                    return True
                if x and x.replace(' ', '') == k.replace(' ', ''):    # 'W.E.B. DuBois' and 'W. E. B. Du Bois'
                    return True
                a, b = set(x.split()), set(k.split())                # one word off in four: a catalogue's typo
                if x and min(len(a), len(b)) >= 4 and len(a & b) / len(a | b) >= 0.75:
                    return True
    return False


def same_family(a, b):
    """'garcia canclini' ~ 'canclini', "o'brien" ~ 'obrien', 'de ste croix' ~ 'ste croix'."""
    a, b = (re.sub(r'[^a-z ]', '', fold(x).replace('-', ' ')).split() for x in (a, b))
    return bool(a and b) and (''.join(a) == ''.join(b) or a[-1] == b[-1])


def isbn_valid(i13):
    return len(i13) == 13 and i13.isdigit() and sum((3 if k % 2 else 1) * int(c) for k, c in enumerate(i13)) % 10 == 0


def norm_lccn(s):
    s = re.sub(r'[^0-9a-z-]', '', (s or '').lower())
    if '-' in s:                                       # '76-7550' -> '76007550'
        a, b = s.split('-', 1)
        s = a + b.zfill(6)
    return s


def isbn13(s):
    d = re.sub(r'[^0-9X]', '', (s or '').upper())
    if len(d) == 10:
        core = '978' + d[:9]
        check = (10 - sum((3 if i % 2 else 1) * int(c) for i, c in enumerate(core)) % 10) % 10
        return core + str(check)
    return d if len(d) == 13 else ''


def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 + attempt * 3)
        except Exception:
            time.sleep(2 + attempt * 3)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    items, verdicts = {}, {}
    for sub in sorted(d for d in args.dir.iterdir() if d.is_dir() and (d / 'groups.json').exists()):  # pilot, r1, r2 ...
        if (sub / 'groups.json').exists():
            items.update({i['id']: i for g in json.loads((sub / 'groups.json').read_text()) for i in g['items']})
            verdicts.update({v['id']: v for f in sorted(sub.glob('g*/verdicts.json')) for v in json.loads(f.read_text())})
    verdicts = list(verdicts.values())
    db = duckdb.connect()
    db.execute("SET memory_limit = '3GB'")
    people = defaultdict(set)                          # corpus work -> corpus person ids
    db.execute('CREATE TABLE want(w VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(w,) for w in items])
    for p, w in db.execute(f"SELECT person_key, work_id FROM read_csv('{CORPUS}/authored.csv.gz') WHERE work_id IN (SELECT w FROM want)").fetchall():
        people[w].add(p)

    def families(item):
        fams = {fold(p.split('|')[0]) for p in people[item['id']]}
        fams |= {fold(re.split(r'[;,]', item.get('cited_authors') or '')[0])}
        for c in item['candidates']:
            n = c['name']
            fams.add(fold(n.split(',')[0]) if ',' in n else fold(n.split()[-1]) if n.split() else '')
        return {f for f in fams if len(f) > 1}

    def lc_record(lccn=None, isbn=None):
        where = f"trim(control) = '{lccn}'" if lccn else f"list_contains(isbns, '{isbn}')"
        r = db.execute(f"SELECT trim(control), title, date1 FROM read_parquet('{LC_INDEX}/records-*.parquet', union_by_name=true) WHERE {where} LIMIT 1").fetchone()
        if not r:
            return None
        fams = {fold(f) for (f,) in db.execute(f"SELECT family FROM read_parquet('{LC_INDEX}/headings-*.parquet') WHERE trim(control) = '{r[0]}'").fetchall()}
        return dict(anchor=f'lccn:{r[0]}', title=r[1], year=(r[2] or '')[:4], families=fams, source='LC 2016 record')

    fetch = Fetcher(SRU_CACHE, 3.0)

    def lc_live(lccn=None, isbn=None):
        """LC's catalogue now (SRU), for books after or outside the 2016 file (2026-11-03: Open Library refused
        connections from here)."""
        r = fetch.get(SRU + urllib.parse.quote(f'bath.lccn={lccn}' if lccn else f'bath.isbn={isbn}'))
        if not r.get('status') or r['status'] != 200:
            return None
        heads, n = bib_headings(r['body'])
        facts = record_facts(r['body']) if n else {}
        if not facts.get('lccn') and not facts.get('control'):
            return None
        return dict(anchor=f'lccn:{facts.get("lccn") or facts["control"]}', title=facts.get('title', ''), year='',
                    families={fold(h['family']) for h in heads}, source='LC catalogue record')

    # Open Library asks for no bulk single-book requests (openlibrary.org/developers/api; identified clients 3/s):
    # every verdict's ISBN is fetched up front, fifty to a request, one request a second. One request per ISBN
    # with a single startup probe got the 2026-11-04 10:45 run shut out for the whole run.
    ol, ol_failed = {}, 0
    want = sorted({i for v in verdicts if (i := isbn13(v.get('isbn')))})
    for n in range(0, len(want), 50):
        part = want[n:n + 50]
        d = get_json('https://openlibrary.org/api/books?format=json&jscmd=data&bibkeys=' + ','.join(f'ISBN:{i}' for i in part))
        if d is None:
            ol_failed += 1
        ol.update({k.removeprefix('ISBN:'): r for k, r in (d or {}).items()})
        time.sleep(1)

    def openlibrary(isbn):
        rec = ol.get(isbn)
        if not rec:
            return None
        fams = {fold(a['name'].split()[-1]) for a in rec.get('authors', []) if a.get('name')}
        year = (re.search(r'\d{4}', rec.get('publish_date') or '') or [''])[0]
        return dict(anchor=f'isbn:{isbn}', title=rec.get('title', ''), year=year, families=fams, source='Open Library record')

    def crossref(doi):
        d = get_json(f'https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto=jic823@usask.ca')
        m = (d or {}).get('message')
        if not m:
            return None
        year = str(((m.get('issued') or {}).get('date-parts') or [[None]])[0][0] or '')
        return dict(anchor=f'doi:{doi.lower()}', title=(m.get('title') or [''])[0], year=year, container=(m.get('container-title') or [''])[0],
                    families={fold(a.get('family', '')) for a in m.get('author', [])}, source='Crossref record')

    def page(url):
        """A publisher's or repository's article page: its citation_* metadata (Highwire tags), else nothing."""
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                html = r.read(400000).decode('utf-8', 'replace')
        except Exception:
            return None
        meta = lambda n: re.findall(rf'name="{n}" content="([^"]*)"', html)
        if not meta('citation_title'):
            return None
        year = (re.search(r'\d{4}', (meta('citation_date') or meta('citation_publication_date') or [''])[0]) or [''])[0]
        return dict(anchor=f'url:{url}', title=meta('citation_title')[0], year=year, source='publisher page',
                    families={fold(a.split(',')[0] if ',' in a else (a.split() or [''])[-1]) for a in meta('citation_author')})

    state = State.load(args.state)
    report, rows, review, clusters, claims = Counter(), [], [], [], []
    report.update(openlibrary_records=len(ol), openlibrary_batches_failed=ol_failed)
    for v in verdicts:
        it = items.get(v.get('id'))
        if not it:
            report['unknown_item'] += 1
            continue
        rel = v.get('relation')
        report[f'relation:{rel}'] += 1
        ok = {w['work'] for c in it['candidates'] for w in c['works']}
        if v.get('work') and rel in ('translation', 'edition', 'same'):
            if v['work'] in ok:
                rows.append((it['id'], v['work']))
                report['candidate_work'] += 1
            else:
                review.append(dict(v, why='work is not one of the candidates'))
            continue
        if rel in ('unclear', 'unresolvable', 'part'):        # 'part': a chapter whose book is named, no identifier of its own
            review.append(dict(v, why=rel))
            continue
        rec, tried = None, []
        if v.get('lccn'):
            tried.append('lccn')
            rec = lc_record(lccn=norm_lccn(v['lccn'])) or lc_live(lccn=norm_lccn(v['lccn']))
        if not rec and isbn13(v.get('isbn')):
            tried.append('isbn')
            i13 = isbn13(v['isbn'])
            rec = lc_record(isbn=i13) or lc_live(isbn=i13) or openlibrary(i13)
        if not rec and v.get('doi'):
            tried.append('doi')
            rec = crossref(v['doi'].strip().removeprefix('https://doi.org/'))
        if not rec and v.get('url'):
            tried.append('url')
            rec = page(v['url'])
            if not rec and v.get('kind') in ('thesis', 'article', 'chapter') and v.get('decided_by') == 'review':
                # a reviewed item whose only home is a file without metadata (Monteiro's livre-docência PDF)
                report['reviewed_url'] += 1
                rows.append((it['id'], f'url:{v["url"]}'))
                if f'url:{v["url"]}' not in state.anchor:
                    clusters.append(dict(type='work', label=(v.get('original_title') or it['cited_title'])[:250], anchors={f'url:{v["url"]}'},
                                         members={f'year:{v["original_year"]}'} if v.get('original_year') else set(), aliases=set(),
                                         resolution='recorded', basis=f'reviewed: {v.get("note", "")}'))
                continue
        if not rec and isbn_valid(isbn13(v.get('isbn'))) and (v.get('source_url') or '').startswith('http') \
                and rel != 'unclear' and v.get('kind') in ('book', 'book_selection'):
            # no catalogue here holds it (Brazilian, Portuguese and French editions LC never bought): Sol's ISBN, with
            # the catalogue or publisher page Sol confirmed it on, at the lower tier
            i13 = isbn13(v['isbn'])
            report['sol_sourced_isbn'] += 1
            rows.append((it['id'], f'isbn:{i13}'))
            if f'isbn:{i13}' not in state.anchor:
                clusters.append(dict(type='work', label=(v.get('original_title') or it['cited_title'])[:250], anchors={f'isbn:{i13}'},
                                     members={f'year:{v["original_year"]}'} if v.get('original_year') else set(), aliases=set(),
                                     resolution='recorded', basis=f'Sol named it the work cited as {it["cited_title"]} ({it["id"]}) and '
                                                                  f'confirmed the ISBN at {v["source_url"]}; no catalogue checked here holds it'))
            for p in sorted(people[it['id']]):
                c = f'verdict-authored:isbn:{i13}:{p}'
                if state.anchor.get(f'diss-person:{p}') and c not in state.anchor:
                    claims.append(dict(anchor=c, subject=f'diss-person:{p}', object=f'isbn:{i13}'))
            continue
        if not rec:
            review.append(dict(v, why=f'no identifier found ({", ".join(tried) or "none given"})'))
            continue
        fams = families(it) | ({fold(v['catalogued_as'].split(',')[0])} if v.get('catalogued_as') else set())
        if not rec['title'] and rec['source'] == 'Crossref record' and (
                any(same_family(f, g) for f in fams for g in rec['families'])
                or (v.get('container') and titles_agree(rec.get('container', ''), v['container']))):
            pass                                       # a chapter DOI whose record carries no title: the authors decide
        elif not titles_agree(rec['title'], v.get('original_title'), it['cited_title']):
            review.append(dict(v, why=f'{rec["source"]} title differs: {rec["title"]}'))
            continue
        if not any(same_family(f, g) for f in fams for g in rec['families']) and v.get('decided_by') != 'review':
            review.append(dict(v, why=f'{rec["source"]} has none of the cited authors {sorted(fams)}: {sorted(rec["families"])[:5]}'))
            continue
        report[f'checked:{rec["source"]}'] += 1
        rows.append((it['id'], rec['anchor']))
        if rec['anchor'] in state.anchor:
            report['already_keyed'] += 1
        else:
            clusters.append(dict(type='work', label=(rec['title'] or v.get('original_title') or '')[:250], anchors={rec['anchor']},
                                 members={f'year:{rec["year"]}'} if rec['year'] else set(), aliases=set(), resolution='established',
                                 basis=f'Sol named it the original of the cited {it["cited_title"]} ({it["id"]}); {rec["source"]} agrees on title and author'))
        for p in sorted(people[it['id']]):
            holder = state.anchor.get(f'diss-person:{p}')
            c = f'verdict-authored:{rec["anchor"]}:{p}'
            if holder and any(same_family(p.split('|')[0], g) for g in rec['families']) and c not in state.anchor:
                claims.append(dict(anchor=c, subject=f'diss-person:{p}', object=rec['anchor']))
    seen = set()                                       # two cited forms of one work: one cluster
    clusters = [c for c in clusters if not (min(c['anchors']) in seen or seen.add(min(c['anchors'])))]
    ops, assign, held = plan(state, clusters)
    for i, c in enumerate({c['anchor']: c for c in claims}.values()):
        ops.append(dict(event='mint', key=f'new:claim-{i}', type='claim', label='', resolution='recorded', anchors=[c['anchor']],
                        relation=dict(subject=c['subject'], predicate='authored', object=c['object']),
                        basis='author of the cited work, as the corpus lists it and the checked record agrees'))
    materialise(state, dict(basis='work verdicts', ops=ops), 'dry-run', 'dry-run')
    (args.dir / 'proposal.json').write_text(json.dumps(dict(
        basis="much-cited works identified by Sol, each identifier checked against LC, Open Library or Crossref",
        decided_by='rule', ops=ops), ensure_ascii=False) + '\n')
    with gzip.open(args.dir / 'crosswalk.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['work_id', 'key'])
        wr.writerows(rows)
    (args.dir / 'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=1) + '\n')
    summary = dict(**dict(sorted(report.items())), mapped=len(rows), review=len(review),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.dir / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
