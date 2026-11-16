"""OAI-PMH listing of OPEN hosts (robots.txt lets '*' read the OAI path and names no AI client), done by the agent
with the host's crawl delay. Used where OpenAlex's links are stale (Penn moved from bepress to DSpace 7 in 2023;
its old viewcontent.cgi links now redirect to the home page). Pages cached under E:/.../oai/<host>/.
  python3 oai_open.py sets <host>            # ListSets
  python3 oai_open.py records <host> <set>   # ListRecords (xoai), resumable"""
import sys
from common import *

BASES = {'repository.upenn.edu': 'https://repository.upenn.edu/server/oai/request',
         'repository.arizona.edu': 'https://repository.arizona.edu/oai/request',
         'scholarspace.manoa.hawaii.edu': 'https://scholarspace.manoa.hawaii.edu/server/oai/request',
         'shareok.org': 'https://shareok.org/server/oai/request'}


def fetch(host, params, path):
    if path.exists():
        return path.read_text()
    st, text = robots(host)
    cls = classify(host, urllib.parse.urlsplit(BASES[host]).path)
    if cls[0] != 'open':
        raise SystemExit(f'{host}: OAI path not open for this client ({cls})')
    delay = max(cls[2] or 0, 3)
    s, h, body, _ = get(BASES[host] + '?' + urllib.parse.urlencode(params), delay=delay, timeout=300)
    t = body.decode('utf-8', 'replace')
    if '<OAI-PMH' not in t:
        raise SystemExit(f'{host}: not an OAI answer ({s})')
    path.write_text(t)
    return t


def token(t):
    m = re.search(r'<resumptionToken[^>]*>([^<]+)</resumptionToken>', t)
    return m.group(1) if m else None


def main():
    mode, host = sys.argv[1], sys.argv[2]
    d = CACHE / 'oai' / host
    d.mkdir(parents=True, exist_ok=True)
    if mode == 'sets':
        t = fetch(host, {'verb': 'ListSets'}, d / 'sets-0.xml')
        n = 0
        while token(t):
            n += 1
            t = fetch(host, {'verb': 'ListSets', 'resumptionToken': token(t)}, d / f'sets-{n}.xml')
        print('sets pages', n + 1)
    else:
        spec = sys.argv[3]
        sd = d / ('records-' + re.sub(r'[^A-Za-z0-9_.-]', '_', spec))
        sd.mkdir(exist_ok=True)
        t = fetch(host, {'verb': 'ListRecords', 'metadataPrefix': 'xoai', 'set': spec}, sd / 'page-0.xml')
        n = 0
        while token(t):
            n += 1
            t = fetch(host, {'verb': 'ListRecords', 'resumptionToken': token(t)}, sd / f'page-{n}.xml')
            if n % 20 == 0:
                print(n, flush=True)
        (sd / 'DONE').write_text('')
        print('pages', n + 1)


if __name__ == '__main__':
    main()
