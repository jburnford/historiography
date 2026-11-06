"""Each person key's role: historian, primary-source person, other scholar, or not yet known (2026-11-06).

User, 2026-11-06: the 203,759 person keys are not 203,759 historians; "if you've reviewed a history book you are
probably not a primary source author; if you've supervised a student; if your dissertation is in the AHA database;
if you are in the AHA or British directories". Signals, from the graph build and git-tracked lists:
- historian, modern: a history PhD on record (`aha-phd:` AHA dissertation, `diss-author:` our corpus,
  `capes-person:` CAPES), a supervisor (SUPERVISED or ADVISED edges, `repo-advisor:`, `aha:` AHA genealogy and
  directory tokens), a reviewer (an authored review work, or `review-credit:`);
- historian, Wikidata: occupation historian (Q201788; data/wikidata/historians-qlever-2026-09-17). Wikidata also
  calls Diderot and Racine historians, so this signal counts only for people not dated before 1900;
- early: died before 1900, born before 1840 (data/person-facts/life-dates.csv), or first catalogued book (LC) from
  1450 to 1879 (ORCID-listed works are left out: their dates include page numbers, such as 584);
- cited as a primary source: in the dissertations, cited mostly in primary-source bibliography sections;
- scholar: an ORCID, cited mostly as scholarship, or a journal article on record.
Role, in order: any modern historian signal -> historian; early -> primary source; Wikidata historian -> historian;
cited mostly as a primary source -> primary source; a scholar signal -> other scholar; otherwise unknown (mostly
LC book authors with no other facts). Roles describe evidence found, not identity: a historian with no PhD,
review or supervision on record shows as another role until one is keyed. A heuristic for counts and filters,
never an identity decision (duplicate keys are counted as they stand).

    python3 scripts/person_roles.py      # writes data/person-facts/person-roles.csv.gz
"""
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'build/graph'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
WD_HISTORIANS = ROOT / 'data/wikidata/historians-qlever-2026-09-17/historians.csv'
OUT = ROOT / 'data/person-facts/person-roles.csv.gz'


def year(v):
    m = re.match(r'^(-?\d+)', v or '')
    return int(m.group(1)) if m else None


def main():
    db = duckdb.connect()
    people = db.execute(f"SELECT key, label, anchors, wd, orcid FROM '{G}/person.parquet'").fetchall()
    supervisors = {k for (k,) in db.execute(f"""SELECT "from" FROM '{G}/supervised.parquet'
                                               UNION SELECT "from" FROM '{G}/advised.parquet'""").fetchall()}
    reviewers = {k for (k,) in db.execute(f"""SELECT DISTINCT a."from" FROM '{G}/authored.parquet' a
            JOIN '{G}/work.parquet' w ON w.key = a."to"
            WHERE len(w.reviewer_names) > 0 OR w.kind = 'review' OR w.key IN (SELECT "from" FROM '{G}/reviews.parquet')""").fetchall()}
    articles = {k for (k,) in db.execute(f"""SELECT DISTINCT a."from" FROM '{G}/authored.parquet' a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.kind = 'article'""").fetchall()}
    first_work = dict(db.execute(f"""SELECT a."from", min(w.year) FROM '{G}/authored.parquet' a
            JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.kind = 'book' AND w.year >= 1450 GROUP BY 1""").fetchall())
    with WD_HISTORIANS.open(newline='', encoding='utf-8') as f:
        wd_historians = {r['qid'] for r in csv.DictReader(f)}
    with (ROOT / 'data/person-facts/life-dates.csv').open(newline='', encoding='utf-8') as f:
        lives = {r['key']: (year(r['birth']), year(r['death'])) for r in csv.DictReader(f)}
    # primary vs scholarly citation of each corpus person (counts only)
    side = {pk: (p, s) for pk, p, s in db.execute(f"""SELECT a.person_key,
            sum(coalesce(TRY_CAST(json_extract(w.cited_as, '$.primary') AS INT), 0)),
            sum(coalesce(TRY_CAST(json_extract(w.cited_as, '$.secondary') AS INT), 0))
            FROM read_csv_auto('{CORPUS}/authored.csv.gz') a JOIN read_csv_auto('{CORPUS}/works.csv') w USING (work_id)
            GROUP BY 1""").fetchall()}
    rows, roles, signal_counts = [], Counter(), Counter()
    for k, label, anchors, wd, orcid in people:
        schemes = {a.split(':', 1)[0] for a in anchors}
        sig = []
        if schemes & {'aha-phd', 'diss-author', 'capes-person'}:
            sig.append('history-phd')
        if k in supervisors or schemes & {'repo-advisor', 'aha'}:
            sig.append('supervisor-or-aha-directory')
        if k in reviewers or 'review-credit' in schemes:
            sig.append('reviewer')
        born, died = lives.get(k, (None, None))
        fw = first_work.get(k)
        early = (died is not None and died < 1900) or (born is not None and born < 1840) or (fw is not None and fw < 1880)
        if early:
            sig.append('early')
        if wd and wd in wd_historians:
            sig.append('wikidata-historian')
        pks = [a.split(':', 1)[1] for a in anchors if a.startswith('diss-person:')]
        p = sum(side.get(x, (0, 0))[0] for x in pks)
        s = sum(side.get(x, (0, 0))[1] for x in pks)
        if p + s and p / (p + s) >= 0.5:
            sig.append('cited-as-primary')
        elif p + s:
            sig.append('cited-as-scholarship')
        if orcid:
            sig.append('orcid')
        if k in articles:
            sig.append('articles')
        modern = {'history-phd', 'supervisor-or-aha-directory', 'reviewer'} & set(sig)
        if modern:
            role = 'historian'
        elif early:
            role = 'primary source'
        elif 'wikidata-historian' in sig:
            role = 'historian'
        elif 'cited-as-primary' in sig:
            role = 'primary source'
        elif {'orcid', 'cited-as-scholarship', 'articles'} & set(sig):
            role = 'other scholar'
        else:
            role = 'unknown'
        roles[role] += 1
        signal_counts.update(sig)
        rows.append((k, role, ';'.join(sig)))
    with gzip.open(OUT, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key', 'role', 'signals'])
        w.writerows(sorted(rows, key=lambda r: int(r[0].split('-')[1])))
    print(json.dumps(dict(roles=roles, signals=signal_counts), indent=1))


if __name__ == '__main__':
    main()
