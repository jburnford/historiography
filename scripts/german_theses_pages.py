#!/usr/bin/env python3
"""Browser download pages for the German History theses a script must not (or could not) fetch
(stage 4 of the German thesis harvest, 2026-11-14).

A record goes on the pages when it has a free link, is not held already, is not a habilitation,
and either its host is class C (hosts.csv), or the download job sent it to the browser
(manifest.csv status browser:* or failed:*), or its only link is a resolver that was not resolved.
Records still waiting in the download job's queue are left off; rerun this script after the job.

Pages: <fetch-dir>/download-pages/index.html plus one or more pages per repository (about 100
links a page). Each row: author, title, degree year, university, confidence, and the most direct
link known (a PDF link from the record or the job, else the landing page, else the resolver),
opening in a new tab. A checkbox per row ("done") is kept in the browser's localStorage.
A small CSV index (page, host, links) is written next to the tracked metadata table.

Usage:
  python3 -I scripts/german_theses_pages.py --table DIR/theses.csv.gz --hosts DIR/hosts.csv \
      --fetch-dir /mnt/e/german-theses-2026-11-14 --index-csv DIR/browser-pages-index.csv
"""
import argparse
import collections
import csv
import gzip
import html
import pathlib
import re
import urllib.parse

DROP_WIN = r'E:\german-theses-2026-11-14\browser-drop'
CONF = {'high': 0, 'medium': 1, 'low': 2}
STYLE = ('body{font:14px system-ui;max-width:72em;margin:2em auto;padding:0 1em}a:visited{color:#999}'
         'li{margin:.45em 0}li.done{opacity:.4}code{background:#eee;padding:0 .3em}.m{color:#666;font-size:12px}'
         '.low{color:#a50}.hdr{background:#f4f4f4;padding:.6em 1em;border-radius:6px}')
SCRIPT = ('<script>document.querySelectorAll("input[data-id]").forEach(function(b){var k="de-done-"+b.dataset.id;'
          'if(localStorage.getItem(k)){b.checked=true;b.parentNode.classList.add("done")}'
          'b.addEventListener("change",function(){if(b.checked){localStorage.setItem(k,"1");b.parentNode.classList.add("done")}'
          'else{localStorage.removeItem(k);b.parentNode.classList.remove("done")}})});</script>')


def host_of(u):
    return urllib.parse.urlparse(u).netloc.lower()


def slug(h):
    return re.sub(r'[^a-z0-9]+', '-', h.lower()).strip('-') or 'unknown'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--table', type=pathlib.Path, required=True)
    ap.add_argument('--hosts', type=pathlib.Path, required=True)
    ap.add_argument('--fetch-dir', type=pathlib.Path, required=True)
    ap.add_argument('--index-csv', type=pathlib.Path)
    ap.add_argument('--per-page', type=int, default=100)
    a = ap.parse_args()
    with gzip.open(a.table, 'rt', newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    with a.hosts.open(newline='') as f:
        hosts = {r['host']: r for r in csv.DictReader(f)}
    man = {}
    mp = a.fetch_dir / 'manifest.csv'
    if mp.exists():
        with mp.open(newline='') as f:
            for r in csv.DictReader(f):
                man[r['dnb_id']] = r  # last row wins
    pick = collections.defaultdict(list)
    reasons = collections.Counter()
    for r in rows:
        if not r['free_links'] or r['held_id'] or r['degree_type'] == 'habil' or r.get('duplicate_of'):
            continue
        m = man.get(r['dnb_id'])
        if m and m['status'] == 'downloaded':
            continue
        links = r['free_links'].split()
        host = r['host']
        if m and (m['status'].startswith(('browser:', 'failed:'))):
            why = m['status']
            url = m['url'] or m.get('landing_url') or links[0]
            if why == 'browser:no file link on landing page' and m.get('landing_url'):
                url = m['landing_url']
            h = m['host'] if m['host'] and m['host'] != 'resolver' else host_of(url)
        elif hosts.get(host, {}).get('class') == 'C':
            why, h = 'class C: ' + hosts[host].get('reason', ''), host
            url = (r['resolved_link'] or links[0])
        elif host.startswith('resolver:') and m is None:
            continue  # still in the job's queue
        else:
            continue  # class A, not yet tried
        if r['free_link_is_pdf'] and links and host_of(links[0]) == h:
            url = links[0]
        reasons[why[:50]] += 1
        pick[h or 'unknown'].append((r, url, why))

    out = a.fetch_dir / 'download-pages'
    out.mkdir(parents=True, exist_ok=True)
    index_rows, total = [], 0
    for h in sorted(pick, key=lambda h: (-len(pick[h]), h)):
        items = sorted(pick[h], key=lambda x: (CONF.get(x[0]['confidence'], 3), -int(x[0]['degree_year'])))
        for p in range(0, len(items), a.per_page):
            chunk = items[p:p + a.per_page]
            n = p // a.per_page + 1
            name = f'{slug(h)}-{n}.html'
            parts = [f'<!doctype html><meta charset="utf-8"><title>{html.escape(h)} {n}</title><style>{STYLE}</style>',
                     f'<p><a href="index.html">&larr; index</a></p><h1>{html.escape(h)}, page {n} ({len(chunk)} theses)</h1>',
                     f'<div class="hdr">Save each PDF into <code>{DROP_WIN}</code> (any file name works; the '
                     f'registration script matches by DNB id, URN or title page). Faster matching: save as '
                     f'<code>&lt;DNB id&gt;.pdf</code> (the id is shown in each row). Links open in a new tab; '
                     f'tick the box when done (kept in this browser only).</div>',
                     f'<ol start="{p + 1}">']
            for r, url, why in chunk:
                low = ' class="low"' if r['confidence'] == 'low' else ''
                parts.append(
                    f'<li><input type="checkbox" data-id="{r["dnb_id"]}"> '
                    f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(r["author"] or "?")} '
                    f'({r["degree_year"]})</a> &mdash; {html.escape(r["title"][:220])}'
                    f'<br><span class="m">{html.escape(r["university"][:80])} &middot; <span{low}>{r["confidence"]}</span>'
                    f' &middot; {r["degree_country"]} &middot; DNB <code>{r["dnb_id"]}</code> &middot; {html.escape(why[:70])}</span></li>')
            parts += ['</ol>', SCRIPT]
            (out / name).write_text('\n'.join(parts) + '\n', encoding='utf-8')
            index_rows.append({'page': name, 'host': h, 'class': hosts.get(h, {}).get('class', ''), 'links': len(chunk),
                               'high': sum(1 for x in chunk if x[0]['confidence'] == 'high')})
            total += len(chunk)
    parts = [f'<!doctype html><meta charset="utf-8"><title>German History theses to download</title><style>{STYLE}</style>',
             f'<h1>German History theses for browser download: {total} links on {len(index_rows)} pages</h1>',
             f'<div class="hdr">Save every PDF into <code>{DROP_WIN}</code>. Then run '
             '<code>python3 -I scripts/german_theses_register.py</code> in the historiography repo to match them to DNB '
             'records. Pages are grouped by repository, high-confidence History first; "low" marks archaeology, '
             'ancient world, theology or records with no History subject group.</div><ol>']
    for x in index_rows:
        parts.append(f'<li><a href="{x["page"]}">{html.escape(x["host"])} &ndash; {x["page"]}</a> '
                     f'<span class="m">{x["links"]} links, {x["high"]} high; host class {x["class"] or "?"}</span></li>')
    parts.append('</ol>')
    (out / 'index.html').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    if a.index_csv:
        with a.index_csv.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['page', 'host', 'class', 'links', 'high'])
            w.writeheader()
            w.writerows(index_rows)
    print(f'{total} links on {len(index_rows)} pages; {out / "index.html"}')
    for k, v in reasons.most_common():
        print(f'  {v}\t{k}')


if __name__ == '__main__':
    main()
