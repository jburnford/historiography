#!/usr/bin/env python3
"""Publish the canon map (historian co-citation network) for the site.

Reads the data block of the research page that scripts/historian_cocitation_network.py writes
(summary/comparisons/historian-network.html) and writes data/dissertation-layer/site/canon-map.json
with these additions:
- ``snapshot``: the build date the page states;
- removed: ``co`` and each view's ``edges`` (the research page's fixed top-5 lines); the site derives its
  lines from ``links``, ``link_top``, ``keep`` and ``min_co``;
- ``region_theses``: the per-region thesis counts the page states;
- ``nodes[].reading``: the person's key in the Dissertation reading export, where exactly one person
  there has the same display name. This is a link only. The two use different builds.
- ``nodes[].key``, ``nodes[].key_status``: the person's internal key and its status (established or
  unresolved) from data/identifiers/events-NNNN.jsonl. People awaiting merge review have none yet.
- ``nodes[].lc``: the person's LC name authority (an `lcnaf:` anchor in the identifier log), the public
  identifier the key log uses until Wikidata (PID-PLAN.md).
- ``nodes[].life``: life years for display ('1924–1993', 'd. 2009', 'c. 544–469 BCE') from
  data/person-facts/life-dates.csv. Birth years appear only for the dead (a recorded death, a reviewed
  deceased status, or born more than 120 years ago; user decision 2026-10-30); the repository keeps them all.
- ``nodes[].label``: the name with initials written out ('Thompson, E. P', 'Du Bois, W.e.b' become
  'Thompson, E. P.' and 'Du Bois, W. E. B.'); ``name`` stays as the graph keys it.
The output hash, the source hash and the snapshot go into data/dissertation-layer/manifest.json under
``canon_map``; scripts/build_site.py publishes the file only when the hash matches.
"""
import csv
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


def life_years(row):
    """Display life years from a life-dates row; living people's birth years are withheld."""
    def part(v):
        m = re.match(r'^(-?)0*(\d+)', v or '')
        return (int(m.group(2)) * (-1 if m.group(1) else 1), v.endswith('~')) if m else None
    born = part(row['birth']) if row['status'] == 'deceased' else None
    died = part(row['death'])
    if not died:
        return f'b. {born[0]}' if born and born[0] > 0 else ''
    approx = 'c. ' if died[1] or (born and born[1]) else ''
    if born and born[0] < 0 and died[0] < 0:
        return f'{approx}{-born[0]}–{-died[0]} BCE'
    era = lambda y: f'{-y} BCE' if y < 0 else str(y)
    return f'{approx}{era(born[0])}–{era(died[0])}' if born else f'd. {approx}{era(died[0])}'


def attach_keys(nodes):
    """``key`` and ``key_status`` from the identifier log (PID-PLAN.md), via the person's graph key.

    People deferred for merge review have no key yet and carry neither field."""
    from identifiers import State
    from key_canon_map import canon_keys
    state = State.load(ROOT / 'data/identifiers')
    graph_key = canon_keys(nodes)
    with (ROOT / 'data/person-facts/life-dates.csv').open(newline='', encoding='utf-8') as f:
        lives = {r['key']: r for r in csv.DictReader(f)}
    keyed = 0
    for n in nodes:
        found = state.lookup(f"diss-person:{graph_key[n['name'], n['qid']]}")
        if len(found) == 1:
            n['key'] = found[0]
            n['key_status'] = state.keys[found[0]]['resolution']
            keyed += 1
            lc = [a.split(':', 1)[1] for a in state.keys[found[0]]['anchors'] if a.startswith('lcnaf:')]
            if len(lc) == 1:
                n['lc'] = lc[0]
            row = lives.get(found[0])
            if row and (life := life_years(row)):
                n['life'] = life
    return keyed


def main():
    page = SOURCE.read_text(encoding='utf-8')
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1))
    data['snapshot'] = re.search(r'Built (\d{4}-\d\d-\d\d)', page).group(1)
    # The site draws its lines from ``links`` with its own link controls (top k per person, minimum
    # co-citation); the research page's fixed top-5 lines and their pair counts are not sent.
    data.pop('co')
    for view in data['views'].values():
        view.pop('edges')
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
    keyed = attach_keys(data['nodes'])
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
          f"{linked} linked to Dissertation reading, {keyed} keyed, snapshot {data['snapshot']}")


if __name__ == '__main__':
    main()
