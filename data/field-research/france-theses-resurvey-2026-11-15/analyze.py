"""Join the 2026-11-15 French re-survey pieces into lists (metadata only; no thesis file is requested here).

Inputs (E: cache = /mnt/e/france-theses-snapshot-2026-11-12):
  screen/history-screen.jsonl.gz      corrected History screen of the 2026-11-12 ABES snapshot (screen_snapshot.py)
  cache/buttons.jsonl                 theses.fr access buttons per NNT (thesesfr_buttons.py)
  cache/openalex-thesesfr.jsonl.gz    OpenAlex dissertations with a theses.fr location + their other copies
  ../france-theses-2026-10-30/{candidates.json,downloads.jsonl}, dissertation-citations-2026-10-11/dissertations.csv
  cache/held-hal-ids.json             HAL ids already downloaded by the 2026-10 BASE harvest
Robots files: fetched once per host today through scripts/user_run_download_lists.classify (cache redirected to
the E: folder; generic User-Agent, 1 request a second).
Writes in this folder: hosts.csv, open-urls.tsv, ai-excluded-urls.tsv, browser.html, restricted.csv,
records.csv (one row per thesis with its route), summary.json.
usage: python3 analyze.py
"""
import collections
import csv
import gzip
import html
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
E = Path('/mnt/e/france-theses-snapshot-2026-11-12')
sys.path.insert(0, str(ROOT / 'scripts'))
import user_run_download_lists as U  # noqa: E402

U.CACHE = E / 'cache' / 'robots'
OLD = ROOT / 'data/field-research/france-theses-2026-10-30'
OLD_SNAPSHOT_SCREEN = Path('/mnt/e/historiography-dissertation-pdfs/france-theses-2026-10-30/history-accessible.json')

# one HEAD per open host, 2026-11-16: these hand the file to a university login (CAS), i.e. an access
# restriction, not a robots question; their links are not listed anywhere
LOGIN_HOSTS = {'extranet.u-bordeaux-montaigne.fr': 'login (CAS) at intranet/sso.u-bordeaux-montaigne.fr',
               'scd-resnum.univ-lyon3.fr': 'login (CAS) at cas.univ-lyon3.fr'}
# item pages, not files (HEAD answered text/html): a person must find the file
LANDING_HOSTS = {'octaviana.fr', 'archive.bu.univ-nantes.fr'}
SKIP_HOSTS = ('sudoc.fr', 'doi.org', 'citeseerx', 'hdl.handle.net/10068', 'opengrey', 'chasse-aux-livres', 'worldcat',
              'books.google', 'theses.fr', 'europepmc', 'pubmed', 'semanticscholar', 'scholar.archive.org',
              'core.ac.uk', 'base-search', 'researchgate', 'academia.edu', 'scribd', 'dokumen')


def fold(s):
    s = unicodedata.normalize('NFKD', (s or '').replace('\u2019', "'")).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def tkey(s):
    return fold(re.sub(r'\(\.\.\.\)', '', s or ''))[:50]


def held_index():
    nnts, keys = set(), set()
    with open(ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv') as f:
        for r in csv.DictReader(f):
            if r['id'].startswith('thesesfr-'):
                nnts.add(r['id'][9:])
            for part in re.split(r' ; | / ', r['title'] or ''):
                k = tkey(part)
                if len(k) >= 25:
                    keys.add(k)
    return nnts, keys


def titles(d):
    t = d.get('titres') or {}
    return [v for v in t.values() if v]


def button_routes(b):
    """-> (open_urls[(url, kind)], restrictions[str], published_version_urls[str])"""
    opens, restr, pub = [], [], []
    for cat in (b or {}).get('categories') or []:
        subs = cat.get('sousCategories') or [{'libelle': '', 'boutons': cat.get('boutons') or []}]
        for sc in subs:
            for x in sc.get('boutons') or []:
                t, lib, url = x.get('typeAcces'), x.get('libelle') or '', x.get('url') or ''
                if t == 'ACCES_LIGNE':
                    opens.append(('https://theses.fr/api/v1/' + url, 'national deposit (incomplete version)'
                                  if 'incompl' in lib else 'national deposit'))
                elif t == 'ACCES_ESR':
                    restr.append('intranet' if 'Intranet' in lib else 'ESR-only')
                elif t == 'EMBARGO':
                    restr.append('embargo until ' + (x.get('dateFin') or '?'))
                elif t == 'CONFIDENTIALITE':
                    restr.append('confidential until ' + (x.get('dateFin') or '?'))
                elif t == 'SUDOC' and 'en ligne' in lib.lower() and 'achat' not in lib.lower() and url:
                    if 'remani' in lib:
                        pub.append(url)
                    else:
                        opens.append((url, 'reproduction listed by theses.fr'))
                elif t == 'SUDOC' and 'biblioth' in lib.lower() and 'éditeur' not in lib:
                    restr.append('library copy')
    return opens, restr, pub


HAL_REC = re.compile(r'^https?://([a-z0-9.-]*hal[a-z0-9.-]*|tel\.archives-ouvertes\.fr|[a-z0-9.-]*archives-ouvertes\.fr)/'
                     r'((?:tel|hal|halshs|dumas|cel)-\d+)(v\d+)?', re.I)


def openalex_copies(locs):
    out = []
    for src, landing, pdf, is_oa, version, lic in locs:
        for u in (pdf, landing):
            if not u:
                continue
            host = urlsplit(u).netloc.lower()
            if any(s in u for s in SKIP_HOSTS) or not host:
                continue
            m = HAL_REC.match(u)
            if m:
                if not (is_oa or pdf):
                    continue
                out.append((f'https://theses.hal.science/{m.group(2)}/document' if m.group(2).startswith('tel-')
                            else f'https://{m.group(1)}/{m.group(2)}/document', 'HAL', src or 'HAL'))
                break
            if is_oa or pdf:
                out.append((u, 'file' if u == pdf else 'landing', src or ''))
                break
    # de-duplicate by URL, HAL first
    seen, res = set(), []
    for x in sorted(out, key=lambda x: x[1] != 'HAL'):
        if x[0] not in seen:
            seen.add(x[0])
            res.append(x)
    return res


def main():
    held_nnts, held_keys = held_index()
    # HAL records already downloaded by the BASE harvest (downloads*.jsonl in dissertation-citations-2026-10-11)
    held_hal = set(json.loads((E / 'cache/held-hal-ids.json').read_text()))
    old_cands = {d['nnt'] for d in json.loads((OLD / 'candidates.json').read_text())}
    old_dl = {}
    for l in (OLD / 'downloads.jsonl').open():
        r = json.loads(l)
        old_dl[r['nnt']] = r
    old_screen = {d['nnt'] for d in json.loads(OLD_SNAPSHOT_SCREEN.read_text())}
    buttons = {}
    for l in (E / 'cache/buttons.jsonl').open():
        r = json.loads(l)
        buttons[r['nnt']] = r
    oa = collections.defaultdict(list)
    with gzip.open(E / 'cache/openalex-thesesfr.jsonl.gz', 'rt') as f:
        for l in f:
            try:
                w = json.loads(l)
            except Exception:
                continue
            for n in w['nnts']:
                oa[n].append(w)

    rows = []
    with gzip.open(E / 'screen/history-screen.jsonl.gz', 'rt') as f:
        for l in f:
            d = json.loads(l)
            nnt = d['nnt']
            if not nnt or len(nnt) < 10:
                continue
            ks = [tkey(t) for t in titles(d)]
            is_held = nnt in held_nnts or (old_dl.get(nnt, {}).get('status') == 'downloaded') or \
                any(len(k) >= 25 and k in held_keys for k in ks)
            yr = (d.get('date_soutenance') or '')[:4]
            origin = ('old candidate' if nnt in old_cands else 'old screen, held/deduped' if nnt in old_screen else
                      'after Jan 2024 snapshot' if yr >= '2024' else
                      'added by corrected screen' if d['screen'] != 'history' else
                      'accessible=non in snapshot' if d.get('accessible') != 'oui' else 'accessible=oui, not in old screen')
            rec = {'nnt': nnt, 'year': yr, 'screen': d['screen'], 'discipline': d.get('discipline'),
                   'accessible': d.get('accessible'), 'cas': d.get('cas'), 'held': is_held, 'origin': origin,
                   'title': (d.get('titres') or {}).get('fr') or (titles(d) or [''])[0],
                   'author': ' '.join(filter(None, [((d.get('auteurs') or [d.get('auteur') or {}]) or [{}])[0].get(k)
                                                     for k in ('prenom', 'nom')])),
                   'etab': ((d.get('etablissements_soutenance') or [{}])[0] or {}).get('nom', '')}
            b = buttons.get(nnt)
            rec['buttons_checked'] = bool(b and b.get('status') == 'ok' and b.get('buttons'))
            opens, restr, pub = button_routes(b.get('buttons') if rec['buttons_checked'] else None)
            if b and b.get('status') == 'robots_disallowed_page':
                restr.append('theses.fr robots disallows this page (takedown)')
            copies = []
            for u, kind in opens:
                m = HAL_REC.match(u)
                if m and '/file/' not in u:   # a HAL record page listed by theses.fr: its file is at <record>/document
                    u, kind = (f'https://theses.hal.science/{m.group(2)}/document' if m.group(2).startswith('tel-')
                               else f'https://{m.group(1)}/{m.group(2)}/document'), 'HAL'
                copies.append((u, kind, 'theses.fr button'))
            for w in oa.get(nnt, []):
                copies += [(u, k, 'OpenAlex: ' + s) for u, k, s in openalex_copies(w['locs'])]
            rec['copies'] = copies
            hal_ids = {m.group(2) for u, k, v in copies for m in [HAL_REC.match(u)] if m}
            if hal_ids & held_hal:
                rec['held'] = True
            rec['restrictions'] = sorted(set(restr))
            rec['published_version'] = pub
            rows.append(rec)

    # classify every host that appears
    hosts = collections.Counter()
    for r in rows:
        if r['held']:
            continue
        for u, kind, via in r['copies']:
            hosts[urlsplit(u).netloc.lower()] += 1
    cls = {}
    for h in sorted(hosts):
        path_examples = [urlsplit(u).path or '/' for r in rows for u, k, v in r['copies'] if urlsplit(u).netloc.lower() == h][:1]
        c = U.classify(h, path_examples or ['/'], [])
        if h == 'theses.fr':
            c['crawl_delay'] = c.get('crawl_delay') or '5'
        cls[h] = c

    rank = {'open': 0, 'ai-excluded': 1, 'browser': 2, 'retry': 3}
    for r in rows:
        best = None
        # where a HAL copy exists, the theses.fr national-deposit endpoint usually hands over to HAL (2026-10-30 run:
        # 380 of 417 files came from theses.hal.science); list the HAL file so no script is sent there by redirect
        has_hal = any(k == 'HAL' for u, k, v in r['copies'])
        for u, kind, via in r['copies']:
            if has_hal and kind.startswith('national deposit'):
                continue
            if urlsplit(u).netloc.lower() in LOGIN_HOSTS:
                r['restrictions'] = sorted(set(r['restrictions']) | {LOGIN_HOSTS[urlsplit(u).netloc.lower()]})
                continue
            if urlsplit(u).netloc.lower() in LANDING_HOSTS:
                kind = 'landing'
            h = urlsplit(u).netloc.lower()
            c = cls.get(h, {}).get('cls', 'retry')
            # a landing page is not a file: a person must find the file there
            route = c if kind != 'landing' else ('browser' if c in ('open', 'ai-excluded', 'browser') else c)
            key = (rank.get(route, 9), kind == 'national deposit (incomplete version)')
            if best is None or key < best[0]:
                best = (key, route, u, h, kind, via)
        if best:
            r.update(route=best[1], url=best[2], host=best[3], kind=best[4], via=best[5])
        elif r['buttons_checked'] or r['restrictions'] or any(urlsplit(u).netloc.lower() in LOGIN_HOSTS for u, k, v in r['copies']):
            r.update(route='restricted', url='', host='', kind='', via='')
        else:
            r.update(route='unknown', url='', host='', kind='', via='')

    todo = [r for r in rows if not r['held']]
    # --- outputs
    def name_for(r):
        a = re.sub(r'[^A-Za-z0-9]+', '-', unicodedata.normalize('NFKD', r['author']).encode('ascii', 'ignore').decode())
        return f"fr-{r['nnt']}-{a.strip('-')[:40]}.pdf"

    def delay(h):
        d = cls.get(h, {}).get('crawl_delay') or ''
        try:
            return str(max(10, int(float(d))))
        except ValueError:
            return '10'

    for route, fn in (('open', 'open-urls.tsv'), ('ai-excluded', 'ai-excluded-urls.tsv')):
        with (HERE / fn).open('w') as f:
            for r in sorted((r for r in todo if r['route'] == route), key=lambda r: (r['host'], r['nnt'])):
                f.write('\t'.join([r['url'], name_for(r), r['host'], delay(r['host'])]) + '\n')
    br = [r for r in todo if r['route'] in ('browser', 'retry')]
    by = collections.defaultdict(list)
    for r in br:
        by[r['host']].append(r)
    with (HERE / 'browser.html').open('w') as f:
        f.write('<!doctype html><meta charset="utf-8"><title>French History theses: browser links</title>\n'
                '<style>body{font:14px system-ui;max-width:64em;margin:2em auto}a:visited{color:#999}li{margin:.3em 0}</style>\n'
                f'<h1>French History doctorates not held: {len(br)} open copies that need a person</h1>\n'
                '<p>Open copies only (no ESR, intranet, embargo or library copy is listed). Save into '
                '<code>E:\\historiography-dissertation-pdfs\\france-resurvey-2026-11-15\\browser\\</code> with the NNT in the file name.</p>\n')
        for h, rs in sorted(by.items(), key=lambda x: -len(x[1])):
            f.write(f'<h2>{html.escape(h)} ({len(rs)}; {html.escape(cls.get(h, {}).get("rule", "")[:120])})</h2><ol>\n')
            for r in sorted(rs, key=lambda r: r['nnt']):
                f.write(f'<li><a href="{html.escape(r["url"])}" target="_blank">{html.escape(r["kind"] or "link")}</a> '
                        f'<a href="https://theses.fr/{r["nnt"]}" target="_blank">theses.fr</a> — {html.escape(r["author"])} '
                        f'({r["year"]}) {html.escape(r["title"][:160])} <small>[{r["nnt"]}]</small></li>\n')
            f.write('</ol>\n')
    with (HERE / 'restricted.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['nnt', 'year', 'etab', 'discipline', 'screen', 'origin', 'reason', 'published_version_url',
                    'author', 'title'])
        for r in sorted((r for r in todo if r['route'] in ('restricted', 'unknown')), key=lambda r: r['nnt']):
            reason = '; '.join(r['restrictions']) or ('not checked on theses.fr; no open copy in OpenAlex'
                                                       if r['route'] == 'unknown' else 'no access listed')
            w.writerow([r['nnt'], r['year'], r['etab'], r['discipline'], r['screen'], r['origin'], reason,
                        ' '.join(r['published_version']), r['author'], r['title']])
    with (HERE / 'records.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['nnt', 'year', 'screen', 'discipline', 'accessible', 'cas', 'held', 'origin', 'buttons_checked',
                    'route', 'host', 'kind', 'via', 'url', 'restrictions', 'other_copies', 'etab', 'author', 'title'])
        for r in sorted(rows, key=lambda r: r['nnt']):
            w.writerow([r['nnt'], r['year'], r['screen'], r['discipline'], r['accessible'], r['cas'], r['held'],
                        r['origin'], r['buttons_checked'], r['route'], r['host'], r['kind'], r['via'], r['url'],
                        '; '.join(r['restrictions']), ' '.join(u for u, k, v in r['copies'] if u != r['url']),
                        r['etab'], r['author'], r['title']])
    hn = collections.Counter(r['host'] for r in todo if r['host'])
    with (HERE / 'hosts.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['host', 'class', 'robots_evidence', 'crawl_delay', 'n_theses_best_route', 'n_theses_any_copy',
                    'robots_status', 'checked', 'purpose_comments', 'contacts'])
        for h in sorted(cls, key=lambda h: -hosts[h]):
            c = cls[h]
            w.writerow([h, c.get('cls'), c.get('rule'), c.get('crawl_delay'), hn.get(h, 0), hosts[h],
                        c.get('robots_status'), c.get('checked'), c.get('purpose_comments'), c.get('contacts')])
    summ = {
        'screen_rows': len(rows), 'held': sum(r['held'] for r in rows), 'not_held': len(todo),
        'route': collections.Counter(r['route'] for r in todo),
        'route_by_origin': {o: collections.Counter(r['route'] for r in todo if r['origin'] == o)
                            for o in sorted({r['origin'] for r in todo})},
        'route_by_screen': {s: collections.Counter(r['route'] for r in todo if r['screen'] == s)
                            for s in sorted({r['screen'] for r in todo})},
        'restriction_reasons': collections.Counter('; '.join(r['restrictions']) or 'none listed'
                                                   for r in todo if r['route'] == 'restricted'),
        'kind': collections.Counter((r['route'], r['kind'], r['via'].split(':')[0]) .__str__() for r in todo if r['route'] not in ('restricted', 'unknown')),
        'published_version_only': sum(1 for r in todo if r['route'] in ('restricted', 'unknown') and r['published_version']),
        'buttons_checked_not_held': sum(r['buttons_checked'] for r in todo),
        'hosts': {h: [cls[h].get('cls'), hn.get(h, 0)] for h in cls},
    }
    (HERE / 'summary.json').write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=dict))
    print(json.dumps({k: summ[k] for k in ('screen_rows', 'held', 'not_held', 'route', 'route_by_origin',
                                           'route_by_screen', 'published_version_only', 'buttons_checked_not_held')},
                     ensure_ascii=False, indent=1, default=dict))


if __name__ == '__main__':
    main()
