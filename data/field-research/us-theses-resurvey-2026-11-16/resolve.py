"""Metadata-only link resolution for candidate copies (no thesis file is requested):
  * hdl.handle.net / doi.org links -> target URL through the handle proxy REST API (hdl.handle.net/api/handles/...)
  * landing pages on OPEN hosts only -> the file link the page declares (meta citation_pdf_url), with the host's
    crawl delay (minimum 3 s), one connection per host; a host that answers 401/403/429 or a challenge page is
    stopped for the run and classed browser.
Landing pages on ai-excluded hosts are never requested here; they go to the user-run resolver (resolve-landing.sh)."""
import html as htmlmod
from common import *

CHALLENGE = re.compile(r'just a moment|attention required|access denied|making sure you|are you a robot|captcha|'
                       r'checking your browser|request rejected|anubis', re.I)
RESTRICT = re.compile(r'embargo|restricted to|campus only|access is restricted|not available for download|'
                      r'available to .*(users|community) only|login to view|sign in to (view|access)|withheld', re.I)
STOPPED = {}


def handle_target(url):
    """Resolve hdl.handle.net/<h> or doi.org/<d> through the handle REST API; (target or None)."""
    m = re.match(r'https?://(?:hdl\.handle\.net|(?:dx\.)?doi\.org)/(.+)', url)
    if not m:
        return None
    h = urllib.parse.unquote(m.group(1)).split('?')[0]
    api = ('https://doi.org/api/handles/' if 'doi.org' in url else 'https://hdl.handle.net/api/handles/') + urllib.parse.quote(h, safe='/:')
    try:
        d = cached_json('handles', api, api, delay=1)
    except Exception:
        return None
    for v in d.get('values') or []:
        if v.get('type') == 'URL':
            return v['data']['value']
    return None


def landing_file(url, delay):
    """(file_url or '', status, note) from an open host's landing page; cached on E:."""
    host = urllib.parse.urlsplit(url).netloc
    p = CACHE / 'landing' / (hashlib.sha1(url.encode()).hexdigest() + '.json')
    if p.exists():
        d = json.loads(p.read_text())
        return d['file'], d['status'], d['note']
    if host in STOPPED:
        return '', 'stopped', STOPPED[host]
    file, note = '', ''
    try:
        st, h, body, final = get(url, delay=max(delay or 0, 3), timeout=60)
        ctype = h.get('Content-Type', '')
        if 'html' not in ctype:
            note = f'not html ({ctype}); not read'
            status = st
        else:
            text = body[:400000].decode('utf-8', 'replace')
            title = (re.search(r'<title[^>]*>([^<]*)', text, re.I) or [None, ''])[1].strip()
            if CHALLENGE.search(title) or (st == 202):
                STOPPED[host] = f'challenge page: {title[:60]}'
                return '', 'challenge', STOPPED[host]
            metas = re.findall(r'<meta[^>]+name="citation_pdf_url"[^>]+content="([^"]+)"', text, re.I) + \
                re.findall(r'<meta[^>]+content="([^"]+)"[^>]+name="citation_pdf_url"', text, re.I)
            if metas:
                file = urllib.parse.urljoin(final, htmlmod.unescape(metas[0]))
            elif RESTRICT.search(text):
                note = 'landing page: restricted or embargoed, no file link'
            else:
                note = 'landing page: no file link declared'
            status = st
    except urllib.error.HTTPError as e:
        status = e.code
        if e.code in (401, 403, 429):
            STOPPED[host] = f'answered {e.code}'
        note = f'HTTP {e.code}'
    except Exception as e:
        status, note = 0, f'network: {str(e)[:80]}'
    p.write_text(json.dumps({'url': url, 'file': file, 'status': status, 'note': note}))
    return file, status, note
