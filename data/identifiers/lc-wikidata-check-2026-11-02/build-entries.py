"""Entries for the Sol check of LC→Wikidata pairs that failed the automatic checks (2026-11-02).

Input: the check_failed rows of lc-wikidata-2026-11-01g/review-queue.json (a Wikidata item cites the key's LC
authority through P244, but the names, birth years, or LC's own Wikidata link disagree). Each entry carries
the key's own evidence (AHA dissertation records, Open Library author, atlas, ORCID, cited-name keys), the LC
authority's heading, and the item's labels and birth years. Writes entries.json here.

    python3 data/identifiers/lc-wikidata-check-2026-11-02/build-entries.py
"""
import csv
import json
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State  # noqa: E402

NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
state = State.load(ROOT / 'data/identifiers')
queue = [q for q in json.loads((ROOT / 'data/identifiers/lc-wikidata-2026-11-01g/review-queue.json').read_text())
         if q['kind'] == 'check_failed']
with (ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.csv').open(newline='', encoding='utf-8') as f:
    aha = {r['id']: r for r in csv.DictReader(f)}
db = duckdb.connect()
db.execute('CREATE TABLE want(lcid VARCHAR)')
db.executemany('INSERT INTO want VALUES (?)', [(q['lc'],) for q in queue])
lc_label = dict(db.execute(f"SELECT lcid, label FROM read_parquet('{NAMES}') JOIN want USING (lcid)").fetchall())
entries = []
for q in queue:
    k = q['key']
    anchors = state.keys[k]['anchors'] | state.members.get(k, set())
    evidence = {}
    for a in sorted(anchors):
        p, _, v = a.partition(':')
        if p == 'aha-phd' and v in aha:
            r = aha[v]
            evidence.setdefault('aha_dissertations', []).append(dict(dissertator=r['dissertator'], department=r['department'],
                                                                     year=r['year'], title=r['title']))
        elif p == 'orcid':
            evidence.setdefault('orcid', []).append(v)
        elif p in ('atlas', 'registry-v12') and 'atlas' in a:
            evidence.setdefault('atlas_person', []).append(a.split(':')[-1])
        elif 'ol:' in a:
            evidence.setdefault('open_library_author', []).append(a.split('ol:')[-1])
        elif p == 'diss-person':
            evidence.setdefault('cited_in_dissertations_as', []).append(v)
    entries.append(dict(id=f'{k}-{q["qid"]}', key=k, key_label=state.keys[k]['label'], key_evidence=evidence,
                        lc=dict(id=q['lc'], heading=lc_label.get(q['lc']), birth_in_lc=q['lc_birth'],
                                url=f'https://id.loc.gov/authorities/names/{q["lc"]}.html'),
                        wikidata=dict(qid=q['qid'], labels=q['item_labels'], births=q['item_births'],
                                      url=f'https://www.wikidata.org/wiki/{q["qid"]}'),
                        automatic_check_problems=q['problems']))
(HERE / 'entries.json').write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n')
print(len(entries))
