"""Sol's verdicts on much-cited works -> a crosswalk and a proposal, after checking every identifier (2026-11-03).

A round directory (data/identifiers/translation-check-2026-11-03b) holds groups.json (translation_check_groups.py)
and one g*/verdicts.json per group (BRIEF.md there), or round folders laid out the same way (pilot/, r1/, r2/: later folders' verdicts win). For each verdict:
- a graph `work` that is one of the item's candidate works, with relation translation, edition or same: the cited
  work maps to it (as in round one's apply-verdicts.py);
- otherwise the identifier Sol gave for the work is checked before anything is written:
  - `lccn`: the record is in LC's 2016 file (local index) and its title agrees with the original's or the cited
    title (key_lc_works.title_key: equal, or one the start of the other) and a 100/700 heading on it has a cited
    author's family name;
  - `isbn`: an ISBN LC's file holds is its record (checked as above); else Open Library's record of the ISBN, with
    the same title and author checks;
  - `doi`: Crossref's record, with the same title and author checks;
  - an `oclc` number alone, or a failed check, goes to review.json, not the proposal.
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

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
LC_INDEX = Path('/mnt/e/lc-bib-2016/index')
UA = 'historiography-research/1.0 (mailto:jic823@usask.ca)'


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip(' ,.')


def titles_agree(record_title, *wanted):
    r = title_key((record_title or '').split(':')[0]), title_key(record_title or '')
    for w in wanted:
        for k in (title_key((w or '').split(':')[0]), title_key(w or '')):
            if not k:
                continue
            for x in r:
                if x and (x == k or (len(min(x, k, key=len).split()) >= 2 and (x.startswith(k) or k.startswith(x)))):
                    return True
    return False


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

    def openlibrary(isbn):
        d = get_json(f'https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data')
        rec = (d or {}).get(f'ISBN:{isbn}')
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
        return dict(anchor=f'doi:{doi.lower()}', title=(m.get('title') or [''])[0], year=year,
                    families={fold(a.get('family', '')) for a in m.get('author', [])}, source='Crossref record')

    state = State.load(args.state)
    report, rows, review, clusters, claims = Counter(), [], [], [], []
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
        if rel == 'unclear':
            review.append(dict(v, why='unclear'))
            continue
        rec, tried = None, []
        if v.get('lccn'):
            tried.append('lccn')
            rec = lc_record(lccn=norm_lccn(v['lccn']))
        if not rec and isbn13(v.get('isbn')):
            tried.append('isbn')
            rec = lc_record(isbn=isbn13(v['isbn'])) or openlibrary(isbn13(v['isbn']))
        if not rec and v.get('doi'):
            tried.append('doi')
            rec = crossref(v['doi'].strip().removeprefix('https://doi.org/'))
        if not rec:
            review.append(dict(v, why=f'no identifier found ({", ".join(tried) or "none given"})'))
            continue
        fams = families(it)
        if not titles_agree(rec['title'], v.get('original_title'), it['cited_title']):
            review.append(dict(v, why=f'{rec["source"]} title differs: {rec["title"]}'))
            continue
        if not (fams & rec['families']):
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
            if holder and fold(p.split('|')[0]) in rec['families'] and c not in state.anchor:
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
