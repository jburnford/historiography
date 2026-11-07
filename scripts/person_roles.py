"""Each person key's role: historian, primary-source person, other scholar, or not yet known (2026-11-06).

User, 2026-11-06: the 203,759 person keys are not 203,759 historians; "if you've reviewed a history book you are
probably not a primary source author; if you've supervised a student; if your dissertation is in the AHA database;
if you are in the AHA or British directories". Signals, from the graph build and git-tracked lists:
- historian, modern: a history PhD on record (`aha-phd:` AHA dissertation, `diss-author:` our corpus,
  `capes-person:` CAPES), a supervisor or a listed teacher of history (SUPERVISED or ADVISED edges,
  `repo-advisor:`, `aha:` AHA genealogy and directory tokens, `ihr:` the IHR's Teachers of History 2002-04), a reviewer (an authored review work, or `review-credit:`);
- historian, Wikidata: occupation historian (Q201788; data/wikidata/historians-qlever-2026-09-17). Wikidata also
  calls Diderot and Racine historians, so this signal counts only for people not dated before 1900;
- early: died before 1900, born before 1840 (data/person-facts/life-dates.csv), or first catalogued book (LC) from
  1450 to 1879 (ORCID-listed works are left out: their dates include page numbers, such as 584);
- cited as a primary source: in the dissertations, cited mostly in primary-source bibliography sections;
- scholar: an ORCID, cited mostly as scholarship, or a journal article on record.
Confidence: score = 2 per public identifier family (LC with VIAF/ISNI/GND/IdRef, Wikidata, ORCID) + 1 per
historian signal + 1 each for 5, 20 and 100 distinct works citing the key's works (doctoral theses, and JSTOR
articles from their notes) + 1 each for 3 and 10 works +
1 each for 1, 5 and 20 network partners (reviews given or received, supervision, advising, co-authors, co-editors,
volume editors). strong >= 6, supported 3-5, thin <= 2; and thin whenever fewer than 5 theses or articles cite the key and it has
no public identifier and no partner (user, 2026-11-06: such people weigh "well below people with lots of edges").
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
    # evidence weight: distinct theses citing the key's works, works authored, distinct network partners
    # citing works: doctoral theses (the corpus) and, from 2026-11-06, JSTOR articles (their notes); both count
    citing_by_kind = db.execute(f"""SELECT a."from", count(DISTINCT c."from") FILTER (WHERE cw.kind = 'thesis'),
            count(DISTINCT c."from") FILTER (WHERE cw.kind <> 'thesis') FROM '{G}/authored.parquet' a
            JOIN '{G}/cites.parquet' c ON c."to" = a."to" JOIN '{G}/work.parquet' cw ON cw.key = c."from" GROUP BY 1""").fetchall()
    citing = {k: t + o for k, t, o in citing_by_kind}
    citing_split = {k: (t, o) for k, t, o in citing_by_kind}
    works = dict(db.execute(f"""SELECT "from", count(DISTINCT "to") FROM '{G}/authored.parquet' GROUP BY 1""").fetchall())
    partners = defaultdict(set)
    for t in ('reviewed', 'advised', 'coauthored', 'coedited', 'editor_of'):
        for a, b in db.execute(f"""SELECT "from", "to" FROM '{G}/{t}.parquet'""").fetchall():
            if a != b:
                partners[a].add(b)
                partners[b].add(a)
    for a, b in db.execute(f"""SELECT s."from", a."from" FROM '{G}/supervised.parquet' s
            JOIN '{G}/authored.parquet' a ON a."to" = s."to\"""").fetchall():
        if a != b:
            partners[a].add(b)
            partners[b].add(a)
    rows, roles, signal_counts, tiers = [], Counter(), Counter(), Counter()
    for k, label, anchors, wd, orcid in people:
        schemes = {a.split(':', 1)[0] for a in anchors}
        sig = []
        if schemes & {'aha-phd', 'diss-author', 'capes-person'}:
            sig.append('history-phd')
        if k in supervisors or schemes & {'repo-advisor', 'aha', 'ihr'}:
            sig.append('supervisor-or-staff-list')
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
        modern = {'history-phd', 'supervisor-or-staff-list', 'reviewer'} & set(sig)
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
        hist = len(modern | ({'wikidata-historian'} & set(sig)))
        pid = (bool(schemes & {'lcnaf', 'viaf', 'isni', 'gnd', 'idref'}) + bool(wd) + bool(orcid))
        cites, nw, links = citing.get(k, 0), works.get(k, 0), len(partners.get(k, ()))
        score = (2 * pid + hist + (cites >= 5) + (cites >= 20) + (cites >= 100) + (nw >= 3) + (nw >= 10)
                 + (links >= 1) + (links >= 5) + (links >= 20))
        if cites < 5 and not pid and not links:        # the user's thin rule, whatever else is on record
            conf = 'thin'
        else:
            conf = 'strong' if score >= 6 else 'supported' if score >= 3 else 'thin'
        roles[role] += 1
        tiers[role, conf] += 1
        signal_counts.update(sig)
        ct, ca = citing_split.get(k, (0, 0))
        rows.append((k, role, ';'.join(sig), hist, pid, ct, ca, nw, links, score, conf))
    with gzip.open(OUT, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key', 'role', 'signals', 'historian_signals', 'pid_families', 'citing_theses', 'citing_articles', 'works', 'partners',
                    'score', 'confidence'])
        w.writerows(sorted(rows, key=lambda r: int(r[0].split('-')[1])))
    print(json.dumps(dict(roles=roles, signals=signal_counts,
                          confidence={f'{r} / {c}': n for (r, c), n in sorted(tiers.items())}), indent=1))


if __name__ == '__main__':
    main()
