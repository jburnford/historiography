"""Read-only candidate audit; no identity decisions or source modifications."""
import csv
import glob
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.dont_write_bytecode = True
sys.path.insert(0, '/home/jic823/hnet-reviews')
from ground_local import norm, split_authors

ROOT = Path('/home/jic823/hnet-reviews')
OUT = Path(__file__).resolve().parent
ground = ROOT / 'data/grounding'
records = {}
inputs = []
history = defaultdict(list)
for role in ('reviewer', 'author'):
    p = ground / f'{role}_grounding.csv'
    inputs.append(p)
    for row in csv.DictReader(p.open()):
        row.update(role=role, grounding_file=str(p))
        if row['status'] != 'matched':
            row['qid'] = ''
        records[role, row['name']] = row
for name in glob.glob(str(ground / 'mcp_results/*.csv')):
    p = Path(name)
    inputs.append(p)
    for row in csv.DictReader(p.open()):
        role = 'reviewer' if row['role'] == 'reviewer' else 'author'
        history[role, row['name']].append(dict(row, file=str(p)))
        if not row['decided_qid'] or row['decided_qid'] == 'none' or row['confidence'] == 'low':
            continue
        base = records.setdefault((role, row['name']), {'name': row['name'], 'role': role})
        base.update(qid=row['decided_qid'], status='mcp_' + row['confidence'],
                    matched_label=row['matched_label'], method='mcp',
                    reason=row['reason'], grounding_file=str(p))

c = duckdb.connect(str(ROOT / 'data/export/catalog.duckdb'), read_only=True)
freq = Counter()
reviewer_mismatch = []
author_mismatch = []
rows = c.execute('SELECT source,era,review_id,reviewer,reviewer_qid,book_author,author_qids,is_real FROM reviews').fetchall()
for source, era, rid, rev, rq, auth, aq, real in rows:
    if rev:
        expected = records.get(('reviewer',rev), {}).get('qid') or None
        if expected != (rq or None):
            reviewer_mismatch.append([source,era,rid,rev,rq,expected])
        if real:
            freq['reviewer',rev] += 1
    names = split_authors(auth) if auth else []
    expected = '|'.join(records.get(('author',n),{}).get('qid','') for n in names if records.get(('author',n),{}).get('qid')) or None
    if expected != (aq or None):
        author_mismatch.append([source,era,rid,auth,aq,expected])
    if real:
        freq.update(('author',n) for n in names)
c.close()
groups = defaultdict(list)
for key, n in freq.items():
    row = dict(records.get(key, {'role':key[0], 'name':key[1], 'qid':'', 'status':'missing'}))
    row['live_real_rows'] = n
    groups[norm(row['name'])].append(row)

conflicts, gaps = [], []
for name, members in groups.items():
    qids = sorted({r['qid'] for r in members if r['qid']})
    item = {'normalized_name':name, 'total_role_occurrences':sum(r['live_real_rows'] for r in members), 'qids':qids, 'members':members}
    if len(qids) > 1:
        conflicts.append(item)
    if qids and any(not r['qid'] for r in members):
        gaps.append(item)
for data in (conflicts, gaps):
    data.sort(key=lambda x:-x['total_role_occurrences'])
summary = {'catalog_rows':len(rows), 'is_real_rows':sum(bool(r[-1]) for r in rows),
           'live_role_name_pairs':len(freq), 'normalized_groups':len(groups),
           'multiple_qid_candidate_groups':len(conflicts), 'mixed_grounded_ungrounded_candidate_groups':len(gaps),
           'reviewer_reconstruction_mismatches':len(reviewer_mismatch), 'author_reconstruction_mismatches':len(author_mismatch)}
result = {'summary':summary, 'conflicts':conflicts, 'gaps':gaps,
          'reviewer_mismatch_examples':reviewer_mismatch[:20], 'author_mismatch_examples':author_mismatch[:20],
          'inputs':[{'path':str(p), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]}
(OUT/'candidates.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
flagged = {(r['role'], r['name']) for g in conflicts + gaps for r in g['members']}
(OUT/'effective-grounding.json').write_text(json.dumps([records[k] for k in sorted(flagged) if k in records], ensure_ascii=False, indent=2)+'\n')
print(json.dumps(summary, indent=2))
for label, data in [('CONFLICTS',conflicts),('GAPS',gaps)]:
    print(label)
    for item in data[:35]:
        print(item['normalized_name'],item['total_role_occurrences'], [(r['role'],r['name'],r['qid'],r.get('matched_label'),r['status'],r['live_real_rows']) for r in item['members']])
