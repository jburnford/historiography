"""Combine routes, choose one copy per unheld AHA record, class hosts, write the lists (2026-11-16).

Inputs (all metadata): AHA universe (common.universe), OpenAlex institution listings (harvest_openalex.py),
OpenAlex per-record title search (search_openalex.py), the pass-one links and the user's 2026-11-14 fetch log.
Steps that touch the network: robots.txt per host, the handle/DOI proxy API, and landing pages on OPEN hosts
(resolve.py). Run:  python3 analyze.py [--no-resolve]"""
import argparse, collections, csv, glob, html, random
from common import *
from match import score, link, open_links
from harvest_openalex import inst_ids
import resolve

P1 = FIELD / 'aha-repository-links-2026-11-04'
FETCH = Path('/mnt/e/historiography-dissertation-pdfs/aha-wget-2026-11-14')
# hosts that refused or challenged scripted clients when a file was requested (pass one, 2026-11-04/05/15, and the
# single HEAD of this survey); these stay browser whatever robots.txt says
KNOWN_BROWSER = {
    'deepblue.lib.umich.edu': '403 to scripted file requests (2026-11-05)',
    'd.lib.msu.edu': 'bot challenge (2026-11-05)',
    'arch.library.northwestern.edu': '401/403 to scripts (2026-11-04)',
    'repositories.lib.utexas.edu': '401/403 to scripts (2026-11-04); robots.txt 403 (2026-11-16)',
    'www.ideals.illinois.edu': '401/403 to scripts (2026-11-04); robots.txt 403 (2026-11-16)',
    'etd.ohiolink.edu': 'robots.txt Disallow: / (OhioLINK)', 'rave.ohiolink.edu': 'redirects to etd.ohiolink.edu (Disallow: /)',
    'scholarshare.temple.edu': 'robots-disallowed file paths (2026-11-05)', 'hammer.purdue.edu': 'robots-disallowed (2026-11-05)',
    'docs.lib.purdue.edu': 'robots-disallowed (2026-11-05)', 'researchrepository.wvu.edu': 'robots-disallowed (2026-11-05)',
    'ecommons.cornell.edu': 'CloudFront 429 (retry-after 900) on the first file request, 2026-11-15 run and 2026-11-16 HEAD',
    'academicworks.cuny.edu': 'Cloudflare challenge ("Just a moment...") to scripts, 2026-11-15 run',
    'digitalcommons.fiu.edu': '202 JavaScript challenge to scripts, 2026-11-15 run',
    'nrs.harvard.edu': 'robots.txt disallows * (URN resolver; DASH copy used instead)',
    # one HEAD per open host, 2026-11-16 (head_check.py)
    'repository.lsu.edu': '403 to a scripted HEAD of a file link (bepress), 2026-11-16',
    'digitalcommons.unl.edu': '403 to a scripted HEAD of a file link (bepress), 2026-11-16',
    'ecommons.luc.edu': '403 to a scripted HEAD of a file link (bepress), 2026-11-16',
    'scholars.unh.edu': '403 to a scripted HEAD of a file link (bepress), 2026-11-16',
    'epublications.marquette.edu': '403 to a scripted HEAD of a file link (bepress), 2026-11-16',
    'research.library.fordham.edu': '403 to a scripted HEAD of a file link (bepress), 2026-11-16',
    'conservancy.umn.edu': '403 to a scripted HEAD of a file link, 2026-11-16',
    'dash.harvard.edu': '429 on the first scripted HEAD of a file link, 2026-11-16',
    'dspace.mit.edu': '429 on the first scripted HEAD of a file link, 2026-11-16',
    'scholarworks.umass.edu': 'old bepress file link redirects to the home page (moved platform), 2026-11-16 HEAD',
    'lib.dr.iastate.edu': 'old link redirects to a landing page, not a file, 2026-11-16 HEAD',
}
# repository hosts (or handle prefixes) whose institution OpenAlex does not record; checked by hand 2026-11-16
EXTRA_HOSTS = {'hdl.handle.net/2142': 'Univ. of Illinois, Urbana-Champaign', 'www.ideals.illinois.edu': 'Univ. of Illinois, Urbana-Champaign',
               'docs.lib.purdue.edu': 'Purdue Univ.', 'hammer.purdue.edu': 'Purdue Univ.', 'scholars.unh.edu': 'Univ. of New Hampshire, Durham',
               'aquila.usm.edu': 'Univ. of Southern Mississippi', 'scholarlyrepository.miami.edu': 'Univ. of Miami',
               'indigo.uic.edu': 'Univ. of Illinois, Chicago', 'hdl.handle.net/2027.42': 'Univ. of Michigan',
               'deepblue.lib.umich.edu': 'Univ. of Michigan', 'escholarship.org': None,
               'repositories.lib.utexas.edu': 'Univ. of Texas, Austin', 'hdl.handle.net/2152': 'Univ. of Texas, Austin',
               'libraetd.lib.virginia.edu': 'Univ. of Virginia', 'dash.harvard.edu': 'Harvard Univ.',
               'knowledge.uchicago.edu': 'Univ. of Chicago', 'academiccommons.columbia.edu': 'Columbia Univ.',
               'repository.library.brown.edu': 'Brown Univ.', 'cdr.lib.unc.edu': 'Univ. of North Carolina, Chapel Hill'}
EXTRA_HOSTS = {k: v for k, v in EXTRA_HOSTS.items() if v}
FILE_PAT = re.compile(r'(\.pdf($|\?)|/bitstream/|/bitstreams/[^/]+/download|/core/bitstreams/[^/]+/content|viewcontent\.cgi|'
                      r'/files/[^/]+\.pdf|/download(/|$|\?)|/content$|send_file|/datastream/|/files/original/)', re.I)
BANDS = [(2010, 9999, '2010+'), (1995, 2009, '1995-2009'), (1980, 1994, '1980-1994'), (0, 1979, 'before 1980')]


def band(y):
    y = int(y)
    return next(b for lo, hi, b in BANDS if lo <= y <= hi)


def host_of(u):
    return urllib.parse.urlsplit(u).netloc.lower()


_class = {}


def host_class(url):
    h = host_of(url)
    path = urllib.parse.urlsplit(url).path or '/'
    key = (h, path.split('/')[1] if '/' in path else '')
    if key not in _class:
        if h in KNOWN_BROWSER:
            _class[key] = ('browser', KNOWN_BROWSER[h], None)
        else:
            _class[key] = classify(h, path)
    return _class[key]


def pass_one():
    """aha id -> pass-one link + what happened to it in the user's 2026-11-14/15 run."""
    url2id = {}
    for f in ('matches.csv', 'oai-matches.csv', 'openalex-source-matches.csv'):
        for r in csv.DictReader((P1 / f).open(newline='')):
            for u in (r.get('pdf_url'), r.get('landing_url')):
                if u:
                    url2id.setdefault(html.unescape(u), r['id'])
    lists = {}
    for f in ('open-urls.tsv', 'ai-excluded-urls.tsv', 'browser-urls.tsv'):
        for row in csv.reader((P1 / 'wget' / f).open(), delimiter='\t'):
            if row:
                lists[row[1]] = (f.split('-urls')[0], row[0], row[2])
    log = {}
    if (FETCH / 'fetch-log.tsv').exists():
        for row in csv.reader((FETCH / 'fetch-log.tsv').open(), delimiter='\t'):
            log[row[3]] = row[1]
    back = set()
    if (FETCH / 'back-to-browser.tsv').exists():
        back = {row[1] for row in csv.reader((FETCH / 'back-to-browser.tsv').open(), delimiter='\t') if len(row) > 1}
    files = set(p.name for p in FETCH.glob('*.pdf')) if FETCH.exists() else set()
    out = {}
    for name, (cls, url, host) in lists.items():
        aid = url2id.get(url)
        if not aid:
            continue
        if name in files:
            st = 'downloaded'
        elif name in log:
            st = 'failed: ' + log[name].replace('failed:', '').strip()
        elif name in back:
            st = 'never tried (host dropped by fetch.sh)'
        else:
            st = 'not run (browser list)' if cls == 'browser' else 'never tried'
        out[aid] = {'list': cls, 'url': url, 'host': host, 'name': name, 'status': st}
    return out


OAI_OPEN = {'repository.upenn.edu': 'Univ. of Pennsylvania', 'repository.arizona.edu': 'Univ. of Arizona',
            'scholarspace.manoa.hawaii.edu': 'Univ. of Hawaii, Manoa', 'shareok.org': 'Univ. of Oklahoma'}


def oai_works(host):
    import xml.etree.ElementTree as ET
    sys.path.insert(0, str(ROOT / 'scripts'))
    from user_run_canada import flatten, direct_dspace
    O = '{http://www.openarchives.org/OAI/2.0/}'
    out = []
    for page in sorted((CACHE / 'oai' / host).glob('records-*/page-*.xml')):
        root = ET.fromstring(page.read_text())
        for rec in root.iter(O + 'record'):
            h, md = rec.find(O + 'header'), rec.find(O + 'metadata')
            if h is None or h.get('status') == 'deleted' or md is None or not len(md):
                continue
            m, bits = flatten(md[0])
            files = [direct_dspace(d.get('url'), host) or d.get('url') for b, d in bits
                     if b == 'ORIGINAL' and (d.get('format') or '').endswith('pdf') and d.get('url')]
            landing = next((v for v in m.get('dc.identifier.uri', []) if v.startswith('http')), '')
            yr = re.findall(r'(1[89]\d\d|20\d\d)', ' '.join(m.get('dc.date.issued', [])))
            out.append({'id': 'oai:' + h.findtext(O + 'identifier'), 'title': (m.get('dc.title') or [''])[0],
                        'authors': m.get('dc.contributor.author') or m.get('dc.creator') or [],
                        'year': int(yr[0]) if yr else None,
                        'locations': [{'pdf': f, 'landing': None, 'oa': True, 'source': host, 'source_type': 'repository'} for f in files[:1]]
                        + ([{'pdf': None, 'landing': landing, 'oa': None, 'source': host, 'source_type': 'repository'}] if landing else [])})
    return out


def institution_ok(rec, work, I, hostmap):
    if I and (I in (work.get('aff') or []) or any(I in (l.get('host') or []) for l in work.get('locations') or [])):
        return True
    for l in work.get('locations') or []:
        for u in (l.get('pdf'), l.get('landing')):
            if u and rec['inst_name'] in hostmap.get(hostkey(u), ()):
                return True
    return False


def hostkey(u):
    h = host_of(u)
    if h in ('hdl.handle.net', 'doi.org', 'dx.doi.org'):
        p = urllib.parse.urlsplit(u).path.strip('/').split('/')
        return h.replace('dx.', '') + '/' + (p[0] if p else '')
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-resolve', action='store_true')
    args = ap.parse_args()
    random.seed(20261116)
    U, n_held = universe()
    R = {r['id']: r for r in U}
    ids = inst_ids()
    byinst = collections.defaultdict(list)
    for r in U:
        byinst[r['inst_name']].append(r)

    # ---- route 1a: institution listings
    found = {}
    hostmap = collections.defaultdict(set)
    for name, I in ids.items():
        p = CACHE / f'works/{I}.jsonl'
        if not p.exists():
            continue
        works = [json.loads(l) for l in p.open()]
        for w in works:
            for l in w.get('locations') or []:
                for u in (l.get('pdf'), l.get('landing')):
                    if u and (l.get('source_type') in (None, 'repository')):
                        hostmap[hostkey(u)].add(name)
        for aid, (w, s, n) in link(byinst[name], works).items():
            found[aid] = {'work': w, 'score': s, 'via': 'openalex-institution-listing'}
    # hosts seen for more than 3 institutions are aggregators, not evidence of an institution
    hostmap = {h: v for h, v in hostmap.items() if len(v) <= 3}
    for h, inst in EXTRA_HOSTS.items():
        hostmap.setdefault(h, set()).add(inst)

    # ---- route 1c: OAI listings of open hosts (oai_open.py); file links from the xoai bitstreams
    for host, name in OAI_OPEN.items():
        works = oai_works(host)
        for aid, (w, s, n) in link(byinst[name], works).items():
            if aid in found and any(open_links(found[aid]['work'])) and found[aid]['work']['id'] != w['id']:
                # both routes matched: keep the OAI record's links first (current), OpenAlex's after
                w = dict(w, locations=w['locations'] + found[aid]['work'].get('locations', []))
            found[aid] = {'work': w, 'score': s, 'via': f'oai-listing {host}'}

    # ---- route 1b: per-record title search
    searched = set()
    for f in glob.glob(str(CACHE / 'search-*.jsonl')):
        for l in open(f):
            d = json.loads(l)
            searched.add(d['aha_id'])
            r = R.get(d['aha_id'])
            if not r or r['id'] in found:
                continue
            I = ids.get(r['inst_name'])
            ws = [w for w in d['results'] if institution_ok(r, w, I, hostmap)]
            m = link([r], ws)
            if r['id'] in m:
                w, s, n = m[r['id']]
                found[r['id']] = {'work': w, 'score': s, 'via': 'openalex-title-search'}

    p1 = pass_one()
    # ---- choose a route per record
    rows = []
    to_resolve = []
    for r in U:
        aid = r['id']
        f = found.get(aid)
        pp = p1.get(aid)
        row = {'aha_id': aid, 'year': r['year'], 'band': band(r['year']), 'institution': r['inst_name'],
               'dissertator': r['dissertator'], 'title': r['title'], 'via': '', 'openalex_id': '', 'match_score': '',
               'work_title': '', 'work_year': '', 'route': 'unknown', 'reason': '', 'url': '', 'host': '',
               'kind': '', 'host_class': '', 'pass_one': pp['status'] if pp else '', 'other_copies': ''}
        cands = []
        if f:
            w = f['work']
            row.update(via=f['via'], openalex_id=w['id'], match_score=f['score'], work_title=w['title'], work_year=w['year'])
            for l in open_links(w):
                cands.append((l['url'], 'file' if (l['kind'] == 'pdf' or FILE_PAT.search(l['url'])) else 'landing', 'openalex'))
            if not cands and any(l.get('pdf') or l.get('landing') for l in w.get('locations') or []):
                urls = ' '.join((l.get('pdf') or '') + ' ' + (l.get('landing') or '') for l in w.get('locations') or []).lower()
                if 'repository.upenn.edu/' in urls:
                    row['reason'] = 'Penn record known only by its pre-2023 bepress link, which now redirects to the home page; not in the current Dissertations and Theses OAI set with a file (ProQuest-only "AAI" record or not migrated)'
                elif re.search(r'proquest|umi\.com|pqdt', urls):
                    row['reason'] = 'ProQuest only (paywalled)'
                else:
                    row['reason'] = 'only library-catalogue or journal locations (no repository copy)'
        if pp:
            if not f:
                row['via'] = 'pass-one link'
            cands.append((pp['url'], 'file', 'pass-one'))
        row['_cands'] = cands
        rows.append(row)

    # resolve handle/DOI links to their targets (handle proxy API, metadata only)
    for row in rows:
        new = []
        for u, k, src in row['_cands']:
            if host_of(u) in ('hdl.handle.net', 'doi.org', 'dx.doi.org'):
                t = None if args.no_resolve else resolve.handle_target(u)
                if t:
                    new.append((t, 'file' if FILE_PAT.search(t) else 'landing', src + '+handle'))
                    continue
            new.append((u, k, src))
        row['_cands'] = list(dict.fromkeys(new))

    RANK = {('open', 'file'): 0, ('ai-excluded', 'file'): 1, ('open', 'landing'): 2, ('ai-excluded', 'landing'): 3,
            ('browser', 'file'): 4, ('browser', 'landing'): 5, ('retry', 'file'): 6, ('retry', 'landing'): 7}
    for row in rows:
        scored = []
        for u, k, src in row['_cands']:
            if host_of(u) in ('hdl.handle.net', 'doi.org', 'dx.doi.org'):
                scored.append((5, u, 'landing', ('browser', 'unresolved handle/DOI link', None)))
                continue
            c = host_class(u)
            scored.append((RANK.get((c[0], k), 8), u, k, c))
        scored.sort(key=lambda s: s[0])
        row['_scored'] = scored
        if scored:
            row['other_copies'] = ' '.join(s[1] for s in scored[1:4])

    # landing pages on open hosts: ask the page for its file link (round-robin over hosts)
    if not args.no_resolve:
        queue = collections.defaultdict(list)
        for row in rows:
            for rk, u, k, c in row['_scored']:
                if c[0] == 'open' and k == 'landing' and not any(s[0] == 0 for s in row['_scored']):
                    queue[host_of(u)].append((u, c[2]))
        order = []
        while any(queue.values()):
            for h in list(queue):
                if queue[h]:
                    order.append(queue[h].pop(0))
        print('landing pages to read on open hosts:', len(order), flush=True)
        for k, (u, delay) in enumerate(order):
            resolve.landing_file(u, delay)
            if k % 100 == 0:
                print(' ', k, flush=True)

    # final route
    for row in rows:
        pp = p1.get(row['aha_id'])
        if pp and pp['status'] == 'downloaded':
            row.update(route='held-pending', reason='downloaded 2026-11-14/15, not registered (failed register checks)', url=pp['url'], host=pp['host'])
            continue
        chosen = None
        notes = []
        for rk, u, k, c in row['_scored']:
            cls = c[0]
            if cls == 'open' and k == 'landing' and not args.no_resolve:
                fu, st, note = resolve.landing_file(u, c[2])
                if fu:
                    fc = host_class(fu)
                    if fc[0] in ('open', 'ai-excluded'):
                        chosen = (fc[0], fu, 'file', fc)
                        break
                    notes.append(f'{host_of(fu)}: {fc[1]}')
                    continue
                notes.append(f'{host_of(u)}: {note or st}')
                continue
            chosen = (cls, u, k, c)
            break
        # pass-one failures that tell us about access
        if pp and pp['status'].startswith('failed: 401 [application/json'):
            row.update(route='restricted', reason='file restricted/embargoed (DSpace API answered 401 to the 2026-11-15 run)',
                       url=pp['url'], host=pp['host'])
            continue
        if pp and re.search(r'Login', pp['status']):
            row.update(route='restricted', reason='login page instead of file (2026-11-15 run)', url=pp['url'], host=pp['host'])
            continue
        if chosen:
            cls, u, k, c = chosen
            row.update(url=u, host=host_of(u), kind=k, host_class=f'{c[0]}: {c[1]}')
            if cls in ('open', 'ai-excluded') and k == 'file':
                row['route'] = cls
            elif cls in ('open', 'ai-excluded') and k == 'landing':
                row['route'] = 'ai-excluded-landing' if cls == 'ai-excluded' else 'browser'
            elif cls == 'retry':
                row['route'] = 'retry'
            else:
                row['route'] = 'browser'
            if pp and row['route'] in ('open', 'ai-excluded') and pp['status'].startswith('failed') and u == pp['url']:
                row['route'] = 'retry' if 'never tried' in pp['status'] else row['route']
            continue
        if notes:
            if any('restricted or embargoed' in n for n in notes):
                row.update(route='restricted', reason='repository record, landing page says restricted/embargoed; no file link')
            elif any(re.search(r'/AAI|dissertations/AAI', u) for _, u, _, _ in row['_scored']):
                row.update(route='restricted', reason='repository record of a ProQuest dissertation (abstract only, no file)')
            elif any('HTTP 40' in n or 'challenge' in n or 'stopped' in n for n in notes):
                row.update(route='browser', reason='; '.join(notes)[:200], url=row['_scored'][0][1], host=host_of(row['_scored'][0][1]))
            else:
                row.update(route='restricted', reason='repository record with no file link on its landing page: ' + '; '.join(notes)[:150])
            continue
        if row['reason']:
            row['route'] = 'restricted'
            continue
        row['reason'] = 'no open copy found (OpenAlex listing' + (' + title search' if row['aha_id'] in searched else '') + ')'

    json.dump({'found': {k: {'via': v['via'], 'score': v['score'], 'work': v['work']['id']} for k, v in found.items()}},
              (CACHE / 'found.json').open('w'))
    import pickle
    pickle.dump(rows, (CACHE / 'rows.pkl').open('wb'))
    print(collections.Counter((r['route'], r['band']) for r in rows))


if __name__ == '__main__':
    main()
