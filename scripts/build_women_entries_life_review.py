#!/usr/bin/env python3
"""Life-status records for the person entries added in revisions 1.237–1.238 (2026-11-02).

Each researcher (Sol 6.1 or Claude) wrote a life-status.json beside the entry draft, in several shapes. This script
normalises them into the life-review schema (scripts/historian_life_review.py) and writes:
- data/field-research/women-entries-life-review-2026-11-02/results.json, the hash-pinned report;
- the new rows in data/historian-life-review.json (historians layer) and data/theorist-life-review.json (theory layer).

Sources on blocked hosts or excluded routes are dropped. Status maps to deceased, living or unresolved: an undated
emeritus page is "living" only where the researcher recorded it so, and "unknown" becomes "unresolved". Birth years stay
in the review, because the site build withholds living people's birth years from the published copy.
"""
import hashlib, json, os, re, sys
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.source_hosts import blocked_url
from scripts.historian_life_review import validate_review

PKT = os.path.join(ROOT, 'data/extension-2026/timeline-women-entries-2026-11-01')
REPORT = 'data/field-research/women-entries-life-review-2026-11-02/results.json'
DAY = '2026-11-02'
EXCLUDED = re.compile(r'course|syllab|/~|moodle|canvas|blackboard|scribd|everand|academia\.edu|commons\.gc\.cuny|blogs\.law', re.I)


def life_file(pid):
    for p in (f'{PKT}/{pid}/life-status.json', f'{PKT}/_backfill/{pid}/life-status.json'):
        if os.path.exists(p):
            return json.load(open(p))
    return None


def sources_of(d):
    found = []
    def add(s, default_title='Source'):
        if not isinstance(s, dict):
            return
        url = s.get('url') or s.get('source_url')
        if not url:
            return
        support = s.get('support') or s.get('evidence') or s.get('basis') or s.get('note') or s.get('used_for') or ''
        found.append({'url': url, 'title': s.get('title') or default_title, 'locator': s.get('locator') or '',
                      'support': str(support)[:600], 'checked_on': s.get('checked_on') or d.get('checked_on') or DAY})
    for key in ('sources', 'evidence', 'status_sources', 'status_evidence'):
        for s in d.get(key) or []:
            add(s)
    for part in ('birth', 'death'):
        x = d.get(part)
        if isinstance(x, dict):
            for s in x.get('sources') or []:
                add(s)
            if x.get('source_url'):
                add({'url': x['source_url'], 'title': f'{part.title()} evidence', 'support': x.get('basis') or x.get('evidence') or ''})
    keep, seen = [], set()
    for s in found:
        host = urlsplit(s['url']).netloc
        if not host or blocked_url(s['url']) or EXCLUDED.search(s['url']) or s['url'] in seen:
            continue
        seen.add(s['url'])
        if s['title'] == 'Source':
            s['title'] = host
        if not s['support']:
            s['support'] = 'Identity and life evidence as recorded by the researcher.'
        if s['checked_on'] > DAY:
            s['checked_on'] = DAY
        keep.append(s)
    return keep


def row_for(pid, node, d):
    status = (d.get('status') or d.get('life_status') or 'unresolved').lower()
    status = {'unknown': 'unresolved', 'presumed_living': 'living', 'alive': 'living', 'dead': 'deceased'}.get(status, status)
    if status not in ('deceased', 'living', 'unresolved'):
        status = 'unresolved'
    birth, death = d.get('birth') if isinstance(d.get('birth'), dict) else {}, d.get('death') if isinstance(d.get('death'), dict) else {}
    by = d.get('birth_year') or birth.get('year')
    dy = d.get('death_year') or death.get('year')
    dd = d.get('death_date') or death.get('date')
    dp = d.get('death_precision') or death.get('precision')
    row = {'person_id': pid, 'label': node['label'], 'status': status,
           'death_year': int(dy) if status == 'deceased' and dy else None,
           'death_date': dd if status == 'deceased' and dd else None,
           'death_precision': dp if status == 'deceased' and dy else None,
           'checked_on': min(str(d.get('checked_on') or d.get('prepared') or d.get('status_as_of') or d.get('as_of') or DAY)[:10], DAY),
           'identity_rationale': (d.get('identity_rationale') or d.get('identity_resolution') or d.get('resolved_person')
                                  or f"The {node['label']} person entry added in revision 1.237; identity resolved by the cited works."),
           'sources': sources_of(d),
           'confidence': d.get('confidence') or 'medium',
           'limits': (d.get('limits') or d.get('status_basis') or d.get('life_status_basis') or
                      'Status from the researcher\'s cited pages; a missing death is not a living-status certification.')}
    if isinstance(row['identity_rationale'], (dict, list)):
        row['identity_rationale'] = json.dumps(row['identity_rationale'], ensure_ascii=False)[:600]
    if by:
        row['birth_year'] = int(by)
    if row['death_date'] and str(row['death_date'])[:4] != str(row['death_year']):
        row['death_date'], row['death_precision'] = None, 'year'
    return row


def main():
    graph = json.load(open(os.path.join(ROOT, 'historiography-1920-2000.json')))
    nodes = {n['id']: n for n in graph['nodes']}
    batch = json.load(open(f'{PKT}/release-1.237/batch.json'))
    rows = []
    for pid in batch['persons']:
        d = life_file(pid) or {}
        row = row_for(pid, nodes[pid], d)
        if not row['sources']:
            raise SystemExit(f'no permitted life source for {pid}')
        rows.append(row)
    os.makedirs(os.path.join(ROOT, os.path.dirname(REPORT)), exist_ok=True)
    report = {'prepared': DAY, 'revisions': ['1.237', '1.238'], 'method': __doc__.strip(), 'people': rows}
    with open(os.path.join(ROOT, REPORT), 'w') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    digest = hashlib.sha256(open(os.path.join(ROOT, REPORT), 'rb').read()).hexdigest()
    for path, layer in (('data/historian-life-review.json', 'historians'), ('data/theorist-life-review.json', 'intellectual_connections')):
        review = json.load(open(os.path.join(ROOT, path)))
        have = {r['person_id'] for r in review['people']}
        add = [r for r in rows if nodes[r['person_id']]['layer'] == layer and r['person_id'] not in have]
        review['people'] += add
        review['checked_on'] = max(review['checked_on'], DAY)
        review['source_report_sha256'][REPORT] = digest
        validate_review(review)
        with open(os.path.join(ROOT, path), 'w') as f:
            f.write(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
        print(path, '+', len(add))


if __name__ == '__main__':
    main()
