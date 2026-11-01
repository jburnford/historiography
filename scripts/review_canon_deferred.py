"""Canon-map people deferred for review -> joins and separations through their works (LC). Writes a proposal; never mints.

scripts/key_canon_map.py deferred 208 canon people whose name matches an atlas person but whom no
bridge or QID joined (`merge-review-queue.json`). The user's rule (2026-10-31): resolve historians
through their works; topic and venue never merge or split. Here the works are the books the theses cite
under the canon name, resolved to an LC name authority by scripts/lc_canon_people.py:

- **join**: the canon name's books resolve (tier `exact`) to the LC authority that already anchors the
  atlas person, or to an authority whose LC Wikidata link is the atlas person's reviewed QID
  (data/people-wikidata.json, accepted). The canon person's
  `diss-person:` anchor is attached to the atlas key.
- **separate**: the canon name's books resolve (`exact`) to a different LC authority from the one the
  atlas person's own works gave (both routes exact). The canon person is minted as a new key; its LC
  anchor comes later through scripts/key_lc_canon.py.
- **join by a shared work**: one of the works the theses cite under the canon name (two or more content
  words in the main title) appears in the atlas beside the atlas person's name (a source citation or an
  entry's works). When the canon books resolve to an LC authority, the shared work must be that
  authority's too (its 670s or the catalogue), so a key that pools namesakes is not joined. Never for
  initials-only names or names LC splits among several people (`books_disagree`).
- **open**: anything else (no exact authority, a pooled name, an atlas person with no LC anchor or QID
  to compare). Stays deferred.

    python3 scripts/review_canon_deferred.py --run data/field-research/lc-authorities-2026-10-30/canon-rerun4-2026-10-31 \\
        --names /mnt/e/lc-authorities/personal-names.parquet --cache /mnt/e/lc-authorities/sru-canon \\
        --out data/identifiers/canon-deferred-2026-10-31
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
import urllib.parse

from key_canon_map import D
from lc_authority_pilot import Fetcher
from lc_canon_people import (FOLD, SRU5, STOP, as_credit, closest_names, given_agrees, initials_only, main_title,
                             query, records, source_names_title, titles_agree, words)
from identity_routes import compatible
from lc_resolve_authorities import load_names, resolve

QUEUE = ROOT / 'data/identifiers/canon-map-2026-10-30/merge-review-queue.json'
SHEET = ROOT / 'data/people-wikidata.json'


def atlas_snippets(atlas):
    """person_id -> text that follows the person's name in source citations and entry works."""
    texts = [s.get('citation') or s.get('title') or '' for s in atlas['sources']] + \
        [n.get('representative_figures_and_works') or '' for n in atlas['nodes']]
    out = defaultdict(list)
    for p in atlas['people']:
        label = p['label']
        for t in texts:
            for m in re.finditer(re.escape(label), t):
                out[p['id']].append(t[m.end():m.end() + 300].split(';')[0])
    return out


def cited_works(keys, per_person=40):
    db = duckdb.connect()
    db.execute("CREATE TABLE k(person_key VARCHAR)")
    db.executemany("INSERT INTO k VALUES (?)", [(k,) for k in keys])
    rows = db.execute(f"""
        WITH a AS (SELECT person_key, work_id FROM read_csv('{D / 'authored.csv.gz'}', all_varchar=true)
                   WHERE person_key IN (SELECT person_key FROM k))
        SELECT a.person_key, w.title, CAST(w.cited_by_dissertations AS INTEGER) AS n
        FROM a JOIN read_csv('{D / 'works.csv'}', all_varchar=true, max_line_size=10000000) w USING (work_id)
        WHERE w.title IS NOT NULL ORDER BY a.person_key, n DESC, w.work_id""").fetchall()
    out = defaultdict(list)
    for key, title, n in rows:
        if len(out[key]) < per_person:
            out[key].append(title)
    return out


def shared_works(titles, snippets):
    """Cited titles whose main title appears in a snippet, most-cited first."""
    hay = [' '.join(words(s)) for s in snippets]
    out = []
    for t in titles:
        w = words(main_title(t))
        if len([x for x in w if x not in STOP]) < 2 or len(w) < 2:
            continue
        needle = ' '.join(w)
        if any(re.search(rf'(^| ){re.escape(needle)}( |$)', h) for h in hay) and main_title(t) not in out:
            out.append(main_title(t))
    return out


def title_authority(title, label, fetch, names):
    """The LC authority the catalogue gives for this title under this name ('' if none or several)."""
    family, person, pg = label.partition(', ')[0], as_credit(label.translate(FOLD)), label.partition(', ')[2]
    r = fetch.get(SRU5 + urllib.parse.quote(query(title, family)))
    if r['status'] != 200:
        return ''
    ids = set()
    for heads, facts in records(r['body']):
        if not titles_agree(title, facts.get('title', '')):
            continue
        match = [(h, [h['given']] + ([h['fuller']] if h['fuller'] else [])) for h in heads
                 if (compatible(person, h['given'], h['family'].translate(FOLD)) and given_agrees(pg, h['given']))
                 or (h['fuller'] and compatible(person, h['fuller'], h['family'].translate(FOLD)) and given_agrees(pg, h['fuller']))]
        match = closest_names(pg, match)
        if len(match) == 1:
            ids.add(resolve(match[0][0], names)[0] or '?')
        elif match:
            ids.add('?')
    return next(iter(ids)) if len(ids) == 1 and '?' not in ids else ''


def decide(item, row, state, sheet_qid, shared=(), confirm=None):
    """(decision, reason, atlas key) for one queue item and its canon LC row (or None)."""
    keys = state.lookup(f'atlas:person:{item["atlas_person"]}')
    if len(keys) != 1:
        return 'open', 'atlas person has no single key', ''
    k = keys[0]
    anchors = state.keys[k]['anchors']
    atlas_lc = {a[6:] for a in anchors if a.startswith('lcnaf:')}
    atlas_qid = {a[3:] for a in anchors if a.startswith('wd:')} | ({sheet_qid[item['atlas_person']]}
                                                                   if item['atlas_person'] in sheet_qid else set())
    cites = 'the atlas cites {} for "{}", a work the theses cite under this name'.format
    if shared and ', ' in item['name'] and initials_only(item['name']):
        return 'open', f'{cites(item["atlas_person"], shared[0])}, but an initials-only name pools people', k
    if shared and row and row.get('outcome') == 'books_disagree':
        return 'open', f'{cites(item["atlas_person"], shared[0])}, but LC splits this name\'s books among several people', k
    if not row or row.get('outcome') != 'resolved' or row.get('tier') != 'exact':
        if shared:
            return 'join', cites(item['atlas_person'], shared[0]), k
        why = row.get('outcome') if row else 'not in the run'
        return 'open', f'canon name has no exact LC authority ({why}{", " + row["tier"] if row and row.get("tier") else ""})', k
    lc = row['lcnaf']
    lc_qids = set(row.get('lc_wikidata', '').split())
    if lc in atlas_lc:
        return 'join', f'canon books resolve to lcnaf:{lc}, which anchors {k}', k
    if atlas_qid & lc_qids:
        return 'join', f'canon books resolve to lcnaf:{lc}, whose LC Wikidata link {sorted(atlas_qid & lc_qids)[0]} is the atlas QID', k
    if shared and atlas_lc:
        return 'open', f'conflict: {cites(item["atlas_person"], shared[0])}, but the canon books resolve to lcnaf:{lc}, ' \
            f'not {sorted(atlas_lc)[0]}', k
    if shared:
        # The canon name's books give lcnaf:{lc}; the shared work must be that person's too, or the key may
        # pool the atlas person with a namesake ('Johnson, Samuel': the theses' Johnson is the lexicographer,
        # the atlas's the historian of the Yoruba). LC's 670s, then the catalogue, for each shared work.
        for t in shared:
            how = 'LC 670' if confirm is None else confirm(t, lc)
            if how:
                return 'join', f'{cites(item["atlas_person"], t)}; {how} gives it to lcnaf:{lc}, the authority of the canon books', k
        return 'open', f'{cites(item["atlas_person"], shared[0])}, but LC does not confirm it is lcnaf:{lc}\'s', k
    if atlas_lc:
        return 'separate', f'canon books resolve to lcnaf:{lc}; the atlas person\'s works gave lcnaf:{sorted(atlas_lc)[0]}', k
    return 'open', f'canon books resolve to lcnaf:{lc}; atlas person has no LC anchor and no matching QID', k


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--names', type=Path, required=True, help='LC personal-name index (parquet)')
    ap.add_argument('--cache', type=Path, required=True, help='SRU response cache (shared with the canon route)')
    ap.add_argument('--delay', type=float, default=3.0)
    args = ap.parse_args()
    state = State.load(args.state)
    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    sheet_qid = {r['person_id']: r['wikidata']['qid'] for r in json.loads(SHEET.read_text(encoding='utf-8'))['people']
                 if r.get('status') == 'accepted' and r.get('wikidata')}
    with (args.run / 'canon-people-lc.csv').open(newline='', encoding='utf-8') as f:
        rows = {r['graph_key']: r for r in csv.DictReader(f)}
    snippets = atlas_snippets(json.loads((ROOT / 'historiography-1920-2000.json').read_text(encoding='utf-8')))
    works = cited_works({item['key'] for item in queue})
    fams = sorted({' '.join(words(item['name'].partition(', ')[0])) for item in queue})
    db = duckdb.connect()
    names = load_names(args.names, {r[0] for f in fams for r in db.execute(
        f"SELECT lcid FROM read_parquet('{args.names}') WHERE strip_accents(replace(replace(lower(label), 'œ', 'oe'), "
        "'æ', 'ae')) LIKE ?", [f + ',%']).fetchall()})
    fetch = Fetcher(args.cache, args.delay)
    decisions, clusters = [], []
    for item in queue:
        row = rows.get(item['key'])
        if state.lookup(f'diss-person:{item["key"]}'):
            decisions.append(dict(item, decision='done', reason='already keyed'))
            continue
        shared = shared_works(works.get(item['key'], []), snippets.get(item['atlas_person'], []))

        def confirm(title, lc, label=item['name']):
            if source_names_title(names[0].get(lc, {}).get('sources', []), title):
                return 'LC 670'
            return 'the LC catalogue' if title_authority(title, label, fetch, names) == lc else ''
        d, reason, k = decide(item, row, state, sheet_qid, shared, confirm)
        lc = dict(lcnaf=row.get('lcnaf', ''), lc_label=row.get('lc_label', ''), evidence_title=row.get('evidence_title', '')) if row else {}
        decisions.append(dict(item, decision=d, reason=reason, atlas_key=k, **lc))
        evidence = {f'dissertation-qid:{row["dissertation_qid"]}:{row["dissertation_qid_basis"] or "unknown"}'} \
            if row and row.get('dissertation_qid') else set()
        if d == 'join':
            clusters.append(dict(type='person', label=item['name'], resolution='established', aliases=set(),
                                 anchors={f'atlas:person:{item["atlas_person"]}', f'diss-person:{item["key"]}'},
                                 members=evidence, basis=f'deferred canon person joined by works: {reason}'))
        elif d == 'separate':
            clusters.append(dict(type='person', label=item['name'], resolution='unresolved', aliases=set(),
                                 anchors={f'diss-person:{item["key"]}'}, members=evidence,
                                 basis=f'deferred canon person separated by works: {reason}'))
    ops, assign, held = plan(state, clusters)
    materialise(state, dict(basis='canon deferred review', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis=f'deferred canon people resolved through their works (LC run {args.run.name})', decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'decisions.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=1) + '\n')
    summary = dict(run=args.run.name, queue=len(queue), decisions=dict(Counter(d['decision'] for d in decisions)),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
