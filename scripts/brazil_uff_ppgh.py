#!/usr/bin/env python3
"""Parse the UFF History programme's online thesis list (PPGH, historia.uff.br/stricto/tesesonline.php).

Brazil expansion, 2026-11-01. UFF (second only to USP in CAPES History doctorates) has no usable
OAI set, but its programme site lists every thesis and dissertation it hosts on one page: author,
advisor, defence date, level, committee (banca), title, abstract and a PDF under
``/stricto/td/<n>.pdf``. historia.uff.br has no robots.txt (404, 2026-11-01).

Output: ``<out>/uff-ppgh/records.jsonl``, one row per entry, with ``pdf`` set when a PDF is linked.

    python3 scripts/brazil_uff_ppgh.py --out data/field-research/brazil-theses-2026-10-31
"""
import argparse
import html
import json
import re
import urllib.request
from pathlib import Path

URL = 'https://www.historia.uff.br/stricto/tesesonline.php'
UA = 'historiography-research/1.0 (University of Saskatchewan; jic823@usask.ca)'


def field(block, label):
    m = re.search(r'<strong>' + label + r':</strong>(.*?)(?:&nbsp;|</p>)', block, re.S)
    return clean(m.group(1)) if m else ''


def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def parse(text):
    for block in text.split('<div class="teses-online">')[1:]:
        block = block.split('</div>')[0]
        banca = re.search(r'Banca de Defesa:</strong><br>(.*?)</p>', block, re.S)
        pdf = re.search(r'href="([^"]+/stricto/td/[^"]+\.pdf)"', block, re.I)
        abstract = re.search(r'Resumo:</strong>(.*?)(?:\[<a|$)', block, re.S)
        yield dict(author=field(block, 'Autor'), advisor=field(block, 'Orientador'),
                   defence_date=field(block, 'Data de Defesa'), level=field(block, r'N&iacute;vel'),
                   title=field(block, r'T&iacute;tulo'),
                   committee=[clean(x) for x in banca.group(1).split('<br>') if clean(x)] if banca else [],
                   abstract=clean(abstract.group(1)) if abstract else '',
                   pdf=pdf.group(1).replace('http://', 'https://') if pdf else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = Path(a.out) / 'uff-ppgh'
    out.mkdir(parents=True, exist_ok=True)
    raw = urllib.request.urlopen(urllib.request.Request(URL, headers={'User-Agent': UA}), timeout=300).read()
    rows = list(parse(raw.decode('latin-1')))
    with open(out / 'records.jsonl', 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    docs = [r for r in rows if r['level'].lower().startswith('dout')]
    print(f'{len(rows)} entries; {len(docs)} doctorates, {sum(1 for r in docs if r["pdf"])} with PDF')


if __name__ == '__main__':
    main()
