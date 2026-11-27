#!/usr/bin/env python3
"""Split back person keys the 2026-11-17 dissertation graph pooled, without rebuilding the graph.

The graph build (build_dissertation_citation_graph.py) merged person keys that shared one Wikidata QID
whatever their given names, and the QID could reach a key through a single work's catalogue identity (an
'Introduction' by Laura Downs on the key of Gregory P. Downs). Keys of different people were pooled
('nye|mary' into 'nye|david e', 'downs|laura' into 'downs|gregory p', 'taylor|a' into 'taylor|alan') and the
pooled key printed the other person's name. The build is fixed (``guard`` in ``assign_work_authors`` and
``resolve_people``, ``display_name``), but the graph is rebuilt on the cluster (about 3 h, 30 GB). Until
then this script reruns the build's person resolution for the surnames that matter to the canon maps only
(every surname of a person key cited by ``--min`` or more strict theses in any scope), reading the same
inputs, twice: as built (no guard) and with the guard. It writes

- ``person-unpool.csv.gz``: work id, the key the graph's authored.csv.gz gives it, the key the guarded
  build gives it, for every authored pair the guard changes;
- ``person-unpool-people.csv.gz``: for every person key of those surnames in the guarded run, its display name
  (``display_name``: the key's own most printed full spelling), QID and QID basis, strict citing theses;
- ``person-unpool-report.json``: how faithfully the unguarded run reproduces the graph (authored pairs and
  per-key citing theses), and the pooled merges by step, with counts.

historian_cocitation_network.py applies the first two when present. Entries are streamed; only the selected
surnames' entries are held. Thesis text is never written.

    python3 scripts/dissertation_person_unpool.py [--min 15]
"""
import argparse
from collections import Counter, defaultdict
import csv
import gc
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dissertation_citation_graph as b  # noqa: E402
from dissertation_names import bibliography_order, normalise_first_authors, split_name  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
KEEP = ('dissertation', 'n', 'kind', 'title', 'authors', 'surnames', 'author_from_dash')


def authored_sha(out=D):
    return hashlib.sha256((out / 'authored.csv.gz').read_bytes()).hexdigest()


def load_overrides(out=D):
    """({(work id, graph key): key}, {key: people row}) from the files this script writes; empty without them.

    They apply only to the graph they were made from (``authored_sha256`` in the report): a rebuilt graph
    carries the guard itself, and the overrides are then ignored."""
    moved, people = {}, {}
    table, names, report = out / 'person-unpool.csv.gz', out / 'person-unpool-people.csv.gz', out / 'person-unpool-report.json'
    if not table.exists() or not report.exists():
        return moved, people
    if json.loads(report.read_text()).get('authored_sha256') != authored_sha(out):
        print('person-unpool: made from another graph build; not applied', file=sys.stderr)
        return moved, people
    with gzip.open(table, 'rt', encoding='utf-8', newline='') as f:
        moved = {(r['work_id'], r['graph_key']): r['key'] for r in csv.DictReader(f)}
    if names.exists():
        with gzip.open(names, 'rt', newline='', encoding='utf-8') as f:
            people = {r['person_key']: dict(r, name=clean_name(r['name'])) for r in csv.DictReader(f)}
    return moved, people


# A cited title run on after the given names ("Abreu, Márcia. 'Leituras no Brasil colonial.'", "Bates, Henry Walter.
# 'Contributions of an insect fauna'", "Bell, Dean P. ―Jews"): display_name's TITLE_DEBRIS did not catch quoted titles
# when person-unpool-people.csv.gz was written (2026-11-22), so the names are trimmed where they are read.
RUN_ON_TITLE = re.compile(r"\.?\s+[‘'\"“―‖].*$|\.\s+\S*['’]\S.*$|\.\s+(?:\S+\s+){3,}\S+.*$")


def clean_name(name):
    surname, comma, given = name.partition(',')
    if not comma:
        return name
    return f'{surname},{RUN_ON_TITLE.sub("", given)}'.rstrip(' ,')


def target_surnames(minimum):
    out = set()
    with (D / 'cited-people.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            k = r['person_key']
            if '|' in k and max(int(v) for c, v in r.items() if c.startswith('cited_by_') and c != 'cited_by_all'
                                and v.isdigit()) >= minimum:
                out.add(k.split('|', 1)[0])
    return out


def grams(name):
    """Every run of one to three folded tokens of a name: a superset of where its surname can be."""
    t = b.fold(name).split()
    return {' '.join(t[i:i + n]) for n in (1, 2, 3) for i in range(len(t) - n + 1)}


def mentions(e, targets):
    """Whether any of the entry's first six authors may carry a target surname."""
    return any(grams(a) & targets for a in (e.get('authors') or [])[:6] if a)


def load_entries(targets):
    """The build's entry set (latest extraction, n within its count, notes for theses rebuilt from notes,
    comma-less first authors normalised by each thesis's alphabetisation), for entries naming a target."""
    theses = {r['id']: r for r in csv.DictReader((D / 'dissertations.csv').open(newline='', encoding='utf-8'))}
    extraction = {}
    for line in (D / 'extraction.jsonl').open():
        x = json.loads(line)
        extraction[x['id']] = x
    kept, commaless = {}, {}
    t0 = time.time()
    with (D / 'entries.jsonl').open() as f:
        for i, line in enumerate(f):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e['dissertation'] not in extraction:
                continue
            key = (e['dissertation'], e['n'])
            kept.pop(key, None)
            commaless.pop(key, None)
            a0 = (e.get('authors') or [None])[0]
            if a0 and ',' not in a0:
                commaless[key] = (a0, bool(e.get('author_from_dash')))
            if mentions(e, targets):
                kept[key] = {k: e[k] for k in KEEP if k in e}
            if i % 1_000_000 == 0:
                print(f'  entries {i:,} ({time.time() - t0:.0f} s), kept {len(kept):,}', file=sys.stderr, flush=True)
    limit = {d: x.get('entries') or 0 for d, x in extraction.items()}
    kept = {k: e for k, e in kept.items() if k[1] < limit[k[0]]}
    undecided = defaultdict(list)
    for (d, n), (a0, dash) in sorted(commaless.items()):
        if n < limit[d] and split_name(a0) is None and not dash:
            undecided[d].append(a0)
    by_thesis = defaultdict(list)
    for (d, n), e in sorted(kept.items()):
        by_thesis[d].append(e)
    for d, rows in by_thesis.items():
        normalise_first_authors(rows, order=bibliography_order(undecided.get(d, [])))
    notes_used = {d for d, r in theses.items() if r['extraction_status'] == 'parsed_notes'}
    entries = [e for e in kept.values() if e['dissertation'] not in notes_used]
    for line in (D / 'notes-entries.jsonl').open():
        e = json.loads(line)
        if e['dissertation'] in notes_used and mentions(e, targets):
            entries.append(dict({k: e[k] for k in KEEP if k in e}, n=f"notes-{e['n']}"))
    return entries, theses, extraction


def run(entries, theses, extraction, targets, authorities, guard):
    """The build's works and person resolution (build_dissertation_citation_graph.main) on these entries."""
    counted = {d for d, r in theses.items() if r['extraction_status'] in ('parsed', 'parsed_notes') and not r['graph_excluded']}
    raw_key, by_sur = {}, defaultdict(set)
    for e in entries:
        if e['kind'] not in b.CITABLE or not e.get('surnames') or not e.get('title'):
            continue
        sur, tk = b.fold(e['surnames'][0]), b.title_key(e['title'])
        if not sur or len(tk) < 3:
            continue
        if e['kind'] in ('article', 'chapter'):
            tk += '|a'
        raw_key[(e['dissertation'], e['n'])] = (sur, tk)
        by_sur[sur].add(tk)
    alias = b.merge_titles(by_sur, Counter(raw_key.values()))
    translation_of = {}
    for line in (D / 'work-translations.jsonl').open():
        r = json.loads(line)
        if r['work_id'] != r['canonical']:
            translation_of[r['work_id']] = r['canonical']
    now = {'W:' + '|'.join(k): 'W:' + '|'.join(alias.get(k, k)) for k in set(raw_key.values())}
    translation_of = {now.get(a, a): now.get(c, c) for a, c in translation_of.items()}
    translation_of = {a: c for a, c in translation_of.items() if a != c}
    persons = defaultdict(lambda: dict(names=Counter(), roles=Counter()))
    works = defaultdict(lambda: dict(titles=Counter(), author_variants=Counter(), authors=[], citing=set()))

    def add_person(name, inverted, role):
        key, display = b.person_key(name, inverted)
        if key:
            persons[key]['names'][display] += 1
            persons[key]['roles'][role] += 1
        return key

    docs = json.load((D / 'doctorates.json').open())
    for d in docs:
        if d['id'] not in extraction:
            continue
        for a in d['authors']:
            if grams(a) & targets:
                add_person(a, 'auto', 'dissertation_author')
        for a in d.get('advisors', []):
            for part in b.re.split(r'\s*;\s*', a):
                part = b.re.sub(r'\s*\([^)]*\)', '', part).strip(' ,')
                if grams(part) & targets:
                    add_person(part, 'auto', 'supervisor')
    seen = set()
    for e in entries:
        key = raw_key.get((e['dissertation'], e['n']))
        if not key or e['dissertation'] not in counted:
            continue
        key = alias.get(key, key)
        wid = translation_of.get('W:' + '|'.join(key), 'W:' + '|'.join(key))
        w = works[wid]
        w['titles'][e['title']] += 1
        w['author_variants'][tuple(e['authors'][:6])] += 1
        if (e['dissertation'], wid) not in seen:
            seen.add((e['dissertation'], wid))
            w['citing'].add(e['dissertation'])
    person_ids = defaultdict(lambda: dict(qids=Counter(), ids=set()))
    b.assign_work_authors(works, persons, authorities, add_person, person_ids, guard=guard)
    trace = {}
    alias_p, tiers = b.resolve_people(persons, works, person_ids, D, guard=guard, trace=trace)
    for w in works.values():
        w['authors'] = [alias_p.get(a, a) for a in w['authors']]
    b.apply_person_splits(works, persons, person_ids, tiers, D)
    authored = {(wid, k) for wid, w in works.items() for k in w['authors'] if k}
    return dict(works=works, persons=persons, person_ids=person_ids, tiers=tiers, alias=alias_p, trace=trace,
                authored=authored)


def batches(targets, n):
    """Alphabetical runs of surnames of about equal citation weight (near-spellings mostly stay together)."""
    weight = Counter()
    with (D / 'cited-people.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            sur = r['person_key'].split('|', 1)[0]
            if sur in targets:
                weight[sur] += int(r['cited_by_all'] or 0) + 1
    total, out, cur, acc = sum(weight.values()), [], set(), 0
    for sur in sorted(targets):
        cur.add(sur)
        acc += weight[sur]
        if acc >= total * (len(out) + 1) / n and len(out) < n - 1:
            out.append(cur)
            cur = set()
    return out + [cur]


def one_batch(targets):
    """Both runs for one batch of surnames; only what main needs is returned."""
    entries, theses, extraction = load_entries(targets)
    authorities = {}
    for line in (D / 'work-authorities.jsonl').open():
        r = json.loads(line)
        if r['work_id'].split('|', 1)[0][2:] in targets:
            authorities[r['work_id']] = r

    def mine(pairs):
        return {(w, k) for w, k in pairs if w.split('|', 1)[0][2:] in targets}
    res = dict(entries=len(entries))
    built = run(entries, theses, extraction, targets, authorities, guard=False)
    res['built'] = dict(authored=mine(built['authored']), trace=built['trace'], alias=built['alias'])
    del built
    gc.collect()
    fixed = run(entries, theses, extraction, targets, authorities, guard=True)
    people = {}
    for k, p in fixed['persons'].items():
        if '|' in k and k.split('|', 1)[0] in targets and p['names']:
            qids = fixed['person_ids'].get(k, {}).get('qids')
            people[k] = (b.display_name(k, p['names']), qids.most_common(1)[0][0] if qids else '',
                         fixed['tiers'].get(k, 'catalogue_title_match') if qids else '')
    res['fixed'] = dict(authored=mine(fixed['authored']), alias=fixed['alias'], people=people)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--min', type=int, default=15, help='surnames of person keys cited by this many strict theses in any scope')
    ap.add_argument('--out', type=Path, default=D)
    ap.add_argument('--batches', type=int, default=6, help='surnames are run in this many alphabetical batches (memory)')
    args = ap.parse_args()
    targets = target_surnames(args.min)
    print(f'{len(targets):,} surnames in {args.batches} batches', file=sys.stderr)
    theses = {r['id']: r for r in csv.DictReader((D / 'dissertations.csv').open(newline='', encoding='utf-8'))}
    strict = {d for d, r in theses.items() if r['in_analysis'] == 'True'}
    country = {d: r['country'] for d, r in theses.items()}
    built = dict(authored=set(), trace={}, alias={})
    fixed = dict(authored=set(), alias={}, people={})
    n_entries = 0
    for i, part in enumerate(batches(targets, args.batches)):
        res = one_batch(part)
        n_entries += res.pop('entries')
        for k in ('authored', 'trace', 'alias'):
            built[k].update(res['built'][k])
        for k in ('authored', 'alias', 'people'):
            fixed[k].update(res['fixed'][k])
        del res
        gc.collect()
        print(f'  batch {i + 1}/{args.batches}: {len(part):,} surnames done', file=sys.stderr, flush=True)

    # Fidelity: the unguarded run against the graph, on works whose first author's surname is a target.
    def in_scope(wid):
        return wid.split('|', 1)[0][2:] in targets
    graph = set()
    with gzip.open(D / 'authored.csv.gz', 'rt', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if in_scope(r['work_id']) and r['person_key'].split('|', 1)[0] in targets:
                graph.add((r['work_id'], r['person_key']))
    mine = {(w, k) for w, k in built['authored'] if in_scope(w) and k.split('|', 1)[0] in targets}
    work_theses = defaultdict(set)
    with gzip.open(D / 'strict-citations.csv.gz', 'rt', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if in_scope(r['work_id']):
                work_theses[r['work_id']].add(r['dissertation_id'])

    def citing(pairs):
        out = defaultdict(set)
        for w, k in pairs:
            out[k] |= work_theses.get(w, set())
        return out
    g_cite, m_cite = citing(graph), citing(mine)
    cited_rows = {r['person_key']: r for r in csv.DictReader((D / 'cited-people.csv').open(newline='', encoding='utf-8'))
                  if r['person_key'].split('|', 1)[0] in targets}
    big = [k for k, r in cited_rows.items() if int(r['cited_by_dissertations']) >= args.min]
    exact = sum(len(g_cite[k] & strict) == len(m_cite[k] & strict) for k in big)
    within = sum(abs(len(g_cite[k] & strict) - len(m_cite[k] & strict)) <= max(2, 0.05 * len(g_cite[k] & strict)) for k in big)

    # The guard's changes, as overrides on the graph's own pairs: a work keeps its graph key unless the
    # unguarded run agrees with the graph on it and the guarded run gives it another key.
    changes = []
    fixed_by_work = defaultdict(set)
    for w, k in fixed['authored']:
        fixed_by_work[w].add(k)
    built_by_work = defaultdict(set)
    for w, k in built['authored']:
        built_by_work[w].add(k)
    for w, k in sorted(graph):
        if k in built_by_work.get(w, ()) and k not in fixed_by_work.get(w, ()):
            new = sorted(fixed_by_work[w] - built_by_work[w])
            if len(new) == 1:
                changes.append((w, k, new[0]))
    with gzip.open(args.out / 'person-unpool.csv.gz', 'wt', encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['work_id', 'graph_key', 'key'])
        wr.writerows(changes)
    # People of the target surnames in the guarded run: display name, QID, citing theses after the changes.
    moved = {(w, k): n for w, k, n in changes}
    after = defaultdict(set)
    for w, k in graph:
        after[moved.get((w, k), k)] |= work_theses.get(w, set())
    with gzip.open(args.out / 'person-unpool-people.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['person_key', 'name', 'qid', 'qid_basis', 'cited_by_dissertations', 'cited_by_country'])
        for k in sorted(fixed['people']):
            name, qid, tier = fixed['people'][k]
            n = after.get(k, set()) & strict
            if not n and k not in cited_rows:
                continue
            wr.writerow([k, name, qid, tier, len(n), json.dumps(dict(sorted(Counter(country[d] for d in n).items())))])
    # The pooled merges: keys the unguarded run aliased by QID that the guard keeps apart.
    pooled = Counter()
    examples = defaultdict(list)
    gained = defaultdict(set)
    for w, _, new in changes:
        gained[new] |= work_theses.get(w, set())
    for k, step in built['trace'].items():
        if k in fixed['alias']:
            continue
        head = built['alias'].get(k)
        reason = 'initial_only' if b.initial_only(k) else 'given_names_conflict'
        pooled[f'{step}:{reason}'] += 1
        n = len(gained.get(k, set()) & strict)
        examples[f'{step}:{reason}'].append((n, k, head))
    report = dict(
        authored_sha256=authored_sha(), surnames=len(targets), batches=args.batches, entries=n_entries, min_theses=args.min,
        fidelity=dict(graph_pairs=len(graph), rerun_pairs=len(mine), shared=len(graph & mine),
                      keys_checked=len(big), keys_same_count=exact, keys_within_5pct=within),
        guard_changes=dict(authored_pairs_moved=len(changes), works=len({w for w, _, _ in changes}),
                           graph_keys_losing_works=len({k for _, k, _ in changes}), keys_gaining=len({n for *_, n in changes})),
        pooled_merges_refused=dict(pooled),
        examples={s: [dict(theses=n, key=k, was_merged_into=h) for n, k, h in sorted(v, reverse=True)]
                  for s, v in examples.items()})
    (args.out / 'person-unpool-report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'examples'}, indent=1))


if __name__ == '__main__':
    main()
