#!/usr/bin/env python3
"""User-run download survey and lists (2026-11-14): where can History PhD theses be had by script (open hosts),
by a curl list the USER runs (hosts that allow general clients but exclude named AI crawlers), only in a browser
(challenge / disallow / 401-403), or not at all (embargo, print only, captcha)?

Nothing here requests a thesis file. Requests made:
  robots      each host's robots.txt, once, generic User-Agent, no contact details, 1 request a second
  openalex    OpenAlex (key from the git-ignored openalex-api-key.txt, never printed or written)
  datacite    DataCite REST search
  oai         OAI-PMH ListRecords, ONLY on hosts whose robots.txt allows the OAI path for '*' AND names no AI
              client (an AI agent stays off hosts that exclude AI clients, even for metadata)
Outputs under data/field-research/user-run-downloads-2026-11-14/ (see SURVEY.md there); caches (raw robots
files, API pages) under /mnt/e/user-run-downloads-2026-11-14/cache (not in git).

Classes (as in scripts/aha_wget_lists.py):
  open         robots lets '*' fetch the file path and no named AI client is disallowed
  ai-excluded  '*' may fetch the file path; one or more named AI clients are disallowed (the user's curl is not one)
  browser      '*' is disallowed on the file path, robots.txt refused (401/403), HTML/challenge instead of
               robots.txt, or the host is known to challenge/refuse scripts
  retry        robots.txt timed out / DNS failure / 5xx: not a refusal, try again later
"""
import argparse, csv, html, json, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/field-research/user-run-downloads-2026-11-14'
CACHE = Path('/mnt/e/user-run-downloads-2026-11-14/cache')
UA = 'research-download-check/1.0'
API_UA = 'historiography-research/1.0'
AI = ['ClaudeBot', 'Claude-User', 'Claude-SearchBot', 'anthropic-ai', 'GPTBot', 'ChatGPT-User', 'OAI-SearchBot',
      'CCBot', 'Google-Extended', 'PerplexityBot', 'Bytespider', 'Applebot-Extended', 'meta-externalagent']
TODAY = '2026-11-14'


# ---------------------------------------------------------------- robots.txt
def parse_robots(text):
    """Groups as [(agents, [(allow?, pattern)], crawl_delay)]; comments kept separately."""
    groups, cur, last_was_agent = [], None, False
    comments = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('#'):
            comments.append(line.lstrip('#').strip())
            continue
        line = line.split('#', 1)[0].strip()
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k, v = k.strip().lower(), v.strip()
        if k == 'user-agent':
            if cur is None or not last_was_agent:
                cur = {'agents': [], 'rules': [], 'delay': None}
                groups.append(cur)
            cur['agents'].append(v.lower())
            last_was_agent = True
            continue
        last_was_agent = False
        if cur is None:
            continue
        if k in ('allow', 'disallow'):
            cur['rules'].append((k == 'allow', v))
        elif k == 'crawl-delay':
            cur['delay'] = v
    return groups, comments


def _match(pattern, path):
    if not pattern:
        return False
    rx = re.escape(pattern).replace(r'\*', '.*')
    if rx.endswith(r'\$'):
        rx = rx[:-2] + '$'
    return re.match(rx, path) is not None


def group_for(groups, agent):
    a = agent.lower()
    named = [g for g in groups if any(x != '*' and x in a for x in g['agents'])]
    if named:
        return named, True
    return [g for g in groups if '*' in g['agents']], False


def allowed(groups, agent, path):
    """Google semantics: rules of the most specific matching group(s); longest match wins, allow on a tie."""
    gs, _ = group_for(groups, agent)
    best = None
    for g in gs:
        for allow, pat in g['rules']:
            if pat == '' and not allow:
                continue  # "Disallow:" (empty) allows everything
            if _match(pat, path):
                key = (len(pat), allow)
                if best is None or key > best[0]:
                    best = (key, allow, pat)
    if best is None:
        return True, ''
    return best[1], ('Allow: ' if best[1] else 'Disallow: ') + best[2]


def fetch_robots(host, scheme='https'):
    CACHE.mkdir(parents=True, exist_ok=True)
    cf = CACHE / f'robots-{host}.json'
    if cf.exists():
        return json.loads(cf.read_text())
    url = f'{scheme}://{host}/robots.txt'
    res = {'host': host, 'url': url, 'date': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            res.update(status=r.status, final_url=r.geturl(), body=r.read(400000).decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        res.update(status=e.code, final_url=url, body='')
    except Exception as e:  # timeouts, DNS, TLS: a retry, not a refusal
        res.update(status='error:' + type(e).__name__, final_url=url, body='')
    time.sleep(1)
    cf.write_text(json.dumps(res))
    return res


PURPOSE = re.compile(r'(\bai\b|artificial|train|llm|crawler|scrap|load|harvest|oai|api|contact|@|polite|rate|bot|'
                     r'permission|request|please|server|performance|language model)', re.I)


def classify(host, file_paths, oai_paths, known=None):
    """Return a dict: class, rule quoted, AI clients excluded, crawl delay, OAI allowed for '*' and for AI,
    purpose comments, contacts."""
    r = fetch_robots(host)
    out = {'host': host, 'robots_url': r['url'], 'robots_status': r['status'], 'checked': r['date'],
           'final_url': r.get('final_url', ''), 'rule': '', 'ai_excluded': '', 'crawl_delay': '', 'oai_path': '',
           'oai_allowed_star': '', 'oai_allowed_ai': '', 'purpose_comments': '', 'contacts': '', 'sitemaps': ''}
    body = r.get('body') or ''
    st = r['status']
    final_host = urllib.parse.urlparse(out['final_url']).netloc
    if known:
        out.update(cls='browser', rule=known)
        if st != 200:
            return out
    if isinstance(st, str) and st.startswith('error'):
        out.update(cls='retry', rule=f'robots.txt {st} (timeout/DNS: not a refusal)')
        return out
    if st in (500, 502, 503, 504):
        out.update(cls='retry', rule=f'robots.txt answered {st}')
        return out
    if st in (401, 403, 429):
        out.update(cls='browser', rule=f'robots.txt answered {st}')
        return out
    if st == 404:
        out.update(cls=out.get('cls') or 'open', rule='no robots.txt (404): nothing disallowed')
        out['oai_allowed_star'] = out['oai_allowed_ai'] = 'yes'
        out['oai_path'] = oai_paths[0] if oai_paths else ''
        return out
    if final_host and final_host != host:
        out['rule'] = f'robots.txt redirects to {final_host}'
    if '<html' in body[:800].lower() or '<!doctype' in body[:200].lower():
        out.update(cls='browser', rule=(out['rule'] + '; ' if out['rule'] else '') + 'robots.txt returned an HTML page (challenge?)')
        return out
    groups, comments = parse_robots(body)
    star_ok = [allowed(groups, '*', p) for p in file_paths]
    ai_bad = []
    for a in AI:
        gs, named = group_for(groups, a)
        ok, why = allowed(groups, a, file_paths[0])
        if not ok and (named or not star_ok[0][0]):
            if named:
                ai_bad.append(a)
    delays = [g['delay'] for g in groups if '*' in g['agents'] and g['delay']]
    out['crawl_delay'] = delays[0] if delays else ''
    out['ai_excluded'] = ' '.join(ai_bad)
    purpose = [c for c in comments if c and PURPOSE.search(c)]
    out['purpose_comments'] = ' | '.join(purpose)[:600]
    out['contacts'] = ' '.join(sorted(set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', ' '.join(comments)))))
    out['sitemaps'] = ' '.join(re.findall(r'(?im)^\s*sitemap:\s*(\S+)', body))[:300]
    for p in oai_paths:
        s_ok, _ = allowed(groups, '*', p)
        a_ok = all(allowed(groups, a, p)[0] for a in AI)
        out['oai_path'] = p
        out['oai_allowed_star'] = 'yes' if s_ok else 'no'
        out['oai_allowed_ai'] = 'yes' if a_ok else 'no'
        if s_ok:
            break
    bad = [(p, why) for p, (ok, why) in zip(file_paths, star_ok) if not ok]
    if out.get('cls') == 'browser':
        pass
    elif bad:
        out.update(cls='browser', rule=f"'*' {bad[0][1]} (file path {bad[0][0]})")
    elif ai_bad:
        g, _ = group_for(groups, ai_bad[0])
        rules = '; '.join(('Allow: ' if a else 'Disallow: ') + p for gg in g for a, p in gg['rules'])[:200]
        out.update(cls='ai-excluded', rule=f"User-agent: {' / '.join(ai_bad[:4])}{' …' if len(ai_bad) > 4 else ''} → {rules}; '*' may fetch the file path")
    else:
        out.update(cls='open', rule="'*' may fetch the file path; no AI client named" + (f" ({star_ok[0][1]})" if star_ok[0][1] else ''))
    return out


# ---------------------------------------------------------------- APIs
def _key():
    return (ROOT / 'openalex-api-key.txt').read_text().strip()


def get_json(url, cache_name=None, tries=4):
    if cache_name:
        cf = CACHE / 'api' / cache_name
        if cf.exists():
            return json.loads(cf.read_text())
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': API_UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(5 * 2 ** attempt)
                continue
            if e.code == 404:
                data = None
                break
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < tries - 1:
                time.sleep(5 * 2 ** attempt)
                continue
            raise
    if cache_name:
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps(data))
    return data


def openalex_works(params, cache_name=None):
    p = dict(params)
    url = 'https://api.openalex.org/works?' + urllib.parse.urlencode(p) + '&api_key=' + urllib.parse.quote(_key())
    return get_json(url, cache_name)


def openalex_source_all(source_id, extra_filter='type:dissertation', tag=''):
    """Every work of a repository source (cursor paging, 200 a page, 1 credit a page)."""
    cursor, out, page = '*', [], 0
    while cursor:
        d = openalex_works({'filter': f'locations.source.id:{source_id},{extra_filter}', 'per-page': 200, 'cursor': cursor,
                            'select': 'id,doi,title,publication_year,authorships,locations,primary_topic,type,ids'},
                           cache_name=f'oa-src-{source_id}-{tag}-{page}.json')
        if not d:
            break
        out += d['results']
        cursor = d['meta'].get('next_cursor')
        if not d['results']:
            break
        page += 1
    return out


def handle_resolve(hdl):
    """handle.net proxy REST API: returns the URL value without contacting the repository."""
    return get_json('https://hdl.handle.net/api/handles/' + urllib.parse.quote(hdl, safe='/'),
                    cache_name='hdl-' + re.sub(r'[^A-Za-z0-9]+', '_', hdl) + '.json')


def doi_resolve(doi):
    return get_json('https://doi.org/api/handles/' + urllib.parse.quote(doi, safe='/'),
                    cache_name='doi-' + re.sub(r'[^A-Za-z0-9]+', '_', doi) + '.json')


def handle_url(d):
    for v in (d or {}).get('values') or []:
        if v.get('type') == 'URL':
            return v['data']['value']
    return ''


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).casefold()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def title_key(text):
    return fold(re.split(r'[:.?]', text or '', maxsplit=1)[0])[:60]


def slug(s, n=60):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:n]


# ---------------------------------------------------------------- OAI-PMH (open hosts only)
import xml.etree.ElementTree as ET
OAI_NS = {'o': 'http://www.openarchives.org/OAI/2.0/'}
OAI = '{http://www.openarchives.org/OAI/2.0/}'


def oai_get(base, params, gap=2.0):
    """One OAI request, cached by its query; the caller guarantees the host is open and the OAI path allowed."""
    q = urllib.parse.urlencode(params)
    cf = CACHE / 'oai' / (re.sub(r'[^A-Za-z0-9]+', '_', base + '?' + q)[:220] + '.xml')
    if cf.exists():
        return cf.read_text()
    for attempt in range(4):
        try:
            req = urllib.request.Request(base + '?' + q, headers={'User-Agent': API_UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode('utf-8', 'replace')
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 403, 401):
                raise RuntimeError(f'{base}: HTTP {e.code}, stopping this host')
            if attempt == 3:
                raise
            time.sleep(10 * 2 ** attempt)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 3:
                raise
            time.sleep(10 * 2 ** attempt)
    time.sleep(gap)
    cf.parent.mkdir(parents=True, exist_ok=True)
    cf.write_text(body)
    return body


def oai_sets(base, gap=2.0):
    out, token = [], None
    while True:
        body = oai_get(base, {'verb': 'ListSets', **({'resumptionToken': token} if token else {})}, gap)
        root = ET.fromstring(body)
        for s in root.iter(OAI + 'set'):
            out.append((s.findtext('o:setSpec', '', OAI_NS), s.findtext('o:setName', '', OAI_NS)))
        t = root.find('.//o:resumptionToken', OAI_NS)
        token = t.text if t is not None and t.text else None
        if not token:
            return out


def oai_records(base, prefix, setspec=None, gap=2.0):
    token = None
    while True:
        params = ({'verb': 'ListRecords', 'resumptionToken': token} if token else
                  {'verb': 'ListRecords', 'metadataPrefix': prefix, **({'set': setspec} if setspec else {})})
        body = oai_get(base, params, gap)
        root = ET.fromstring(body)
        if root.find('o:error', OAI_NS) is not None:
            return
        for rec in root.iter(OAI + 'record'):
            yield rec
        t = root.find('.//o:resumptionToken', OAI_NS)
        token = t.text if t is not None and t.text else None
        if not token:
            return


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('stage', choices=['canada', 'world'])
    a = p.parse_args()
    if a.stage == 'canada':
        import user_run_canada
        user_run_canada.main()
    else:
        import user_run_world
        user_run_world.main()
