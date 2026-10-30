"""Read ORA landing pages for Oxford DataCite dissertation candidates (2026-10-29).

Input: a JSON list of [doi, year, title, supervisors]. For each DOI, resolve to the ORA landing
page and record department, division, college, award type and level, and the open PDF URL
(citation_pdf_url). Robots.txt allows /objects/ and /files/; previews and searches are not used.
Paced at one request every 3 seconds. Output: raw/ora-landing.jsonl (resumable).
"""
import html
import json
from pathlib import Path
import re
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
UA = 'historiography-research (+https://github.com/jburnford/historiography; jic823@usask.ca)'
LABELS = {'department': 'Department:', 'division': 'Division:', 'college': 'Oxford college:',
          'award_type': 'Type of award:', 'award_level': 'Level of award:', 'awarding_institution': 'Awarding institution:'}
STOP = re.compile(r'\s+(Division|Department|Oxford college|Role|Type of award|Level of award|Awarding institution|Item Description|Sub department|Research group|Funder|Grant)\b.*')


def field(text, label):
    i = text.find(label)
    if i < 0:
        return None
    s = ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', text[i + len(label):i + 700])).split())
    s = s.removeprefix(label).strip()
    return STOP.sub('', s).strip() or None


def main(src, out):
    done = set()
    if out.exists():
        done = {json.loads(l)['doi'] for l in out.open() if l.strip()}
    rows = json.loads(Path(src).read_text())
    with out.open('a') as f:
        for doi, year, title, sups in rows:
            if doi in done:
                continue
            rec = dict(doi=doi, year=year, title=title, supervisors=sups)
            try:
                req = urllib.request.Request(f'https://doi.org/{doi}', headers={'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    t = r.read().decode('utf-8', 'replace')
                    rec['url'] = r.geturl()
                rec.update({k: field(t, v) for k, v in LABELS.items()})
                rec['subjects'] = re.findall(r'name="citation_keywords" content="([^"]+)"', t) or \
                    sorted(set(re.findall(r'subject" content="([^"]+)"', t)))
                rec['pdf_url'] = (re.findall(r'citation_pdf_url" content="([^"]+)"', t) or [None])[0]
                rec['embargo'] = bool(re.search(r'[Ee]mbargo', t))
            except Exception as e:  # keep going; the row records the failure
                rec['error'] = f'{type(e).__name__}: {e}'
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            f.flush()
            time.sleep(3)


if __name__ == '__main__':
    main(sys.argv[1], Path(sys.argv[2]))
