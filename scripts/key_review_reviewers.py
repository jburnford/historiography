"""Reviewers printed on review works -> person keys, only on a fact beyond the name (2026-11-06).

User, 2026-11-06: "Linking reviewers to people is a priority." key_jstor_reviews.py and key_crossref_reviews.py keyed
~215,000 reviews of keyed books with the reviewers' names as printed (`reviewer-name:` members) and, by design, no
reviewer keys: a name alone pools every bearer of it (Fable's design review,
data/identifiers/reviews-route-design-review-2026-11-05.md). This links a printed reviewer to an existing key by the
review's journal (the works-in-this-journal rule of that review):
- the key's name agrees with the printed name: same family name, the same first given name in full (no
  initial-only keys, no initial-only printed names) and compatible further names (namesake_check_groups.given_names_agree);
- the key has published in the same journal (articles or reviews), within ten years of the review: its works there
  come from the key's own identifiers (Crossref's works under the key's ORCID, the key's ORCID record, the JSTOR
  record of the key's keyed works, and review works already credited to the key: a rerun extends a journal's
  linked reviewer to their other reviews there, each chain starting from a non-name fact);
- no other key with an agreeing name has any work in that journal.
The reviewer then gets an `authored` claim on the review work (`journal-reviewer:<review work>:<key>`, recorded);
REVIEWED (reviewer -> the book's authors) follows in the graph build. Everything else stays a printed name.

    python3 scripts/key_review_reviewers.py --out data/identifiers/review-reviewers-2026-11-06
"""
import argparse
import glob
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from namesake_check_groups import given_names_agree, given_words

GRAPH = ROOT / 'build/graph'
CROSSREF_ORCID = Path('/mnt/e/crossref-orcid')
ORCID_RECORDS = ROOT / 'data/orcid-2026-09-21/records'
JSTOR = Path('/mnt/e/jstor-index.parquet')


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def journal_key(j):
    j = re.sub(r'[^a-z0-9 ]+', ' ', fold(j))
    j = re.sub(r'^the ', '', ' '.join(j.split()))
    return j


def family(label):
    return fold(label.split(',')[0] if ',' in label else (label.split() or [''])[-1]).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--window', type=int, default=10)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    db = duckdb.connect()
    people = db.execute(f"SELECT key, label, orcid FROM '{GRAPH}/person.parquet'").fetchall()
    by_family = defaultdict(list)
    for k, label, orcid in people:
        g = given_words(label or '')
        if g and len(g[0]) > 1:                     # no initial-only keys
            by_family[family(label)].append((k, label))
    # the journals each key has published in, from its own identifiers
    journals = defaultdict(lambda: defaultdict(set))   # key -> journal -> {years}
    orcid_key = {o: k for k, _, o in people if o}
    for f in glob.glob(str(CROSSREF_ORCID / '*.json')):
        k = orcid_key.get(Path(f).stem)
        if not k:
            continue
        for it in json.loads(Path(f).read_text()):
            j = ((it.get('container-title') or ['']) or [''])[0]
            y = ((it.get('issued') or {}).get('date-parts') or [[None]])[0][0]
            if j and y:
                journals[k][journal_key(j)].add(y)
    for o, k in orcid_key.items():
        p = ORCID_RECORDS / f'{o}.json'
        if not p.exists():
            continue
        for g in ((json.loads(p.read_text()).get('activities-summary') or {}).get('works') or {}).get('group') or []:
            s = g['work-summary'][0]
            j = ((s.get('journal-title') or {}) or {}).get('value')
            y = (((s.get('publication-date') or {}) or {}).get('year') or {}).get('value')
            if j and (y or '').isdigit():
                journals[k][journal_key(j)].add(int(y))
    for k, container, year in db.execute(f"""
            SELECT a."from", j.container, j.year FROM '{GRAPH}/authored.parquet' a
            JOIN (SELECT key, unnest(anchors) AS an FROM '{GRAPH}/work.parquet') w ON w.key = a."to"
            JOIN '{JSTOR}' j ON 'doi:' || j.doi = w.an
            WHERE w.an LIKE 'doi:10.2307/%' AND j.kind = 'article'""").fetchall():
        if container and year:
            journals[k][journal_key(container)].add(year)
    # reviews already credited to the key (by ORCID, or by this rule on an earlier run) show it publishes there too
    for k, j, y in db.execute(f"""SELECT a."from", w.journal, w.year FROM '{GRAPH}/authored.parquet' a
            JOIN '{GRAPH}/work.parquet' w ON w.key = a."to" WHERE w.journal IS NOT NULL AND w.year IS NOT NULL""").fetchall():
        journals[k][journal_key(j)].add(y)
    reviews = db.execute(f"""SELECT key, reviewer_names, journal, year FROM '{GRAPH}/work.parquet'
                             WHERE len(reviewer_names) > 0 AND journal IS NOT NULL""").fetchall()
    report = Counter(reviews=len(reviews), keys_with_journals=len(journals))
    state = State.load(args.state)
    ops, sample = [], []
    for wk, names, journal, year in reviews:
        jk = journal_key(journal)
        for n in names:
            g = given_words(n)
            if not g or len(g[0]) <= 1:
                report['initial_only_name'] += 1
                continue
            fam = family(n if ',' in n else n)
            cands = [(k, l) for k, l in by_family.get(fam, ())
                     if given_words(l)[0] == g[0] and given_names_agree(n, l)]
            if not cands:
                report['no_agreeing_key'] += 1
                continue
            in_journal = [k for k, _ in cands if jk in journals.get(k, {})]
            near = [k for k in in_journal if not year or any(abs(y - year) <= args.window for y in journals[k][jk])]
            if len(near) != 1 or len(in_journal) != 1:
                report['several_in_journal' if len(in_journal) > 1 else 'none_in_journal'] += 1
                continue
            k = near[0]
            anchor = f'journal-reviewer:{wk}:{k}'
            if anchor in state.anchor:
                report['claim_exists'] += 1
                continue
            report['linked'] += 1
            ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=[anchor], relation=dict(subject=k, predicate='authored', object=wk),
                            basis=f"review in {journal} ({year}) printed as by {n}; the key's own works include "
                                  f"{journal} ({', '.join(str(y) for y in sorted(journals[k][jk])[:3])}) and no other "
                                  f"key of that name has work there"))
            if len(sample) < 60:
                sample.append(dict(review=wk, journal=journal, year=year, printed=n, key=k,
                                   label=dict(cands)[k], journal_years=sorted(journals[k][jk])[:5]))
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="printed reviewers linked to keys that have published in the review's journal", decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()
