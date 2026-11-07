"""AHA dissertation authors -> LC name authorities through the thesis notes of their books (2026-11-07). Writes a proposal.

key_aha_lc_books.py joins an AHA author to the LC authority of a book whose title is the dissertation's. A
retitled book escapes it (John Saltmarsh's 'The Terrible Freedom: An Intellectual Biography of Scott Nearing',
Boston University 1989, became 'Scott Nearing: An Intellectual Biography', 1991). LC's record for such a book
usually says what it is: 'Revision of the author's thesis (Ph. D.)--Boston University, 1989.' (MARC 502/500,
extracted by scripts/lc_thesis_notes.py). Identity by works: the book is the dissertation as published.

1. **Match**: a record with a thesis note (not a master's or bachelor's degree) and a 100 author heading whose
   name agrees with the dissertator (family equal, `compatible` + `given_agrees`), where
   - the note's institution agrees with the AHA department's: every distinctive word of the AHA institution
     (before the first comma: 'Ohio State Univ.' -> ohio, state) is in the note's institution, and every
     distinctive word of the note's institution is in the AHA department (campus included: 'University of
     Wisconsin--Madison' against 'Univ. of Wisconsin, Madison, Dept. of History'); and
   - the note's year is within one of the PhD year, or, when the note gives none, the book appeared from the
     year before the PhD to twenty years after.
   An AHA record matching books under several headings is queued, as is a heading matched by several records.
2. **Heading -> authority** as key_aha_lc_books (the record's $0, else one live authorised heading, or one
   since closed; no variants; undifferentiated authorities skipped). An undated heading on an older record
   ('Saltmarsh, John A.') that no authorised form matches resolves to LC's only live authority of that name
   once dated ('Saltmarsh, John A., 1957-'); an authority whose birth year puts the PhD before 20 or after 65
   is queued. Headings left unresolved are listed in unresolved-headings.json.
3. **Clusters** `aha-phd:<record>` + `lcnaf:<id>` through `plan` with key_lc_books' merge rule (one LC
   authority, all names compatible) behind the merge guard. Only author keys without an LC authority are read.

    python3 scripts/key_aha_lc_theses.py --index /mnt/e/lc-bib-2016/index \\
        --names /mnt/e/lc-authorities/personal-names.parquet --out data/identifiers/aha-lc-theses-2026-11-07
"""
import argparse
import csv
import gzip
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise, plan
from identity_routes import compatible
from key_aha import AHA
from key_aha_lc_books import matched_lcids
from key_lc_books import label_of, merge_rule
from key_registry import names_compatible
from lc_canon_people import as_credit, given_agrees
from lc_resolve_authorities import load_names, norm, resolve
from merge_guard import guarded

GENERIC = {'university', 'univ', 'u', 'of', 'the', 'college', 'at', 'and', 'in', 'dept', 'department', 'history',
           'historical', 'studies', 'program', 'graduate', 'school', 'faculty', 'committee', 'on', 'for', 'de', 'la',
           'universite', 'universitat', 'universidad', 'divinity', 'arts', 'sciences', 'science', 'centre', 'center',
           'institute', 'phd', 'ph', 'd', 'thesis', 'dissertation', 'doctoral', 'degree', 'author', 's', 'its', 'a',
           'an', 'as', 'originally', 'presented', 'revision', 'revised', 'version', 'issued', 'also', 'part',
           'abridged', 'based', 'author', 'under', 'title', 'entitled', 'with', 'is', 'was', 'this', 'work', 'book',
           'american', 'civilization', 'humanities', 'social', 'politics', 'political', 'economics', 'philosophy',
           'english', 'religion', 'religious', 'interdisciplinary', 'european', 'germanic', 'languages', 'joint'}
NOT_PHD = re.compile(r'\b(M\.?\s?A|M\.?\s?S|M\.?\s?Litt|M\.?\s?Phil|B\.?\s?A|Master|Masters|honou?rs|B\.?\s?Litt|Diploma|M\.?\s?Ed|LL\.?\s?M)\b\.?', re.I)
YEAR = re.compile(r'\b(1[89]\d\d|20[01]\d)\b')
ABBR = {'calif': 'california', 'penn': 'pennsylvania', 'wash': 'washington', 'mich': 'michigan', 'wis': 'wisconsin',
        'tex': 'texas', 'ill': 'illinois', 'minn': 'minnesota', 'mass': 'massachusetts', 'n': 'n', 'st': 'state'}


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


def toks(s):
    return {ABBR.get(w, w) for w in re.findall(r'[a-z]+', fold(s))} - GENERIC


def note_institution(note):
    """The institution as the note prints it: after '--' ('Thesis (Ph. D.)--Columbia University, 1975.') or after
    'thesis,' ('Revision of the author's thesis, University of London, 1966.'), up to the year."""
    t = re.sub(r'\([^()]*\)', ' ', note)
    if '--' in t:
        t = t.split('--', 1)[1]
    else:
        m = re.search(r'(thesis|dissertation|diss\.)\s*[,—–-]?\s*', t, re.I)
        if not m:
            return ''
        t = t[m.end():]
    t = YEAR.split(t)[0]
    return t.strip(' .,;:')


def inst_agrees(note_inst, department):
    core = toks(department.split(',')[0])
    full = toks(re.split(r',\s*(Dept|Department|Program|Committee|School|Graduate|Faculty)\b', department)[0])
    n = toks(note_inst)
    return bool(core) and bool(n) and core <= n and n <= full


def aha_authors(state):
    """AHA record id -> (key, record) for author keys without an LC authority."""
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = {r['id']: r for r in csv.DictReader(f)}
    out = {}
    for k, v in state.keys.items():
        if v['type'] != 'person' or v['status'] not in ('active', 'provisional') \
                or any(a.startswith('lcnaf:') for a in v['anchors']):
            continue
        for a in v['anchors']:
            r = records.get(a[len('aha-phd:'):]) if a.startswith('aha-phd:') else None
            if r and r['dissertator'] and ', ' in r['dissertator'] and (r['year'] or '').isdigit() and r['department']:
                out[r['id']] = (k, r)
    return out


def thesis_books(index, notes):
    """family (folded) -> [(heading, family, given, uri, control, title, date1, note)] for 100 headings on records
    with a doctoral thesis note."""
    db = duckdb.connect()
    db.execute('SET memory_limit = "6GB"')
    rows = db.execute(f"""
        WITH n AS (SELECT control, string_agg(note, ' | ') AS note FROM read_parquet('{notes}') GROUP BY control)
        SELECT h.heading, h.family, h.given, h.uri, h.control, r.title, r.date1, n.note
        FROM n JOIN read_parquet('{index}/headings-*.parquet') h USING (control)
        JOIN read_parquet('{index}/records-*.parquet') r USING (control)
        WHERE h.tag = '100'""").fetchall()
    out = defaultdict(list)
    for row in rows:
        out[fold(row[1])].append(row)
    return out, len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--index', type=Path, required=True)
    ap.add_argument('--notes', type=Path, default=None, help='default: <index>/theses-notes.parquet')
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    authors = aha_authors(state)
    books, n_rows = thesis_books(args.index, args.notes or args.index / 'theses-notes.parquet')
    report, queue = Counter(aha_authors=len(authors), thesis_book_headings=n_rows), []
    matched, evidence = defaultdict(set), {}
    for rid, (k, r) in authors.items():
        family, _, given = r['dissertator'].partition(', ')
        year = int(r['year'])
        for heading, fam, giv, uri, control, title, date1, note in books.get(fold(family), ()):
            if not (compatible(as_credit(r['dissertator']), giv, fam) and given_agrees(given, giv)):
                continue
            for one in note.split(' | '):
                if NOT_PHD.search(re.sub(r'^.*?(thesis|dissertation|diss\.)', '', one, flags=re.I)[:40]):
                    continue
                inst = note_institution(one)
                if not inst_agrees(inst, r['department']):
                    continue
                ys = [int(y) for y in YEAR.findall(one)]
                if ys:
                    if abs(ys[-1] - year) > 1:
                        continue
                elif not ((date1 or '').isdigit() and year - 1 <= int(date1) <= year + 20):
                    continue
                h = norm(heading)
                matched[rid].add(h)
                evidence[rid, h] = (title, date1, one, uri or '')
                report['note_with_year' if ys else 'note_without_year_book_in_window'] += 1
                break
    report['records_matching_a_thesis_book'] = len(matched)
    heads = {h for hs in matched.values() for h in hs}
    uris = {}
    for (rid, h), ev in evidence.items():
        uris[h] = uris.get(h) or ev[3]
    names = load_names(args.names, matched_lcids(args.names, heads, uris))
    by_id = names[0]
    undated = defaultdict(set)          # 'Saltmarsh, John A.' -> authorities 'Saltmarsh, John A., 1957-'
    for i, v in by_id.items():
        if not v['deprecated'] and not v.get('undifferentiated'):
            undated[norm(label_of(v['label']))].add(i)
    lc_of, unresolved = {}, []
    for h in heads:
        lcid, via = resolve(dict(heading=h, uri=uris.get(h, '')), names)
        if via == 'variant':
            lcid = ''
        if via == 'not_in_dump' and h == norm(label_of(h)) and len(undated.get(h, ())) == 1:
            # an undated heading on an older record; LC's one authority of that name added the dates later
            lcid, via = next(iter(undated[h])), 'undated_heading_one_authority'
        if not lcid:
            unresolved.append(dict(heading=h, via=via))
        if lcid and not by_id[lcid].get('undifferentiated'):
            lc_of[h] = (lcid, by_id[lcid]['label'])
        report[f'heading_{via}'] += 1
    names = None
    rejected = {(m.split(':', 1)[1], k) for k, ms in state.members.items() for m in ms if m.startswith('lcnaf-rejected:')}
    rejected |= {(m.split(':', 2)[2], k) for k, ms in state.members.items() for m in ms if m.startswith('rejected:lcnaf:')}
    by_lc, pairs = defaultdict(set), {}
    for rid, hs in matched.items():
        lcs = {lc_of[h] for h in hs if h in lc_of}
        if len(lcs) > 1:
            queue.append(dict(kind='record_reaches_several_lcnaf', record=rid, key=authors[rid][0],
                              label=state.keys[authors[rid][0]]['label'], lcnaf=sorted(x[0] for x in lcs)))
            report['record_reaches_several_lcnaf'] += 1
        elif lcs:
            pairs[rid] = next(iter(lcs))
            by_lc[pairs[rid][0]].add(authors[rid][0])
    clusters, rows = [], []
    for rid, (lc, lc_label) in sorted(pairs.items(), key=lambda x: int(x[0])):
        k = authors[rid][0]
        label = label_of(lc_label)
        if len(by_lc[lc]) > 1:
            queue.append(dict(kind='lcnaf_reached_from_several_aha_keys', lcnaf=lc, label=label,
                              keys=sorted(by_lc[lc]), labels=[state.keys[x]['label'] for x in sorted(by_lc[lc])]))
            report['lcnaf_reached_from_several_aha_keys'] += 1
            continue
        owner = state.anchor.get(f'lcnaf:{lc}')
        problem = None
        birth = (by_id[lc].get('birth') or '')[:4]
        if birth.isdigit() and not 20 <= int(authors[rid][1]['year']) - int(birth) <= 65:
            problem = 'lc_birth_disagrees_with_phd_year'
        elif (lc, k) in rejected or (owner and (lc, owner) in rejected):
            problem = 'key_rejected_this_lcnaf'
        elif not names_compatible(label, state.keys[k]['label']) or (owner and not names_compatible(label, state.keys[owner]['label'])):
            problem = 'lcnaf_name_differs_from_key'
        if problem:
            queue.append(dict(kind=problem, record=rid, key=k, owner=owner, lcnaf=lc, label=label,
                              key_label=state.keys[k]['label']))
            report[problem] += 1
            continue
        report['joined_to_existing_lc_key' if owner else 'lcnaf_new_to_log'] += 1
        h = next(h for h in matched[rid] if lc_of.get(h, (None,))[0] == lc)
        title, date1, note, _ = evidence[rid, h]
        r = authors[rid][1]
        rows.append(dict(record=rid, key=k, dissertator=r['dissertator'], department=r['department'], aha_year=r['year'],
                         aha_title=r['title'], lcnaf=lc, lc_label=lc_label, owner=owner or '', book=title,
                         book_year=date1, note=note))
        clusters.append(dict(type='person', label=label, anchors={f'aha-phd:{rid}', f'lcnaf:{lc}'}, members=set(),
                             aliases=set(), resolution='established',
                             basis=f"AHA {rid} ({r['department'].split(',')[0]}, {r['year']}) is the thesis of a book LC "
                                   f"catalogues under {lc}: '{note[:120]}' (Books All 2016)"))
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    materialise(state, dict(basis='aha lc theses', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json.gz').write_bytes(gzip.compress(json.dumps(dict(
        basis='AHA dissertations published as books whose LC records carry the thesis note (MDSConnect Books All 2016)',
        decided_by='build', ops=ops), ensure_ascii=False).encode() + b'\n'))
    with (args.out / 'matches.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['record'])
        w.writeheader()
        w.writerows(rows)
    (args.out / 'unresolved-headings.json').write_text(json.dumps(unresolved, ensure_ascii=False, indent=0) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(**dict(sorted(report.items())), clusters=len(clusters), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held), review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
