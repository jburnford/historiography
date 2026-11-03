"""Audit the AHA genealogy's advisor -> own-dissertation links against education facts (2026-11-02).

key_aha joined each advisor token (`aha:<token>`) to the author of the AHA dissertation the genealogy linked as
their own (`aha-phd:<record>`). 4,409 links rest on 'unique name and date': the only AHA record under the
advisor's name, at a plausible date. An advisor whose doctorate is not in the AHA directory (an Oxford DPhil)
is then joined to a namesake: David Wright, historian of medicine at McMaster and McGill, was joined to the
Wisconsin dissertation of 1991 on Limoges. A few links were chosen by topic similarity.

For every link, the key holding the token (followed through merges) is read from the key log without loading
it, and its PIDs give education facts (key_aha_career: Wikidata P69, the cached ORCID record, LC's notes):
- `confirmed`: an education agrees with the school of the linked dissertation;
- `contradicted_lc`: LC's notes speak of a doctorate at another school only ('Thesis (Ph. D.)--Yale');
- `doubtful`: Wikidata or ORCID list education, none at the linked school (often a first degree only);
- `no_facts`: the key has no PID or its PIDs state no education.
Nothing is changed; `audit.json` lists every link with its outcome and facts.

    python3 scripts/audit_aha_own_links.py --out data/identifiers/aha-own-link-audit-2026-11-02
"""
import argparse
import csv
import glob
import json
from collections import Counter, defaultdict
from pathlib import Path

from aha_links import school, school_agrees
from identifiers import DEFAULT_DIR, open_shard, shards
from key_aha import AHA
from key_aha_career import DOCTORATE, lc_facts, orcid_facts, wikidata_facts

GENEALOGY = AHA / 'genealogy/advisor-links.csv'
GENERIC = {'calif', 'state', 'new', 'north', 'south', 'east', 'west', 'saint', 'thesi', 'from', 'with', 'histo'}
ABBREV = {'ucla': 'california los angeles', 'u c l a': 'california los angeles',
          'unc': 'north carolina', 'nyu': 'new york', 'cuny': 'city new york', 'lse': 'london economics'}


def agrees(fact, record_school):
    """A fact names the dissertation's school: aha_links.school_agrees, or a distinctive school word in common
    ('Ph. D. from University of Virginia in 1966' / 'Univ. of Virginia, Corcoran Dept. of History')."""
    f = ' ' + ' '.join(fact.lower().replace('.', ' ').split()) + ' '
    for k, v in ABBREV.items():
        f = f.replace(f' {k} ', f' {v} ')
    return school_agrees(fact, record_school) or bool((school(f) & school(record_school)) - GENERIC)
KEEP = ('aha:', 'aha-phd:', 'wd:', 'lcnaf:', 'orcid:')


def person_anchors(directory):
    """key -> anchors (KEEP schemes only), following mint/attach/detach/merge, without loading the full log."""
    anchors, into = defaultdict(set), {}
    for f in shards(directory):
        for line in open_shard(f):
            if '"key": "p-' not in line:
                continue
            e = json.loads(line)
            k, kind = e['key'], e['event']
            if kind in ('mint', 'attach'):
                anchors[k] |= {a for a in e.get('anchors', ()) if a.startswith(KEEP)}
            elif kind == 'detach':
                anchors[k] -= set(e.get('anchors', ()))
            elif kind == 'merge':
                into[k] = e['into']
                anchors[e['into']] |= anchors.pop(k, set())

    def live(k):
        while k in into:
            k = into[k]
        return k
    return anchors, live


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--lc-dir', default='/mnt/e/lc-authorities')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = {r['id']: r for r in csv.DictReader(f)}
    with GENEALOGY.open(newline='', encoding='utf-8') as f:
        links = [r for r in csv.DictReader(f) if r['status'].startswith('linked') and r['own_record']]
    anchors, live = person_anchors(args.state)
    holder = {}
    for k, s in anchors.items():
        for a in s:
            if a.startswith('aha:'):
                holder[a] = k
    rows, qids, lcids = [], set(), set()
    for l in links:
        k = holder.get(f'aha:{l["advisor_id"]}')
        a = anchors.get(k, set()) if k else set()
        row = dict(advisor_id=l['advisor_id'], advisor=l['advisor'], basis=l['basis'], record=l['own_record'],
                   record_school=records[l['own_record']]['department'], record_year=l['own_year'], key=k,
                   wd=sorted(x[3:] for x in a if x.startswith('wd:')), lc=sorted(x[6:] for x in a if x.startswith('lcnaf:')),
                   orcid=sorted(x[6:] for x in a if x.startswith('orcid:')),
                   record_on_key=f'aha-phd:{l["own_record"]}' in a)
        qids |= set(row['wd'])
        lcids |= set(row['lc'])
        rows.append(row)
    (args.out / 'cache').mkdir(exist_ok=True)
    wf = wikidata_facts(qids, args.out / 'cache') if qids else {}
    lf = lc_facts(sorted(lcids), args.lc_dir)
    report = Counter()
    for row in rows:
        lc_edu = sorted({c for x in row['lc'] for c in lf.get(x, {}).get('edu', ()) if DOCTORATE.search(c)})
        other = sorted({e for q in row['wd'] for e in wf.get(q, {}).get('edu', ())} |
                       {e for o in row['orcid'] for e in orcid_facts(o)['edu']})
        row.update(lc_doctorate=lc_edu, education=other)
        school_of = row['record_school']
        if any(agrees(e, school_of) for e in lc_edu + other):
            out = 'confirmed'
        elif any(school(c) - {'thesi', 'diss', 'disse', 'docto'} for c in lc_edu):
            out = 'contradicted_lc'
        elif other:
            out = 'doubtful'
        else:
            out = 'no_facts' if not (row['wd'] or row['lc'] or row['orcid']) else 'pid_no_education'
        row['outcome'] = out
        report[out] += 1
        report[f'{"topic" if row["basis"].startswith("2 namesakes") or "similarity" in row["basis"] else "name"}:{out}'] += 1
    (args.out / 'audit.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n')
    summary = dict(links=len(rows), **dict(sorted(report.items())))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
