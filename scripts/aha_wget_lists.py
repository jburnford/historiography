"""Direct-PDF lists for the AHA hybrid route, for a command-line download the USER runs (2026-11-14).

Reads download-links-batch-*.html (the "PDF links" sections only), reads each host's robots.txt once
(generic client, no contact details) and sorts hosts:
  open         robots.txt lets a generic client ('*') fetch the file path and names no AI client
  ai-excluded  '*' may fetch, but named AI crawlers are disallowed (the user's own wget is not one of them)
  browser      '*' is disallowed on the path, robots.txt is refused/unreachable, or the host is known to
               challenge or refuse scripts (KNOWN_BROWSER)
Writes wget/hosts.csv, wget/<class>-urls.tsv (url <TAB> output file name <TAB> host <TAB> crawl delay) and
wget/fetch.sh. No thesis file is requested.
"""
import csv, html, re, sys, time, urllib.parse, urllib.request, urllib.robotparser, collections, unicodedata
from pathlib import Path

D = Path('data/field-research/aha-repository-links-2026-11-04')
OUT = D / 'wget'
UA = 'research-download-check/1.0'
AI = ['ClaudeBot', 'Claude-User', 'anthropic-ai', 'GPTBot', 'CCBot', 'Google-Extended', 'PerplexityBot', 'Bytespider']
# refused or challenged scripts in earlier sessions (401/403, bot challenge, robots Disallow on the route)
KNOWN_BROWSER = {'deepblue.lib.umich.edu': '403 to scripts (2026-11-05)', 'd.lib.msu.edu': 'bot challenge (2026-11-05)',
                 'arch.library.northwestern.edu': '401/403 to scripts (2026-11-04)',
                 'repositories.lib.utexas.edu': '401/403 to scripts (2026-11-04)',
                 'www.ideals.illinois.edu': '401/403 to scripts (2026-11-04)',
                 'rucore.libraries.rutgers.edu': 'robots disallows OAI and search (2026-11-05)',
                 'etd.ohiolink.edu': 'OhioLINK robots disallows everything (2026-11-04)',
                 'scholarshare.temple.edu': 'robots-disallowed (2026-11-05)', 'hammer.purdue.edu': 'robots-disallowed (2026-11-05)',
                 'docs.lib.purdue.edu': 'robots-disallowed (2026-11-05)', 'researchrepository.wvu.edu': 'robots-disallowed (2026-11-05)',
                 'www.researchgate.net': 'not a repository route'}

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:60]

def rows():
    seen = set()
    for f in sorted(D.glob('download-links-batch-*.html')):
        s = f.read_text(encoding='utf-8')
        for part in re.split(r'<h2>', s)[1:]:
            head = part.split('</h2>')[0]
            if not head.lower().startswith('pdf links'):
                continue
            for m in re.finditer(r'<li><a href="([^"]+)">(.*?)</a>\s*—\s*(.*?)</li>', part, flags=re.S):
                u = html.unescape(m.group(1)); who = html.unescape(re.sub('<.*?>', '', m.group(2))); title = html.unescape(re.sub('<.*?>', '', m.group(3)))
                if u in seen:
                    continue
                seen.add(u)
                yield f.stem.split('-')[-1], u, who, title

def robots(host):
    url = f'https://{host}/robots.txt'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(400000).decode('utf-8', 'replace'); code = r.status
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return type(e).__name__, ''
    return code, body

def main():
    OUT.mkdir(exist_ok=True)
    rs = list(rows())
    byhost = collections.defaultdict(list)
    for b, u, who, title in rs:
        byhost[urllib.parse.urlparse(u).netloc].append((b, u, who, title))
    hosts = []; lists = collections.defaultdict(list)
    for host, items in sorted(byhost.items(), key=lambda x: -len(x[1])):
        code, body = robots(host); time.sleep(1)
        note = ''; delay = ''
        if host in KNOWN_BROWSER:
            cls, note = 'browser', KNOWN_BROWSER[host]
        elif host in ('hdl.handle.net', 'doi.org'):
            cls, note = 'browser', 'resolver link: target host not known without a request'
        elif code != 200:
            cls, note = ('open', 'no robots.txt (404): nothing disallowed') if code == 404 else ('browser', f'robots.txt {code}')
        elif '<html' in body[:600].lower():
            cls, note = 'browser', 'robots.txt returned an HTML page (challenge?)'
        else:
            rp = urllib.robotparser.RobotFileParser(); rp.parse(body.splitlines())
            ok = [rp.can_fetch('*', u) for _, u, _, _ in items]
            ai = [a for a in AI if not rp.can_fetch(a, items[0][1])]
            d = rp.crawl_delay('*'); delay = str(d) if d else ''
            if not all(ok):
                cls, note = 'browser', f"robots.txt disallows the file path for '*' ({ok.count(False)} of {len(ok)})"
            elif ai:
                cls, note = 'ai-excluded', 'named AI clients disallowed: ' + ' '.join(ai)
            else:
                cls = 'open'
        hosts.append({'host': host, 'direct_links': len(items), 'class': cls, 'crawl_delay': delay, 'robots_status': code, 'note': note})
        for b, u, who, title in items:
            name = f"aha-b{b}-{slug(who)}-{slug(title)[:40]}.pdf"
            lists[cls].append((u, name, host, delay or '10'))
        print(f"{len(items):4d} {host:42s} {cls:12s} {note}", flush=True)
    with open(OUT / 'hosts.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(hosts[0])); w.writeheader(); w.writerows(hosts)
    for cls, items in lists.items():
        with open(OUT / f'{cls}-urls.tsv', 'w', encoding='utf-8') as f:
            for it in items:
                f.write('\t'.join(it) + '\n')
        print(cls, len(items))

if __name__ == '__main__':
    main()
