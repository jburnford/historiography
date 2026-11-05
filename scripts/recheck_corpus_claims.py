"""Authorship claims made through a corpus id, checked against the record's own author names (2026-11-05).

key_cited_articles.py (`cited-authored:<doi>:<corpus id>`) and apply_work_verdicts.py (`verdict-authored:...`) wrote
`authored` claims whose subject is the corpus id (`diss-person:allen|robert`), checking only the family name in the
JSTOR or Crossref record. A corpus id can pool namesakes, so every namesake's article reached whichever key holds the
id: Robert Allen the film scholar's key carries the economist's articles (person-dups-2026-11-04: 236 of 441 keys of
much-cited people mix several people's works). This reads each claim's record (JSTOR export creators, Crossref cache)
and compares the record's author of that family with the person the id's key names, by its fullest form (the LC
heading when the key holds one): a claim is withdrawn when the given names disagree
(namesake_check_groups.given_names_agree: 'John E. Smith' is not Paul Smith; 'R. C. Allen' and 'Robert Clyde Allen'
agree, so this catches only part of the mixing; the rest needs reading by works). Claims whose record cannot be
read, or whose record has no author of that family, are counted and left. The conflicts (candidates.json) go to Sol
by works (corpus_claim_groups.py) before any is withdrawn; proposal.json is the rule's list, not applied as such.

    python3 scripts/recheck_corpus_claims.py --out data/identifiers/corpus-claims-recheck-2026-11-05
    python3 scripts/identifiers.py apply data/identifiers/corpus-claims-recheck-2026-11-05/proposal.json
"""
import argparse
import glob
import gzip
import json
from collections import Counter
from pathlib import Path

import duckdb
import orjson

from identifiers import ROOT
from key_cited_works import family_of
from namesake_check_groups import given_names_agree

JSTOR = Path('/mnt/e/jstor_metadata_2026-10-23.jsonl.gz')
CROSSREF = Path('/mnt/e/crossref-cited/answers.jsonl')
LC_NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
GRAPH = ROOT / 'build/graph'


def claims(directory):
    """(claim key, subject corpus id, object doi or other identifier, anchor scheme) for corpus-id authorship claims."""
    out = []
    for f in sorted(glob.glob(f'{directory}/events-*.jsonl*')):
        op = gzip.open if f.endswith('.gz') else open
        with op(f, 'rt', encoding='utf-8') as fh:
            for line in fh:
                if '"subject": "diss-person:' not in line:
                    continue
                e = json.loads(line)
                r = e.get('relation') or {}
                if e.get('event') == 'mint' and r.get('predicate') in ('authored', 'edited'):
                    out.append((e['key'], r['subject'].split(':', 1)[1], r['object'], e['anchors'][0].split(':', 1)[0]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--log', type=Path, default=ROOT / 'data/identifiers')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    cs = claims(args.log)
    report = Counter(claims=len(cs))
    dois = {o.split(':', 1)[1].lower() for _, _, o, _ in cs if o.startswith('doi:')}
    authors = {}                                       # doi -> [(family, 'Given Family')]
    with gzip.open(JSTOR, 'rb') as fh:
        for line in fh:
            o = orjson.loads(line)
            d = (o.get('ithaka_doi') or '').lower()
            if d in dois:
                authors[d] = [(family_of(c.get('last_name') or ''), f"{c.get('last_name') or ''}, {c.get('first_name') or ''}")
                              for c in o.get('creators') or []]
    if CROSSREF.exists():
        with CROSSREF.open(encoding='utf-8') as fh:
            for line in fh:
                for it in json.loads(line).get('items') or []:
                    d = (it.get('DOI') or '').lower()
                    if d in dois and d not in authors:
                        authors[d] = [(family_of(x.get('family') or ''), f"{x.get('family') or ''}, {x.get('given') or ''}")
                                      for x in it.get('author') or []]
    report['records_read'] = len(authors)
    db = duckdb.connect()
    holder = {a.split(':', 1)[1]: (k, label, lc) for k, label, lc, a in db.execute(
        f"SELECT key, label, lcnaf, a FROM (SELECT key, label, lcnaf, unnest(anchors) a FROM '{GRAPH}/person.parquet') "
        "WHERE a LIKE 'diss-person:%'").fetchall()}
    lcs = sorted({h[2] for h in holder.values() if h[2]})
    db.execute('CREATE TABLE want(lcid VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(x,) for x in lcs])
    lc_label = dict(db.execute(f"SELECT lcid, label FROM read_parquet('{LC_NAMES}') WHERE lcid IN (SELECT lcid FROM want)").fetchall())
    ops, sample, cands = [], [], []
    for claim, p, obj, scheme in cs:
        if not obj.startswith('doi:'):
            report['not_doi'] += 1
            continue
        rec = authors.get(obj.split(':', 1)[1].lower())
        h = holder.get(p)
        if rec is None or not h:
            report['record_or_holder_missing'] += 1
            continue
        fam = family_of(p.split('|')[0])
        names = [n for f, n in rec if f == fam and n.split(', ', 1)[-1].strip()]
        if not names:
            report['no_given_name_of_family'] += 1
            continue
        person = lc_label.get(h[2]) or h[1]
        if any(given_names_agree(n, person) for n in names):
            report['agree'] += 1
            continue
        report['withdraw'] += 1
        ops.append(dict(event='withdraw', key=claim, basis=f'{scheme} claim through corpus id {p}: the record {obj} names '
                        f"{' / '.join(names)}, not {person} ({h[0]}), whose key holds the id"))
        cands.append(dict(claim=claim, id=p, record=names, person=person, key=h[0], doi=obj))
        if len(sample) < 60:
            sample.append(cands[-1])
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="authorship claims through a corpus id whose record names another person of that family", decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'candidates.json').write_text(json.dumps(cands, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()
