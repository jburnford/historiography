"""Crossref article METADATA for history journals, all years, with or without deposited references (2026-11-11).

Why: the harvest of 2026-11-08 (scripts/crossref_references.py, /mnt/e/crossref-refs-2026-11-08) was built to collect
CITING articles: records with deposited references, published 2000 on. Matching the articles that dissertations cite
(scripts/key_cited_works_crossref.py) found that it lacks nearly everything before 2000 and most of the core journals
(no Past & Present or Journal of Social History; 42 AHR records). Matching needs only title, authors, year, journal and
DOI, which Crossref holds for these journals whatever the publisher deposited. Of 6,957 still-unmatched articles cited
by 3+ theses (2026-11-10), 4,109 are pre-2000.

Journals:
- the catalogue's journals with ISSNs (data/journal-catalogue/catalogue.csv), as crossref_references.py takes them;
- every `container` of still-unmatched cited ARTICLES in the dissertation corpus with 25+ strict citations in total
  (a containers CSV: container, cites, works; built from works.csv and the crosswalks), resolved to ISSNs through the
  catalogue (title and aliases, title_key equal) or else through Crossref's journals endpoint (`/journals?query=`),
  taking only journals whose Crossref title has the same title_key as the container (or the same key once the words
  journal / revue / review / of / the are dropped, two words or more). Abbreviations (ZPE, JRS), newspapers and
  reference works do not resolve and are reported.

Crossref conventions follow crossref_references.py (its User-Agent with the project mailto, polite pool; Crossref
answers with a limit of 10 requests a second and 3 concurrent): at most 3 workers, back-off on 429/5xx/timeouts
(Retry-After honoured), cursor paging, rows=1000, `select=` only the fields a matcher needs, no filter on references
or dates. Output: /mnt/e/crossref-meta-2026-11-11/ only.

    python3 scripts/crossref_metadata_harvest.py resolve --containers <containers25.csv>
    python3 scripts/crossref_metadata_harvest.py count            # per-journal totals, grand total, estimate
    python3 scripts/crossref_metadata_harvest.py harvest [--workers 3] [--max-records 6000000]

Files (in the output folder): journals.json (the list: id, title, issns, origin, containers), resolve-cache.jsonl
(one line per container queried), counts.json, works/<journal id>.jsonl.gz (one per journal, written as .part and
renamed when complete: the per-journal done marker; an interrupted journal restarts from its first page), harvest.log.
Re-running any phase skips what is done.
"""
import argparse
import concurrent.futures as cf
import csv
import gzip
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crossref_references import UA, CATALOGUE  # noqa: E402  (the project's Crossref identity; not redefined here)
from key_cited_works_openalex import title_key, ckey  # noqa: E402

OUT = Path('/mnt/e/crossref-meta-2026-11-11')
API = 'https://api.crossref.org'
SELECT = 'DOI,title,subtitle,author,issued,published-print,published-online,container-title,ISSN,type,volume,issue,page'
ROWS = 1000
LOCK = threading.Lock()


def log(msg):
    line = time.strftime('%Y-%m-%d %H:%M:%S ') + msg
    print(line, flush=True)
    with LOCK, open(OUT / 'harvest.log', 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def get(path, params, tries=8):
    """GET api.crossref.org<path>?params -> JSON, None on 404. Backs off on 429, 5xx and network errors."""
    url = API + path + '?' + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code not in (429, 500, 502, 503, 504):
                raise
            wait = e.headers.get('Retry-After') if e.headers else None
            wait = float(wait) if wait and wait.replace('.', '').isdigit() else min(120, 5 * 2 ** i)
            log(f'HTTP {e.code} on {path}; waiting {wait:.0f}s (try {i + 1})')
            time.sleep(wait)
        except Exception as e:                        # timeouts, resets, truncated JSON
            wait = min(120, 5 * 2 ** i)
            log(f'{type(e).__name__} on {path}; waiting {wait}s (try {i + 1})')
            time.sleep(wait)
    raise RuntimeError(f'gave up on {url}')


def catalogue():
    out = []
    for r in csv.DictReader(open(CATALOGUE, encoding='utf-8')):
        issns = [x.strip().upper() for x in r['issns'].split('|') if x.strip()]
        names = [r['title']] + [x.strip() for x in (r['aliases'] or '').split('|') if x.strip()]
        out.append(dict(id=r['id'], title=r['title'], issns=issns, names=names))
    return out


KEEP_DROP = {'the', 'of', 'and', 'for', 'de', 'la', 'des', 'et', 'du', 'in', 'on', 'a', 'an', 's', 'l', 'd'}


def ckey2(s):
    """Loose journal key: title_key words without articles and particles, two words or more. Unlike the OpenAlex
    matcher's ckey it keeps 'journal', 'review' and 'revue' (first run, 2026-11-11: ckey made 'Women's History Review'
    and 'Journal of Women's History' one key, 'women history')."""
    k = ' '.join(w for w in title_key(re.sub(r"['’‘ʼ]", ' ', s or '')).split() if w not in KEEP_DROP)
    return k if len(k.split()) >= 2 else ''


def title_ok(c, t):
    """Crossref journal title t names container c: same title_key or loose key, or t is c followed by more words
    ('Historical Methods A Journal of Quantitative and Interdisciplinary History', 'Environment and Planning A Economy
    and Space', 'Estudos Históricos (Rio de Janeiro)'; container of two words or more)."""
    tk, ck, it = title_key(c), ckey2(c), title_key(t)
    return it == tk or (ck and ckey2(t) == ck) or (len(tk.split()) >= 2 and it.startswith(tk + ' '))


LOOSE_DROP = {'the', 'and', 'of', 'a', 'an', 'le', 'la', 'les', 'de', 'des', 'du', 'et', 'el', 'los', 'las', 'y', 'e',
              'do', 'da', 'dos', 'das', 'der', 'die', 'das', 'und', 'für', 'il', 'di', 'del', 'della'}


def loose_words(c):
    import unicodedata
    t = unicodedata.normalize('NFKD', re.sub(r"['’‘ʼ&]", ' ', c)).encode('ascii', 'ignore').decode().lower()
    w = [x for x in re.sub(r'[^a-z0-9 ]+', ' ', t).split() if x not in LOOSE_DROP and len(x) > 2]
    return ' '.join(w)


def cmd_resolve(a):
    cat = catalogue()
    by_tk, by_ck = {}, {}
    for j in cat:
        if not j['issns']:
            continue
        for n in j['names']:
            if title_key(n):
                by_tk.setdefault(title_key(n), set()).add(j['id'])
            if ckey2(n):
                by_ck.setdefault(ckey2(n), set()).add(j['id'])
    journals = {j['id']: dict(id=j['id'], title=j['title'], issns=j['issns'], origin='catalogue', containers=[],
                              container_cites=0) for j in cat if j['issns']}
    issn_owner = {i: j['id'] for j in journals.values() for i in j['issns']}
    cache_f = OUT / 'resolve-cache.jsonl'
    cache = {}
    if cache_f.exists():
        for line in open(cache_f, encoding='utf-8'):
            d = json.loads(line)
            cache[d['container']] = d['items']
    rows = list(csv.DictReader(open(a.containers, encoding='utf-8')))
    todo = []
    status = {}
    for r in rows:
        c = r['container']
        hit = by_tk.get(title_key(c)) or by_ck.get(ckey2(c))
        if hit:
            status[c] = ('catalogue', sorted(hit))
        elif len(title_key(c)) < 3:
            status[c] = ('unresolved_too_short', [])
        elif c not in cache:
            todo.append(c)

    def query(c):
        # second form ('2|' + container): Crossref's journal query wants every word, so 'Journal of Imperial and
        # Commonwealth History' finds nothing where the title has '&', 'The American Economic Review' nothing where
        # it lacks 'The', and curly apostrophes ('Revue d’histoire') nothing; the second form drops those words
        q = loose_words(c[2:]) if c.startswith('2|') else c
        d = get('/journals', dict(query=q, rows=10)) if q else None
        items = [dict(title=it.get('title'), issns=sorted({x.upper() for x in it.get('ISSN') or []}),
                      total=(it.get('counts') or {}).get('total-dois')) for it in (d['message']['items'] if d else [])]
        return c, items

    def accept(c, keys=None):
        keys = keys or (c, '2|' + c)
        return [it for k in keys for it in cache.get(k, []) if it['issns'] and it['title'] and title_ok(c, it['title'])]

    for rnd in (1, 2):
        if rnd == 2:
            todo = ['2|' + r['container'] for r in rows if r['container'] not in status
                    and not accept(r['container']) and '2|' + r['container'] not in cache]
        with cf.ThreadPoolExecutor(a.workers) as ex, open(cache_f, 'a', encoding='utf-8') as fh:
            for i, (c, items) in enumerate(ex.map(query, todo)):
                cache[c] = items
                fh.write(json.dumps(dict(container=c, items=items), ensure_ascii=False) + '\n')
                if i % 100 == 0:
                    log(f'resolve round {rnd}: {i}/{len(todo)} queried')
    # catalogue journals whose catalogue ISSNs give no Crossref records (Journal of Women's History 1042-7961, Kritika,
    # Bulletin of the History of Medicine ...): look the title up and harvest under the ISSNs Crossref uses
    counts_f = OUT / 'counts.json'
    zero = [j for j in journals.values() if j['origin'] == 'catalogue'
            and json.loads(counts_f.read_text()).get(j['id'], {}).get('total', 1) == 0] if counts_f.exists() else []
    todo = [k for j in zero for k in ('cat|' + j['title'], '2|cat|' + j['title']) if k not in cache]
    with cf.ThreadPoolExecutor(a.workers) as ex, open(cache_f, 'a', encoding='utf-8') as fh:
        for c, items in ex.map(lambda k: (k, query(k[4:] if k.startswith('cat|') else '2|' + k[6:])[1]), todo):
            cache[c] = items
            fh.write(json.dumps(dict(container=c, items=items), ensure_ascii=False) + '\n')
    retitled = {}
    for j in zero:
        for it in accept(j['title'], ('cat|' + j['title'], '2|cat|' + j['title']))[:3]:
            if any(i in issn_owner for i in it['issns']):
                continue
            nid = 'cr_' + it['issns'][0]
            journals[nid] = dict(id=nid, title=it['title'], issns=it['issns'], origin='catalogue_retitled',
                                 replaces=j['id'], containers=[], container_cites=0)
            for i in it['issns']:
                issn_owner[i] = nid
            retitled.setdefault(j['id'], []).append(nid)
    for c, (how, ids) in list(status.items()):
        if how == 'catalogue' and any(i in retitled for i in ids):
            status[c] = (how, sorted(set(ids) | {n for i in ids for n in retitled.get(i, [])}))
    for r in rows:
        c = r['container']
        if c in status:
            continue
        ok = accept(c)
        if not ok:
            status[c] = ('unresolved', [])
            continue
        ids = []
        for it in ok[:5]:                             # several journals of one name ('Historia'): all of them
            owner = next((issn_owner[i] for i in it['issns'] if i in issn_owner), None)
            if not owner:
                owner = 'cr_' + it['issns'][0]
                journals[owner] = dict(id=owner, title=it['title'], issns=it['issns'], origin='container',
                                       containers=[], container_cites=0)
                for i in it['issns']:
                    issn_owner[i] = owner
            ids.append(owner)
        status[c] = ('crossref', sorted(set(ids)))
    tally = {}
    for r in rows:
        how, ids = status[r['container']]
        tally.setdefault(how, [0, 0])
        tally[how][0] += 1
        tally[how][1] += int(r['cites'])
        for jid in ids:
            journals[jid]['containers'].append(r['container'])
            journals[jid]['container_cites'] += int(r['cites'])
    unresolved = [dict(container=r['container'], cites=int(r['cites']), status=status[r['container']][0])
                  for r in rows if not status[r['container']][1]]
    res = dict(containers=len(rows), by_status={k: dict(containers=v[0], cites=v[1]) for k, v in tally.items()},
               journals=len(journals), catalogue_journals=sum(1 for j in journals.values() if j['origin'] == 'catalogue'),
               container_only_journals=sum(1 for j in journals.values() if j['origin'] == 'container'),
               catalogue_retitled=sum(1 for j in journals.values() if j['origin'] == 'catalogue_retitled'),
               zero_count_catalogue_journals=len(zero),
               catalogue_journals_hit_by_containers=sum(1 for j in journals.values()
                                                       if j['origin'] == 'catalogue' and j['containers']))
    (OUT / 'journals.json').write_text(json.dumps(dict(summary=res, journals=list(journals.values())), indent=0,
                                                  ensure_ascii=False))
    (OUT / 'unresolved-containers.json').write_text(json.dumps(unresolved, indent=0, ensure_ascii=False))
    log('resolve: ' + json.dumps(res))


def load_journals():
    return json.loads((OUT / 'journals.json').read_text())['journals']


def cmd_count(a):
    js = load_journals()
    cf_ = OUT / 'counts.json'
    counts = json.loads(cf_.read_text()) if cf_.exists() else {}

    def one(j):
        per = {}
        for issn in j['issns']:
            d = get(f'/journals/{issn}/works', dict(rows=0))
            per[issn] = d['message']['total-results'] if d else 0
        best = max(per.items(), key=lambda x: x[1]) if per else (None, 0)
        return j['id'], dict(title=j['title'], issn=best[0], total=best[1], per_issn=per)

    todo = [j for j in js if j['id'] not in counts]
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for i, (jid, c) in enumerate(ex.map(one, todo)):
            counts[jid] = c
            if i % 50 == 0:
                cf_.write_text(json.dumps(counts, indent=0, ensure_ascii=False))
                log(f'count: {i}/{len(todo)}')
    cf_.write_text(json.dumps(counts, indent=0, ensure_ascii=False))
    tot = sum(v['total'] for v in counts.values())
    reqs = sum(-(-v['total'] // ROWS) + 1 for v in counts.values() if v['total'])
    log(f"count: {len(counts)} journals, {sum(1 for v in counts.values() if v['total'])} with records, {tot:,} records; "
        f"~{reqs:,} requests; at ~2.5 s a page and 3 workers ~{reqs * 2.5 / 3 / 3600:.1f} h; "
        f"~{tot * 330 / 1e9:.1f} GB gzip (330 B/record est.)")
    for v in sorted(counts.values(), key=lambda v: -v['total'])[:40]:
        print(f"{v['total']:9,d}  {v['issn']}  {v['title']}")


def cmd_harvest(a):
    js = {j['id']: j for j in load_journals()}
    counts = {jid: v for jid, v in json.loads((OUT / 'counts.json').read_text()).items() if jid in js}  # current list
    # 2026-11-11: the full list came to 8.59M records, over the 6M budget, because container resolution brought in
    # general science and medical journals (The Lancet 475k records for 297 unmatched citations, Nature, BMJ, PLOS One,
    # JAMA ...). Journals that are in the list only as a container (not in the catalogue), with more than --big records
    # and more than --ratio records per unmatched corpus citation of that container, are left out (excluded.json).
    excl = {jid: dict(title=js[jid]['title'], total=v['total'], container_cites=js[jid]['container_cites'])
            for jid, v in counts.items() if js[jid]['origin'] == 'container' and v['total'] > a.big
            and v['total'] / max(js[jid]['container_cites'], 1) > a.ratio}
    (OUT / 'excluded.json').write_text(json.dumps(dict(rule=dict(big=a.big, ratio=a.ratio), journals=excl), indent=0,
                                                  ensure_ascii=False))
    counts = {jid: v for jid, v in counts.items() if jid not in excl}
    tot = sum(v['total'] for v in counts.values())
    log(f'harvest: {len(excl)} journals excluded by size rule ({sum(e["total"] for e in excl.values()):,} records, '
        f'{sum(e["container_cites"] for e in excl.values()):,} container citations); {tot:,} records in scope')
    if tot > a.max_records:
        sys.exit(f'{tot:,} records exceed --max-records {a.max_records:,}: not harvesting')
    wd = OUT / 'works'
    wd.mkdir(exist_ok=True)
    order = sorted((jid for jid, v in counts.items() if v['total']), key=lambda jid: counts[jid]['total'])
    if a.only:
        order = [jid for jid in order if jid in set(a.only.split(','))]

    def one(jid):
        dest = wd / f'{jid}.jsonl.gz'
        if dest.exists():
            return jid, None
        tmp = wd / f'{jid}.jsonl.part'
        issn = counts[jid]['issn']
        n, cursor = 0, '*'
        with gzip.open(tmp, 'wt', encoding='utf-8') as f:
            while True:
                d = get(f'/journals/{issn}/works', dict(rows=ROWS, select=SELECT, cursor=cursor))
                items = d['message']['items'] if d else []
                for it in items:
                    it['_journal'] = jid
                    f.write(json.dumps(it, ensure_ascii=False) + '\n')
                n += len(items)
                cursor = d['message'].get('next-cursor') if d else None
                if not items or not cursor:
                    break
        os.replace(tmp, dest)
        return jid, n

    t0, done, recs = time.time(), 0, 0
    log(f'harvest: {len(order)} journals to check, {tot:,} records expected')
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, jid): jid for jid in order}
        for fu in cf.as_completed(futs):
            jid = futs[fu]
            done += 1
            try:
                _, n = fu.result()
            except Exception as e:                    # leave the .part; a re-run starts this journal again
                log(f'FAILED {jid} {js[jid]["title"]}: {e}')
                continue
            if n is not None:
                recs += n
                log(f'{done}/{len(order)} {n:7d} of {counts[jid]["total"]:7d}  {js[jid]["title"][:60]}  '
                    f'({recs:,} records this run, {time.time() - t0:.0f}s)')
    log(f'harvest: finished this run, {recs:,} records in {time.time() - t0:.0f}s')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('phase', choices=('resolve', 'count', 'harvest'))
    ap.add_argument('--containers', help='CSV of container, cites, works (resolve)')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--max-records', type=int, default=6_000_000)
    ap.add_argument('--big', type=int, default=50_000, help='size rule: records (container-only journals)')
    ap.add_argument('--ratio', type=float, default=1000, help='size rule: records per unmatched container citation')
    ap.add_argument('--only', help='comma-separated journal ids (harvest pilot)')
    a = ap.parse_args()
    a.workers = min(a.workers, 3)
    OUT.mkdir(exist_ok=True)
    {'resolve': cmd_resolve, 'count': cmd_count, 'harvest': cmd_harvest}[a.phase](a)


if __name__ == '__main__':
    main()
