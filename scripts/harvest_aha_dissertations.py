#!/usr/bin/env python3
"""Harvest the AHA Directory of History Dissertations (public; no login) into local records.

The directory (https://secure.historians.org/members/services/cgi-bin/memberdll.dll/info?wrp=dissertations.htm)
covers about 61,600 dissertations, completed or in progress, at about 204 US and Canadian history
departments. Its search form refuses to list everything at once, so this script queries one award
year at a time (everything before 1950 as one query) through the form's own endpoint, 250 rows per
page, pausing between requests and identifying itself as research.

Raw pages are kept locally (raw/, gitignored); records.jsonl and records.csv are parsed from them.
A dissertation with two advisors appears as two rows sharing an id; they are merged. Resumable:
existing raw pages are not refetched.

    python3 scripts/harvest_aha_dissertations.py            # fetch what is missing, then parse
    python3 scripts/harvest_aha_dissertations.py --parse    # parse saved pages only
"""
import argparse
import csv
import datetime as dt
import html
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/field-research/aha-dissertations-2026-10-13'
RAW = OUT / 'raw'
URL = 'https://secure.historians.org/members/services/cgi-bin/utilities.dll/customlist'
START = 'https://secure.historians.org/members/services/cgi-bin/memberdll.dll/info?wrp=dissertations.htm'
AGENT = 'Mozilla/5.0 (compatible; historiography-research; contact jic823@usask.ca)'
PAGE = 250
FIRST_YEAR = 1950  # everything earlier is one query ('<1950')


def form(awarddate, start):
    return dict([('AWARDSTT', '|IN|Awarded|Nominated'), ('QNAME', 'SEARCHDISS'), ('WHP', 'SearchDiss_h.htm'),
                 ('WBP', 'SearchDiss.htm'), ('WNR', 'SearchDiss_norec.htm'), ('RANGE', f'{start}/{PAGE}'),
                 ('AWARDNAME', 'DISSERTATIONS'), ('NOMINATEDBYCD', '~'), ('C.LASTNAME', ''), ('RELATEDENTITYCODE', ''),
                 ('AWARDDESC', ''), ('AWARDDATE', awarddate), ('SORT', 'OWNERNAME,AWARDDATE,RELATIONSHIPTYPE')])


def fetch(awarddate, start, pause):
    data = urllib.parse.urlencode(form(awarddate, start)).encode()
    req = urllib.request.Request(URL, data=data, headers={'User-Agent': AGENT, 'Referer': START})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode('utf-8', errors='replace')
            time.sleep(pause)
            return body
        except Exception as e:  # network hiccup: back off and retry
            print('  retry', attempt + 1, e, flush=True)
            time.sleep(pause * (attempt + 2))
    raise RuntimeError(f'Failed {awarddate} {start}')


def total_of(page):
    m = re.search(r'There are\s*(?:<[^>]+>\s*)*([\d,]+)', page)
    return int(m.group(1).replace(',', '')) if m else 0


def harvest(pause, years):
    RAW.mkdir(parents=True, exist_ok=True)
    log = (OUT / 'harvest-log.jsonl').open('a')
    for key in years:
        start, total = 1, None
        while total is None or start <= total:
            path = RAW / f"{key.replace('<', 'lt')}-{start:06d}.html"
            if path.exists():
                page = path.read_text()
            else:
                page = fetch(key, start, pause)
                path.write_text(page)
                log.write(json.dumps(dict(awarddate=key, start=start, at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                                          bytes=len(page))) + '\n')
                log.flush()
            total = total_of(page) if total is None else total
            if start == 1:
                print(f'{key}: {total} rows', flush=True)
            start += PAGE
            if total == 0:
                break


ROW = re.compile(r'<tr class="(\d+)_row".*?</tr>\s*<script>(.*?)</script>', re.S)
FIELD = lambda label, s: (m.group(1).strip() if (m := re.search(r'<b>' + label + r':</b>\s*(.*?)<br', s, re.S)) else '')


def text(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def parse():
    recs = {}
    for path in sorted(RAW.glob('*.html')):
        key = path.name.split('-')[0].replace('lt', '<')
        for rid, body, script in [(m.group(1), m.group(0), m.group(2)) for m in ROW.finditer(path.read_text(errors='replace'))]:
            dept = re.search(r'<b>Department:</b>\s*<a href="[^"]*orgcd=(\d+)">(.*?)</a>', body, re.S)
            advs = [(a, text(n)) for a, n in re.findall(r'gotoUrl_init\((\d+),[^>]*>\s*<span class="\d+adv">(.*?)</span>', body, re.S)]
            status = re.search(r"if \('(\w+)' == \"Awarded\"", script)
            year = re.search(r"Dissertation completed, (\d{4})", script)
            r = recs.setdefault(rid, dict(id=rid, dissertator=text(FIELD('Dissertator', body)),
                department=text(dept.group(2)) if dept else text(FIELD('Department', body)),
                orgcd=dept.group(1) if dept else None, title=text(FIELD('Dissertation Title', body)).strip('"'),
                status='completed' if status and status.group(1) == 'Awarded' else 'in_progress',
                year=int(year.group(1)) if year else None, query=key, advisors=[]))
            for a in advs:
                if a not in [tuple(x) for x in r['advisors']]:
                    r['advisors'].append(list(a))
    rows = sorted(recs.values(), key=lambda r: (r['year'] or 0, r['dissertator']))
    with (OUT / 'records.jsonl').open('w') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with (OUT / 'records.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'dissertator', 'department', 'orgcd', 'title', 'status', 'year', 'advisors', 'advisor_ids'])
        for r in rows:
            w.writerow([r['id'], r['dissertator'], r['department'], r['orgcd'], r['title'], r['status'], r['year'],
                        '; '.join(n for _, n in r['advisors']), '; '.join(a for a, _ in r['advisors'])])
    print(f"{len(rows)} dissertations ({sum(r['status'] == 'completed' for r in rows)} completed); "
          f"{len({r['orgcd'] for r in rows})} departments")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--parse', action='store_true')
    ap.add_argument('--pause', type=float, default=3.0)
    ap.add_argument('--last-year', type=int, default=dt.date.today().year + 1)
    args = ap.parse_args()
    if not args.parse:
        harvest(args.pause, [f'<{FIRST_YEAR}'] + [str(y) for y in range(FIRST_YEAR, args.last_year + 1)])
    parse()


if __name__ == '__main__':
    main()
