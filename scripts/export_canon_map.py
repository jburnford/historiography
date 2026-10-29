#!/usr/bin/env python3
"""Publish the canon map (historian co-citation network) for the site.

Reads the data block of the research page that scripts/historian_cocitation_network.py writes
(summary/comparisons/historian-network.html) and writes data/dissertation-layer/site/canon-map.json
with three additions:
- ``snapshot``: the build date the page states;
- ``region_theses``: the per-region thesis counts the page states;
- ``nodes[].reading``: the person's key in the Dissertation reading export, where exactly one person
  there has the same display name. This is a link only. The two use different builds.
- ``nodes[].label``: the name with initials written out ('Thompson, E. P', 'Du Bois, W.e.b' become
  'Thompson, E. P.' and 'Du Bois, W. E. B.'); ``name`` stays as the graph keys it.
The output hash, the source hash and the snapshot go into data/dissertation-layer/manifest.json under
``canon_map``; scripts/build_site.py publishes the file only when the hash matches.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/field-research/dissertation-citations-2026-10-11/summary/comparisons/historian-network.html'
LAYER = ROOT / 'data/dissertation-layer'
OUT = LAYER / 'site' / 'canon-map.json'
INITIALS = re.compile(r'^(?:[A-Za-z]\.)*[A-Za-z]\.?$')


def label(name):
    surname, sep, given = name.partition(', ')
    if not sep:
        return name
    parts = [' '.join(f'{c.upper()}.' for c in tok.replace('.', '')) if INITIALS.match(tok) else tok for tok in given.split()]
    return f"{surname}, {' '.join(parts)}"


NAMES = {'Canada': 'CA', 'United States': 'US', 'Britain': 'GB', 'Rest of Europe': 'EU', 'elsewhere': 'OTHER'}


def main():
    page = SOURCE.read_text(encoding='utf-8')
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1))
    data['snapshot'] = re.search(r'Built (\d{4}-\d\d-\d\d)', page).group(1)
    counts = re.search(r'next\s+region\'s \(([^)]*) theses\)', page).group(1)
    data['region_theses'] = {NAMES[m.group(1)]: int(m.group(2).replace(',', ''))
                             for m in re.finditer(r'(Canada|United States|Britain|Rest of Europe|elsewhere) ([\d,]+)', counts)}
    assert set(data['region_theses']) == set(NAMES.values()), data['region_theses']
    index = json.loads((LAYER / 'site' / 'index.json').read_text())
    by_name = {}
    for s in index['sources']:
        if s['key'].startswith('P:'):
            by_name.setdefault(s['short'], []).append(s['key'])
    linked = 0
    for n in data['nodes']:
        n['label'] = label(n['name'])
        keys = by_name.get(n['name'], [])
        if len(keys) == 1:
            n['reading'] = keys[0]
            linked += 1
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    OUT.write_text(text, encoding='utf-8')
    manifest_path = LAYER / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['canon_map'] = dict(
        snapshot=data['snapshot'],
        source=str(SOURCE.relative_to(ROOT)),
        source_sha256=hashlib.sha256(page.encode('utf-8')).hexdigest(),
        output='site/canon-map.json',
        output_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text) / 1e6:.2f} MB): {len(data['nodes'])} people, "
          f"{linked} linked to Dissertation reading, snapshot {data['snapshot']}")


if __name__ == '__main__':
    main()
