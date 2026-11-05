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
  'Thompson, E. P.' and 'Du Bois, W. E. B.'); ``name`` stays as the graph keys it. When the person's key holds an
  LC authority whose given names disagree with ``name`` (one citation's form, sometimes a namesake's), the label is
  the key's heading without dates.
Each sub-graph (``SCOPES``) gets its own file, ``site/canon-map-<CC>.json``, from the page that
``historian_cocitation_network.py --country CC`` writes; ``scope`` and ``scopes`` let the site switch.
The output hash, the source hash and the snapshot go into data/dissertation-layer/manifest.json under
``canon_map`` (and ``canon_map_scopes`` for the sub-graphs); scripts/build_site.py publishes the file only when the hash matches.
"""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/field-research/dissertation-citations-2026-10-11/summary/comparisons/historian-network.html'
LAYER = ROOT / 'data/dissertation-layer'
OUT = LAYER / 'site' / 'canon-map.json'
CROSSWALK = ROOT / 'data/field-research/dissertation-citations-2026-10-11/person-key-crosswalk-2026-11-03.csv'
INITIALS = re.compile(r'^(?:[A-Za-z]\.)*[A-Za-z]\.?$')


def label(name):
    surname, sep, given = name.partition(', ')
    if not sep:
        return name
    parts = [' '.join(f'{c.upper()}.' for c in tok.replace('.', '')) if INITIALS.match(tok) else tok for tok in given.split()]
    return f"{surname}, {' '.join(parts)}"


NAMES = {'Canada': 'CA', 'United States': 'US', 'Britain': 'GB', 'Brazil': 'BR', 'Rest of Europe': 'EU', 'elsewhere': 'OTHER'}


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


def attach_keys(nodes, pairs=None):
    """``key`` and ``key_status`` from the identifier log (PID-PLAN.md), via the person's graph key.

    People deferred for merge review have no key yet and carry neither field."""
    from identifiers import State
    from key_canon_map import canon_keys
    from namesake_check_groups import given_names_agree
    state = State.load(ROOT / 'data/identifiers')
    graph_key = canon_keys(nodes, *([pairs] if pairs else []))
    with (ROOT / 'data/person-facts/life-dates.csv').open(newline='', encoding='utf-8') as f:
        lives = {r['key']: r for r in csv.DictReader(f)}
    # Graph keys renamed by the split-key fixes of 2026-11-03 ('hobsbawn|eric j' -> 'hobsbawm|eric') reach
    # the key log through their old keys until the log anchors the new ones.
    renamed = defaultdict(list)
    if CROSSWALK.exists():
        with CROSSWALK.open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                renamed[r['new_key']].append(r['old_key'])
    keyed = 0
    for n in nodes:
        gk = graph_key[n['name'], n['qid']]
        found = state.lookup(f"diss-person:{gk}")
        if not found:
            found = sorted({k for old in renamed.get(gk, []) for k in state.lookup(f'diss-person:{old}')})
        if len(found) == 1:
            n['key'] = found[0]
            n['key_status'] = state.keys[found[0]]['resolution']
            keyed += 1
            lc = [a.split(':', 1)[1] for a in state.keys[found[0]]['anchors'] if a.startswith('lcnaf:')]
            if len(lc) == 1:
                n['lc'] = lc[0]
                # The graph's display name is one citation's form and can name someone else ('Silva, Maria
                # Aparecida de Aquino' for Maria Beatriz Nizza da Silva's books; namesake-check-2026-11-04): when
                # its given names disagree with the LC-anchored key's, the key's heading is shown.
                head = re.sub(r'\s*\([^)]*\)|,\s*(?:approximately\s+|active\s+)?\d{3,4}\??-.*$', '', state.keys[found[0]]['label']).strip()
                if not given_names_agree(n['name'], head):
                    n['label'] = head
            row = lives.get(found[0])
            if row and (life := life_years(row)):
                n['life'] = life
    return keyed


SCOPES = ['BR', 'CA', 'GB', 'US']  # sub-graph maps (user, 2026-11-03: "select a sub-graph and see its map")


def export(scope=None):
    """Write the site file for the main map or one sub-graph's; return its manifest entry."""
    source = SOURCE if not scope else SOURCE.parents[1] / 'countries' / scope / 'comparisons' / SOURCE.name
    out = OUT if not scope else OUT.with_name(f'canon-map-{scope}.json')
    page = source.read_text(encoding='utf-8')
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1))
    data['snapshot'] = re.search(r'Built (\d{4}-\d\d-\d\d)', page).group(1)
    # The site draws its lines from ``links`` with its own link controls (top k per person, minimum
    # co-citation); the research page's fixed top-5 lines and their pair counts are not sent.
    data.pop('co')
    for view in data['views'].values():
        view.pop('edges')
    counts = re.search(r'next\s+region\'s \(([^)]*) theses\)', page).group(1)
    data['region_theses'] = {NAMES[m.group(1)]: int(m.group(2).replace(',', ''))
                             for m in re.finditer(r'(Canada|United States|Britain|Brazil|Rest of Europe|elsewhere) ([\d,]+)', counts)}
    assert set(data['region_theses']) == set(NAMES.values()), data['region_theses']
    data['scope'] = scope or 'main'
    data['scopes'] = ['main', *SCOPES]
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
    keyed = attach_keys(data['nodes'], source.parents[1] / 'network' / 'historian-cocitation-pairs.csv' if scope else None)
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    out.write_text(text, encoding='utf-8')
    print(f"wrote {out.relative_to(ROOT)} ({len(text) / 1e6:.2f} MB): {len(data['nodes'])} people, "
          f"{linked} linked to Dissertation reading, {keyed} keyed, snapshot {data['snapshot']}")
    return dict(snapshot=data['snapshot'], source=str(source.relative_to(ROOT)),
                source_sha256=hashlib.sha256(page.encode('utf-8')).hexdigest(),
                output=str(out.relative_to(LAYER)), output_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())


def main():
    manifest_path = LAYER / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['canon_map'] = export()
    manifest['canon_map_scopes'] = {scope: export(scope) for scope in SCOPES}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
