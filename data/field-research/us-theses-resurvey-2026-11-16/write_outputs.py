"""Write the lists, browser.html, restricted.csv, records.csv and summary.json from analyze.py's rows."""
import collections, csv, html, pickle, random
from common import *
from user_run_us import file_name

ROUTES = ['open', 'ai-excluded', 'ai-excluded-landing', 'browser', 'retry', 'restricted', 'held-pending', 'unknown']
BANDS = ['2010+', '1995-2009', '1980-1994', 'before 1980']


def delay_of(row):
    m = re.search(r'Crawl-delay (\d+)', row.get('host_class', ''))
    return m.group(1) if m else '10'


def main():
    rows = pickle.load((CACHE / 'rows.pkl').open('rb'))
    crawl = {}
    for p in (CACHE / 'robots').glob('*.json'):
        d = json.loads(p.read_text())
        m = re.search(r'(?im)^\s*crawl-delay\s*:\s*(\d+)', d.get('text', ''))
        crawl[p.stem] = m.group(1) if m else None
    lists = collections.defaultdict(list)
    # URLs the 2026-11-15 run already requested: 401 JSON = restricted file; saved = downloaded, not registered
    P1 = FIELD / 'aha-repository-links-2026-11-04/wget'
    E = Path('/mnt/e/historiography-dissertation-pdfs/aha-wget-2026-11-14')
    name2url = {x[1]: x[0] for f in ('open-urls.tsv', 'ai-excluded-urls.tsv')
                for x in csv.reader((P1 / f).open(), delimiter='\t') if x}
    seen401, seenok = set(), set()
    for x in csv.reader((E / 'fetch-log.tsv').open(), delimiter='\t'):
        u = name2url.get(x[3])
        if u and '401 [application/json' in x[1]:
            seen401.add(u)
        elif u and x[1] == 'ok':
            seenok.add(u)
    for r in rows:
        if r['url'] in seen401:
            r.update(route='restricted', reason='file restricted/embargoed (DSpace API answered 401 to the 2026-11-15 run)')
        elif r['url'] in seenok:
            r.update(route='held-pending', reason='downloaded 2026-11-15, not registered (failed register checks)')
    for r in rows:
        # pass-one links that were never requested or failed once: their own rerun list
        if r['route'] in ('open', 'ai-excluded') and r['pass_one'] and r['pass_one'] != 'downloaded' and \
                r['url'] and r['pass_one'].startswith(('never tried', 'failed')):
            r['route'] = 'retry'
    for r in rows:
        r['file'] = file_name(r) if r['url'] else ''
        if r['route'] in ('open', 'ai-excluded', 'ai-excluded-landing', 'retry') and not r['host_class'].startswith('retry'):
            d = str(max(int(crawl.get(r['host']) or 0), 10))
            lists[r['route']].append((r['url'], r['file'], r['host'], d))
    for route, fn in [('open', 'open-urls.tsv'), ('ai-excluded', 'ai-excluded-urls.tsv'),
                      ('ai-excluded-landing', 'ai-excluded-landing.tsv'), ('retry', 'retry-urls.tsv')]:
        seen = set()
        # interleave hosts so one host's delay overlaps another's request
        byhost = collections.defaultdict(list)
        for x in lists[route]:
            if x[0] not in seen:
                seen.add(x[0])
                byhost[x[2]].append(x)
        out = []
        while any(byhost.values()):
            for h in sorted(byhost):
                if byhost[h]:
                    out.append(byhost[h].pop(0))
        (OUT / fn).write_text(''.join('\t'.join(x) + '\n' for x in out))
    # browser.html
    br = [r for r in rows if r['route'] == 'browser']
    byh = collections.defaultdict(list)
    for r in br:
        byh[r['host']].append(r)
    parts = ['<!doctype html><meta charset="utf-8"><title>US History PhDs: browser downloads (2026-11-16)</title>',
             '<style>body{font:14px sans-serif;max-width:1100px;margin:auto}td{padding:2px 6px;vertical-align:top}'
             'code{font-size:12px}</style>',
             '<h1>US History PhDs not held: copies that need a person (2026-11-16)</h1>',
             '<p>Open each link in the browser and save the PDF into <code>E:\\historiography-dissertation-pdfs\\us-wget-2026-11-16\\browser\\</code> '
             'under the file name shown (it carries the AHA id, surname and year for the register script). Skip anything behind a login '
             'or embargo. Hosts are listed with why a script cannot be used.</p>']
    for h in sorted(byh, key=lambda h: -len(byh[h])):
        rs = byh[h]
        parts.append(f'<h2>{html.escape(h)} ({len(rs)})</h2><p><i>{html.escape(rs[0]["host_class"] or rs[0]["reason"])}</i></p><table>')
        for r in sorted(rs, key=lambda r: r['year']):
            parts.append(f'<tr><td>{r["year"]}</td><td>{html.escape(r["dissertator"])}</td><td><a href="{html.escape(r["url"])}">'
                         f'{html.escape(r["title"][:110])}</a></td><td><code>{html.escape(r["file"])}</code></td></tr>')
        parts.append('</table>')
    (OUT / 'browser.html').write_text('\n'.join(parts))
    # restricted.csv and records.csv
    cols = ['aha_id', 'year', 'band', 'institution', 'dissertator', 'title', 'route', 'reason', 'url', 'host', 'kind',
            'host_class', 'file', 'via', 'openalex_id', 'match_score', 'work_title', 'work_year', 'pass_one', 'other_copies']
    with (OUT / 'restricted.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['aha_id', 'year', 'institution', 'dissertator', 'title', 'reason', 'url'], extrasaction='ignore')
        w.writeheader()
        w.writerows(r for r in rows if r['route'] == 'restricted')
    with (OUT / 'records.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(r for r in rows if r['route'] != 'unknown' or r['pass_one'])
    # hosts.csv
    best = collections.Counter(r['host'] for r in rows if r['host'])
    anyc = collections.Counter()
    for r in rows:
        hs = {r['host']} | {urllib.parse.urlsplit(u).netloc for u in r['other_copies'].split()}
        for h in hs - {''}:
            anyc[h] += 1
    with (OUT / 'hosts.csv').open('w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['host', 'class', 'robots_evidence', 'crawl_delay', 'n_theses_best_route', 'n_theses_any_copy',
                     'robots_status', 'purpose_comments'])
        for h in sorted(anyc, key=lambda h: -anyc[h]):
            p = CACHE / 'robots' / (h + '.json')
            d = json.loads(p.read_text()) if p.exists() else {}
            hc = next((r['host_class'] for r in rows if r['host'] == h and r['host_class']), '')
            cls, ev = (hc.split(': ', 1) + [''])[:2] if hc else ('', '')
            if not cls:
                from analyze import host_class
                c = host_class('https://' + h + '/')
                cls, ev = c[0], c[1]
            comments = ' | '.join(l.strip('# ').strip() for l in (d.get('text') or '').splitlines()
                                  if l.startswith('#') and re.search(r'(?i)\b(ai|train|bot|crawl|llm|scrap|content.signal)', l))[:300]
            sig = '; '.join(sorted(set(re.findall(r'(?im)^\s*content-signal\s*:\s*(.+)$', d.get('text') or ''))))
            wr.writerow([h, cls, ev, crawl.get(h) or '', best[h], anyc[h], d.get('status', ''),
                         (('Content-Signal: ' + sig + ' | ') if sig else '') + comments])
    # summary
    tab = collections.Counter((r['route'], r['band']) for r in rows)
    reasons = collections.Counter(re.sub(r':.*', '', r['reason']) for r in rows if r['route'] == 'restricted')
    insts = collections.defaultdict(collections.Counter)
    for r in rows:
        insts[r['institution']][r['route']] += 1
    get = ('open', 'ai-excluded', 'ai-excluded-landing', 'retry')
    top = sorted(insts.items(), key=lambda kv: -sum(kv[1][x] for x in get))[:25]
    summary = {'unheld_us_aha_records': len(rows),
               'by_route_and_band': {rt: {b: tab[(rt, b)] for b in BANDS} for rt in ROUTES},
               'restricted_reasons': dict(reasons.most_common()),
               'lists': {k: len(v) for k, v in lists.items()},
               'browser_hosts': {h: len(v) for h, v in sorted(byh.items(), key=lambda kv: -len(kv[1]))},
               'top_institutions': {k: dict(v) for k, v in top},
               'unknown_by_institution': dict(collections.Counter(r['institution'] for r in rows if r['route'] == 'unknown').most_common(40))}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary['by_route_and_band'], indent=0))
    print(summary['restricted_reasons'])
    print(summary['lists'])


if __name__ == '__main__':
    main()
