"""Build the Sol check of advisor -> own-dissertation links the audit doubts (2026-11-03).

Input: data/identifiers/aha-own-link-audit-2026-11-03/audit.json (scripts/audit_aha_own_links.py on the key log
after the 11-02 merges). Kept: links whose record is still on the advisor's key and
- `contradicted_lc`, re-read with key_aha_lc_notes.assess (LC's abbreviations, 'postdoctoral' and URLs are not
  doctorates): LC's notes name a doctorate at another school and none at the linked one (14);
- `doubtful`: Wikidata or ORCID list education, none at the linked school (71).
Writes groups.json (groups of eight) for run-sol.sh.

    python3 data/identifiers/own-thesis-check-2026-11-03/build-groups.py
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from key_aha import AHA  # noqa: E402
from key_aha_lc_notes import assess, lc_records  # noqa: E402

audit = json.loads((ROOT / 'data/identifiers/aha-own-link-audit-2026-11-03/audit.json').read_text())
with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
    records = {r['id']: r for r in csv.DictReader(f)}
students = defaultdict(list)
for r in records.values():
    for t in (r['advisor_ids'] or '').split(';'):
        if t.strip():
            students[t.strip()].append(r)
links = [x for x in audit if x['record_on_key'] and x['outcome'] in ('contradicted_lc', 'doubtful')]
lc = lc_records({x['lc'][0] for x in links if len(x['lc']) == 1}, '/mnt/e/lc-authorities')
items = []
for x in links:
    rec = records[x['record']]
    if x['outcome'] == 'contradicted_lc':
        if len(x['lc']) != 1:
            continue
        notes, affs, birth = lc[x['lc'][0]]
        found, _ = assess([rec], [], notes, affs, birth, x['advisor'])
        if found['title'] or found['degree'] or found['school'] or not found['other_school']:
            continue
    st = sorted(students[x['advisor_id']], key=lambda r: r['year'])
    items.append(dict(
        id=x['key'], supervisor=x['advisor'], key=x['key'], wikidata=x['wd'], lc=x['lc'], orcid=x['orcid'],
        linked_dissertation=dict(author=rec['dissertator'], university=rec['department'], year=rec['year'], title=rec['title']),
        facts_found=dict(education=x['education'], lc_doctorate_notes=x['lc_doctorate'][:4]),
        students_total=len(st),
        students=[dict(student=r['dissertator'], university=r['department'], year=r['year'], title=r['title'][:160])
                  for r in st[:6]]))
items.sort(key=lambda i: int(i['key'][2:]))
groups = [dict(id=f'g{n // 8 + 1:04d}', supervisors=items[n:n + 8]) for n in range(0, len(items), 8)]
(HERE / 'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=1) + '\n')
print(len(items), 'links in', len(groups), 'groups')
