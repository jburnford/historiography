"""One HEAD per OPEN host on open-urls.tsv (the first row of each host with >= 3 rows): where does a link land?
Status, final host and content type only; no body is read. Results in E:/.../head/head-check.json."""
import collections, subprocess
from common import *

rows = [l.split('\t') for l in (OUT / 'open-urls.tsv').read_text().splitlines() if l]
by = collections.defaultdict(list)
for r in rows:
    by[r[2]].append(r)
out = {}
for host, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    if len(rs) < 3:
        continue
    url = rs[0][0]
    p = subprocess.run(['curl', '-sS', '-I', '-L', '--max-redirs', '5', '--max-time', '40', '-A', UA, '-o', '/dev/null',
                        '-w', '%{http_code}\t%{content_type}\t%{url_effective}', url], capture_output=True, text=True)
    out[host] = {'n': len(rs), 'url': url, 'result': p.stdout.strip(), 'err': p.stderr.strip()[:200]}
    print(host, len(rs), out[host]['result'][:160], flush=True)
    time.sleep(2)
(CACHE / 'head' / 'head-check.json').write_text(json.dumps(out, indent=1))
