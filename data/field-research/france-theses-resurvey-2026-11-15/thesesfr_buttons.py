"""Ask theses.fr which access routes it lists for each thesis (2026-11-15 re-survey).

Metadata only: GET https://theses.fr/api/v1/button/{nnt} (the endpoint the theses.fr page uses to draw its access
buttons; source: github.com/abes-esr/theses-api-diffusion, BoutonController). It lists the national deposit
(online / ESR-restricted / intranet / embargo with end date), library copies (Sudoc) and "reproductions
conformes" or author versions held elsewhere (EDITION_AO / EDITION_COM_ELEC: HAL-TEL, university repositories).
No document endpoint is called and no thesis file is requested.

theses.fr robots.txt (read 2026-11-15): User-agent * , Crawl-delay 5, no AI client named, a list of single
thesis/person paths disallowed (takedowns). NNTs listed there are skipped. Pace: one request every 5.5 s.
Generic User-Agent, no contact details. Stops at the first 403/429 or HTML challenge on the button endpoint.

usage: python3 -I thesesfr_buttons.py NNT_LIST OUT_JSONL     (resumable: NNTs already in OUT are skipped)
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = 'research-metadata-survey/1.0'
ROBOTS = Path('/mnt/e/france-theses-snapshot-2026-11-12/cache/theses.fr.txt')


def main():
    nnts = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    out = Path(sys.argv[2])
    done = set()
    if out.exists():
        for l in out.open():
            try:
                done.add(json.loads(l)['nnt'])
            except Exception:
                pass
    blocked = set(re.findall(r'(?im)^\s*disallow:\s*/(\S+)', ROBOTS.read_text()))
    with out.open('a') as f:
        for nnt in nnts:
            if nnt in done:
                continue
            rec = {'nnt': nnt, 'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
            if nnt in blocked:
                rec['status'] = 'robots_disallowed_page'
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                continue
            t0 = time.time()
            try:
                req = urllib.request.Request(f'https://theses.fr/api/v1/button/{nnt}',
                                             headers={'User-Agent': UA, 'Accept': 'application/json'})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read().decode('utf-8', 'replace')
                if body.lstrip().startswith('<'):
                    print('HTML instead of JSON (challenge?) - stopping', file=sys.stderr)
                    break
                rec['status'] = 'ok'
                rec['buttons'] = json.loads(body)
            except urllib.error.HTTPError as e:
                rec['status'] = f'http_{e.code}'
                if e.code in (403, 429):
                    f.write(json.dumps(rec) + '\n')
                    print(f'{e.code} on the button endpoint - stopping', file=sys.stderr)
                    break
            except Exception as e:
                rec['status'] = 'error'
                rec['error'] = f'{type(e).__name__}: {e}'[:200]
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            f.flush()
            time.sleep(max(0.0, 5.5 - (time.time() - t0)))


if __name__ == '__main__':
    main()
