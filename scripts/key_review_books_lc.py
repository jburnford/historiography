"""Reviewed books no graph work holds -> LC's record of the book -> works, authors and `reviews` claims (2026-11-07).

The JSTOR full-text session read the book heading of each JSTOR review (author or editors, title, place, publisher,
year) and matched it to graph works (key_jstor_review_headings.py). The books that match no graph work are in
/mnt/e/jstor-fulltext-2026-11-06/review-books-unmatched.parquet (HANDOVER-review-books.md): about a third of the
lookup-ready rows are noisy (review prose or a signature read as a title, OCR damage), so a book is taken only when
LC's 2016 catalogue (offline index, scripts/lc_bib_index.py) has a record that agrees on all of:
- **title**: the record's main title (key_lc_works.title_key, before the first colon) equals the heading's main
  title of three words or more, or the whole titles are equal (two words or more);
- **person**: a 100/700 heading on the record has the family name of an author (or editor) in the review heading,
  with compatible given names (key_registry.names_compatible; namesake_check_groups.given_names_agree);
- **year**: the record's year is within one of the heading's imprint year (the reviewed edition);
- **one book**: every agreeing record has the same main title and lead family name (editions of one book).
Rows from initials-only signatures and rows without an author are skipped (lookup-ready: mean_conf >= 0.9).

Phase `match` writes the matches (matches.csv.gz, for review) and counts. Phase `propose` writes the proposal:
- a work for the book: an existing work when one of its LCCNs is keyed already, else a new work (label: LC title;
  anchors `lccn:`; member `lc-first-year:`; established), as key_lc_works does;
- people: each 100/700 heading with an author or editor role (key_lc_works.role_of) that resolves to one live,
  differentiated LC authority (lc_resolve_authorities.resolve; variant forms only when an earlier form of the
  authorised heading); the authority's key, else a new person key on `lcnaf:<id>` (established: a public PID),
  and an `lc-authored:` / `lc-edited:` claim per edition as key_lc_works makes them;
- a new author or editor whose name a live key without an LC authority already bears (an AHA dissertator, a review
  credit) is not minted blindly: when exactly one such key is an AHA dissertator whose dissertation is this book
  as published (key_aha.own_book's rule: three or more shared content words, 60% of the shorter, the
  dissertation's main title against the book's whole title, published no earlier than the year before the PhD),
  the authority joins that key; otherwise the person and their claims are held (held-people.json) for the merge
  routes, not minted beside a possible twin;
- the reviews: a review work on DOI where none exists (year, journal, signed reviewer's name as printed, as in
  key_jstor_review_headings.py) and a `reviews` claim `jstor-heading-lc:<doi>:<lccn>`.

    python3 scripts/key_review_books_lc.py --phase match --out data/identifiers/review-books-lc-2026-11-07
    python3 scripts/key_review_books_lc.py --phase propose --out data/identifiers/review-books-lc-2026-11-07
"""
import argparse
import csv
import gzip
import json
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise
from key_lc_works import former_heading, role_of, title_key
from key_registry import names_compatible
from key_review_reviewers import family as label_family
from lc_canon_people import content
from namesake_check_groups import given_words, names_agree_strict
from lc_resolve_authorities import load_names, norm, resolve
from namesake_check_groups import given_names_agree

FT = Path('/mnt/e/jstor-fulltext-2026-11-06')
UNMATCHED = FT / 'review-books-unmatched.parquet'
SIGNATURES = FT / 'review-signatures-rules.jsonl.gz'
RECORDS = Path('/mnt/e/JSTOR_history_citation_graph/records.sqlite')
LC_INDEX = Path('/mnt/e/lc-bib-2016/index')
LC_NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
AHA_RECORDS = Path(__file__).resolve().parent.parent / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl'


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip(' ,.')


def family_of(name):
    name = (name or '').strip()
    return fold(name.split(',')[0] if ',' in name else (name.split() or [''])[-1])


def keys_of(title):
    main, whole = title_key((title or '').split(':')[0]), title_key(title or '')
    return {k for k in (main if len(main.split()) >= 3 else None, whole if len(whole.split()) >= 2 else None) if k}


def match(args, db):
    rows = db.execute(f"""SELECT row_number() OVER () AS rid, title, authors, editors, year, reviews, untitled_reviews, iids
        FROM '{args.unmatched}' WHERE mean_conf >= 0.9 AND NOT initials_only AND len(authors) > 0 AND year IS NOT NULL""").fetchall()
    report = Counter(rows=len(rows))
    by_key = defaultdict(list)
    for rid, title, authors, editors, year, *_ in rows:
        for k in keys_of(title):
            by_key[k].append(rid)
    info = {r[0]: r for r in rows}
    db.execute('CREATE TABLE tk(k VARCHAR)')
    db.executemany('INSERT INTO tk VALUES (?)', [(k,) for k in {k.split()[0] for k in by_key}])
    recs = db.execute(f"""SELECT control, lccn, title, title_a, year FROM (
            SELECT trim(control) AS control, trim(lccn) AS lccn, title, title_a, try_cast(date1 AS INT) AS year,
                   list_filter(string_split(regexp_replace(strip_accents(lower(coalesce(title_a, ''))), '[^a-z0-9 ]+', ' ', 'g'), ' '),
                               x -> x <> '') AS ws FROM read_parquet('{LC_INDEX}/records-*.parquet'))
            WHERE len(ws) > 0 AND (ws[1] IN (SELECT k FROM tk) OR (len(ws) > 1 AND ws[2] IN (SELECT k FROM tk)))""").fetchall()
    hits = defaultdict(set)                       # control -> row ids (title and year agree)
    rec_info = {}
    for control, lccn, title, title_a, year in recs:
        ks = {title_key((title_a or '').split(':')[0]), title_key(title or '')}
        for k in ks:
            for rid in by_key.get(k, ()):
                if year and abs(year - info[rid][4]) <= 1:
                    hits[control].add(rid)
                    rec_info[control] = (lccn or control, (title or title_a or '').strip(' /:;.'), year,
                                         title_key((title_a or title or '').split(':')[0]))
    report['lc_records_title_year'] = len(hits)
    db.execute('CREATE TABLE hc(c VARCHAR)')
    db.executemany('INSERT INTO hc VALUES (?)', [(c,) for c in hits])
    heads = defaultdict(list)
    for control, pos, tag, heading, uri, family, given, relators in db.execute(f"""
            SELECT trim(control), pos, tag, heading, uri, family, given, relators FROM read_parquet('{LC_INDEX}/headings-*.parquet')
            WHERE trim(control) IN (SELECT c FROM hc) AND tag IN ('100', '700') ORDER BY 1, 2""").fetchall():
        heads[control].append((tag, heading, uri or '', family or '', given or '', relators or []))
    per_row = defaultdict(set)                    # row id -> controls agreeing on title, year and a person
    for control, rids in hits.items():
        for rid in rids:
            names = info[rid][2]
            if any(fold(h[3]) and any(fold(h[3]) == family_of(n) and names_compatible(f'{h[3]}, {h[4]}', n)
                                      and given_names_agree(f'{h[3]}, {h[4]}', n) for n in names) for h in heads[control]):
                per_row[rid].add(control)
    out = []
    for rid, controls in per_row.items():
        lead = {(rec_info[c][3], fold(heads[c][0][3]) if heads[c] else '') for c in controls}
        if len(lead) != 1:
            report['several_books'] += 1
            continue
        _, title, authors, editors, year, reviews, untitled, iids = info[rid]
        cs = sorted(controls, key=lambda c: (rec_info[c][2] or 9999, c))
        out.append(dict(rid=rid, heading_title=title, heading_authors=authors, heading_year=year, reviews=reviews,
                        untitled=untitled, iids=list(iids), controls=cs, lccns=[rec_info[c][0] for c in cs],
                        lc_title=rec_info[cs[0]][1], lc_year=rec_info[cs[0]][2]))
    report['rows_matched'] = len(out)
    report['reviews_reached'] = sum(len(o['iids']) for o in out)
    args.out.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.out / 'matches.jsonl.gz', 'wt', encoding='utf-8') as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + '\n')
    with gzip.open(args.out / 'matches.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['heading_title', 'heading_authors', 'heading_year', 'lc_title', 'lc_year', 'lccns', 'reviews'])
        for o in out:
            w.writerow([o['heading_title'], '; '.join(o['heading_authors']), o['heading_year'], o['lc_title'], o['lc_year'],
                        ' '.join(o['lccns']), o['reviews']])
    (args.out / 'report-match.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


def propose(args, db):
    state = State.load(args.state)
    # anchors of claims withdrawn by review (a wrong namesake, a festschrift honoree): a withdrawn key releases
    # its anchors, and a rerun must not mint the same claim again (2026-11-07)
    withdrawn = {a for k, v in state.keys.items() if v['type'] == 'claim' and v['status'] == 'withdrawn' for a in v['anchors']}
    matches = [json.loads(l) for l in gzip.open(args.out / 'matches.jsonl.gz', 'rt', encoding='utf-8')]
    report = Counter(matches=len(matches))
    controls = sorted({c for m in matches for c in m['controls']})
    db.execute('CREATE TABLE hc(c VARCHAR)')
    db.executemany('INSERT INTO hc VALUES (?)', [(c,) for c in controls])
    heads = defaultdict(list)
    for control, tag, heading, uri, relators in db.execute(f"""SELECT trim(control), tag, heading, uri, relators
            FROM read_parquet('{LC_INDEX}/headings-*.parquet') WHERE trim(control) IN (SELECT c FROM hc)
            AND tag IN ('100', '700') ORDER BY 1, pos""").fetchall():
        heads[control].append((tag, heading, uri or '', relators or []))
    db.execute('CREATE TABLE hh(h VARCHAR)')
    db.executemany('INSERT INTO hh VALUES (?)', [(norm(h[1]),) for hs in heads.values() for h in hs])
    lcids = {r[0] for r in db.execute(f"""SELECT lcid FROM read_parquet('{LC_NAMES}') WHERE label IN (SELECT h FROM hh)
                                         UNION SELECT lcid FROM (SELECT lcid, unnest(variants) AS v FROM read_parquet('{LC_NAMES}'))
                                         WHERE v IN (SELECT h FROM hh)""").fetchall()}
    lcids |= {h[2].rstrip('/').split('/')[-1] for hs in heads.values() for h in hs if h[2]}
    names = load_names(LC_NAMES, lcids)
    signers = {}
    want = {i for m in matches for i in m['iids']}
    with gzip.open(SIGNATURES, 'rt', encoding='utf-8') as f:
        for line in f:
            s = json.loads(line)
            if s['iid'] in want and s.get('creator') and (s.get('conf') or 0) >= 0.75:
                signers[s['iid']] = ' '.join(s['creator'].split())
    c = sqlite3.connect(f'file:{RECORDS}?mode=ro', uri=True)
    meta = {iid: (doi, y, j) for iid, doi, y, j in c.execute('SELECT item_id, doi, year, journal_title FROM records')
            if iid in want}
    ops, new_people, seen_claims = [], {}, set()
    minted = {}                                   # lccn anchor -> the anchor of the work minted for it in this run
    for m in matches:
        anchors = [f'lccn:{x}' for x in m['lccns']]
        owners = {k for a in anchors for k in state.lookup(a)} | {minted[a] for a in anchors if a in minted}
        if len(owners) > 1:
            report['lccns_on_several_works'] += 1
            continue
        if owners:
            o = next(iter(owners))
            work = o if o.startswith('lccn:') else next(a for a in anchors if a in state.anchor)
            new = [a for a in anchors if a not in state.anchor and a not in minted]
            if new and o.startswith('lccn:'):
                report['heading_rows_of_one_book'] += 1
            elif new:
                ops.append(dict(event='attach', key=o, anchors=new, aliases=[], members=[],
                                basis='further editions in the LC catalogue'))
            for a in new:
                minted[a] = work
            report['work_exists'] += 1
        else:
            for a in anchors:
                minted[a] = anchors[0]
            work = anchors[0]
            ops.append(dict(event='mint', key=f'new:w{len(ops)}', type='work', label=m['lc_title'][:250],
                            resolution='established', anchors=anchors, aliases=[],
                            members=[f'lc-first-year:{m["lc_year"]}'] if m['lc_year'] else [],
                            basis=f'LC catalogue (Books All 2016) record of a book reviewed in JSTOR ({len(m["iids"])} '
                                  f'review(s)): title, author and year agree with the printed review heading'))
            report['works_minted'] += 1
        # people, from every edition's 100/700 headings with a role
        roles = defaultdict(set)                  # (lcid, role) -> lccns
        for control, lccn in zip(m['controls'], m['lccns']):
            for tag, heading, uri, relators in heads[control]:
                role = role_of(tag, relators)
                if not role:
                    continue
                lcid, via = resolve(dict(heading=heading, uri=uri), names)
                if not lcid or names[0][lcid].get('undifferentiated') or names[0][lcid].get('deprecated'):
                    report['heading_unresolved'] += 1
                    continue
                if via == 'variant' and not former_heading(heading, names[0][lcid]['label']):
                    report['heading_variant_skipped'] += 1
                    continue
                roles[lcid, role].add(lccn)
        for (lcid, role), lccns in sorted(roles.items()):
            pa = f'lcnaf:{lcid}'
            claim_anchors = [f'lc-{role}:{x}:{lcid}' for x in sorted(lccns)]
            if any(a in withdrawn for a in claim_anchors):
                report[f'{role}_withdrawn_by_review'] += 1
                continue
            if pa not in state.anchor and lcid not in new_people:
                new_people[lcid] = len(ops)
                ops.append(dict(event='mint', key=f'new:p{len(ops)}', type='person', label=names[0][lcid]['label'],
                                resolution='established', anchors=[pa], aliases=[], members=[],
                                basis='LC name authority of the author or editor of a book reviewed in JSTOR'))
                report['people_minted'] += 1
            if any(a in state.anchor or a in seen_claims for a in claim_anchors):
                report[f'{role}_exists'] += 1
                continue
            seen_claims.update(claim_anchors)
            ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=claim_anchors, relation=dict(subject=pa, predicate=role, object=work)))
            report[f'{role}_claims'] += 1
        for iid in m['iids']:
            doi, y, j = meta.get(iid, (None, None, None))
            if not doi:
                report['review_without_doi'] += 1
                continue
            ra = f'doi:{doi.strip().lower()}'
            claim = f'jstor-heading-lc:{doi.strip().lower()}:{m["lccns"][0]}'
            if claim in state.anchor or claim in seen_claims:
                report['review_claim_exists'] += 1
                continue
            have = state.lookup(ra)
            if have and owners & set(have):
                report['review_doi_on_book'] += 1
                continue
            if not have and ra not in seen_claims:
                name = signers.get(iid)
                ops.append(dict(event='mint', key=f'new:r{len(ops)}', type='work', label=f'Review of {m["lc_title"][:300]}',
                                resolution='recorded', anchors=[ra], aliases=[],
                                members=[x for x in (f'year:{y}' if y else '', f'journal:{j}' if j else '',
                                                     f'reviewer-name:{name}' if name else '') if x],
                                basis=f'JSTOR book review ({j}, {y}) of a book in the LC catalogue'))
                seen_claims.add(ra)
                report['review_works_minted'] += 1
            seen_claims.add(claim)
            ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=[claim], relation=dict(subject=ra, predicate='reviews', object=work),
                            basis="the review's printed heading names this book; LC's record agrees on title, author "
                                  "and year"))
            report['reviews_claims'] += 1
    ops = twins(state, ops, report, args.out)
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    body = json.dumps(dict(basis='books reviewed in JSTOR, found in the LC catalogue by title, author and year',
                           decided_by='rule', ops=ops), ensure_ascii=False) + '\n'
    if len(body) > 50_000_000:
        with gzip.open(args.out / 'proposal.json.gz', 'wt', encoding='utf-8') as f:
            f.write(body)
    else:
        (args.out / 'proposal.json').write_text(body)
    (args.out / 'report-propose.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


def twins(state, ops, report, out):
    """New people whose name a live key without an LC authority bears: join by the dissertation-as-book rule, or hold."""
    by_family = defaultdict(list)
    for k, r in state.keys.items():
        if r['type'] == 'person' and r['status'] in ('active', 'provisional') \
                and not any(a.startswith('lcnaf:') for a in r['anchors']):
            g = given_words(r['label'] or '')
            if g and len(g[0]) > 1:
                by_family[label_family(r['label'])].append(k)
    aha = {}
    with open(AHA_RECORDS, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            aha[f"aha-phd:{r['id']}"] = (r.get('title') or '', r.get('year'))
    books = {o['anchors'][0]: (o['label'], int(o['members'][0].split(':')[1]) if o['members'] else None)
             for o in ops if o.get('type') == 'work' and o['anchors'][0].startswith('lccn:')}
    claims = defaultdict(list)                  # lcnaf anchor -> claim op indexes
    for i, o in enumerate(ops):
        if o.get('type') == 'claim' and o['relation']['subject'].startswith('lcnaf:'):
            claims[o['relation']['subject']].append(i)
    drop, held = set(), []
    for i, o in enumerate(ops):
        if o.get('type') != 'person':
            continue
        label, pa = o['label'], o['anchors'][0]
        twins_ = [k for k in by_family.get(label_family(label), []) if names_agree_strict(label, state.keys[k]['label'])]
        if not twins_:
            continue
        works = [books.get(ops[j]['relation']['object']) for j in claims[pa]]
        works = [w for w in works if w]
        joined = set()
        for k in twins_:
            for a in state.keys[k]['anchors']:
                if a in aha:
                    title, year = aha[a]
                    d = set(content(title))
                    for bt, by in works:
                        c = set(content(bt.replace(':', ' ')))
                        shared = len(c & d)
                        if len(d) >= 3 and shared >= 3 and shared >= 0.6 * min(len(c), len(d)) \
                                and (not by or not year or by >= year - 1):
                            joined.add(k)
        if len(joined) == 1 and len(twins_) == 1:
            k = joined.pop()
            ops[i] = dict(event='attach', key=k, anchors=[pa], aliases=[], members=[],
                          basis=f'LC authority of the author of a book reviewed in JSTOR, which is this AHA '
                                f"dissertation as published ({state.keys[k]['label']})")
            report['people_joined_to_aha_dissertator'] += 1
            report['people_minted'] -= 1
            continue
        drop.add(i)
        drop.update(claims[pa])
        held.append(dict(lcnaf=pa, label=label, twins={k: state.keys[k]['label'] for k in twins_},
                         dissertation_match=sorted(joined), works=[w[0] for w in works]))
        report['people_held_twin'] += 1
        report['people_minted'] -= 1
    report['claims_held_with_people'] = len(drop) - report['people_held_twin']
    (out / 'held-people.json').write_text(json.dumps(held, ensure_ascii=False, indent=1) + '\n')
    return [o for i, o in enumerate(ops) if i not in drop]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--phase', choices=('match', 'propose'), required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--unmatched', type=Path, default=UNMATCHED,
                    help='unmatched-books table (match phase); the Qwen re-read: review-books-qwen-unmatched.parquet '
                         '(scripts/jstor_qwen_unmatched_books.py)')
    args = ap.parse_args()
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    db.execute("SET memory_limit = '4GB'")
    (match if args.phase == 'match' else propose)(args, db)


if __name__ == '__main__':
    main()
