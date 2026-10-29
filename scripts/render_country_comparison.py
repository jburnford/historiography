#!/usr/bin/env python3
"""Render a two-country comparison page for the dissertation citation graph.

Reads the per-country citation counts in ``works.csv`` and ``cited-people.csv`` (columns
``cited_by_<CC>``, strict History PhDs only), the strict counts in ``dissertations.csv``, and each
country's TF-IDF families (``summary/countries/<CC>/tfidf-families/families.json``). Writes one
self-contained HTML page (inline SVG, no external assets) to
``summary/comparisons/<a>-<b>.html``. Re-run after every ingest round:

    python3 scripts/render_country_comparison.py --countries CA US

Shares are per country: the percentage of that country's strict History PhDs that cite the work
or person. Works are the graph's resolved work nodes; a few title variants stay unmerged, so
counts are slight undercounts.

When the second country is the US, a like-for-like section compares both countries' PhDs from
2010 on, with the US weighted by programme against the AHA directory
(``dissertation_weights.py``), plus a per-decade coverage table. It needs per-dissertation
citation links (``strict-citations.csv.gz`` from the builder, else the newest public release)
and is skipped with a warning if those links do not reproduce ``works.csv``.
"""
import argparse
import csv
import html
import json
from collections import Counter
from datetime import date
from pathlib import Path

import dissertation_weights as dw

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
NAMES = {'CA': 'Canada', 'US': 'United States', 'GB': 'United Kingdom'}
PROSE = {'US': 'the United States', 'GB': 'the United Kingdom'}
esc = lambda s: html.escape(str(s if s is not None else ''), quote=True)


def strict_counts():
    c = Counter()
    for r in csv.DictReader(open(D / 'dissertations.csv', newline='', encoding='utf-8')):
        if r.get('in_analysis') in ('True', 'true', '1'):
            c[r.get('country') or 'CA'] += 1
    return c


def load_rows(name, a, b):
    rows = []
    for r in csv.DictReader(open(D / name, newline='', encoding='utf-8')):
        ka, kb = int(r.get(f'cited_by_{a}') or 0), int(r.get(f'cited_by_{b}') or 0)
        if ka + kb:
            rows.append(dict(r, ka=ka, kb=kb))
    return rows


def short_author(s):
    s = (s or '').split(';')[0].strip()
    s = s.split(',')[0] if ',' in s else s
    return s.title() if s.isupper() else s


def work_label(r):
    t = (r.get('title') or '').split(':')[0].strip()
    lab = f"{short_author(r.get('authors'))}, {t}"
    return lab if len(lab) <= 52 else lab[:50].rstrip() + '…'


def dumbbell(items, a, b, na, nb, title_id):
    """Horizontal dumbbell: one row per item, a dot for each country's share."""
    row_h, left, right, top = 26, 380, 40, 40
    width = 900
    vmax = max(max(i['sa'], i['sb']) for i in items)
    vmax = max(2.0, (int(vmax / 2) + 1) * 2)
    plot_w = width - left - right
    x = lambda v: left + plot_w * v / vmax
    h = top + row_h * len(items) + 30
    out = [f'<svg class="dumbbell" viewBox="0 0 {width} {h}" role="img" aria-labelledby="{title_id}">']
    for t in range(0, int(vmax) + 1, 2):
        out.append(f'<line class="grid" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 8}" y2="{h - 26}"/>'
                   f'<text class="tick" x="{x(t):.1f}" y="{top - 14}" text-anchor="middle">{t}%</text>'
                   f'<text class="tick" x="{x(t):.1f}" y="{h - 10}" text-anchor="middle">{t}%</text>')
    for k, i in enumerate(items):
        y = top + row_h * k + row_h / 2
        tip = i.get('tip') or (f"{i['label']}|{na}: {i['ka']} PhDs ({i['sa']:.1f}%)|{nb}: {i['kb']} PhDs ({i['sb']:.1f}%)")
        out.append(f'<g class="row" data-tip="{esc(tip)}">'
                   f'<rect class="hit" x="0" y="{y - row_h / 2:.1f}" width="{width}" height="{row_h}"/>'
                   f'<text class="lab" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{esc(i["label"])}</text>'
                   f'<line class="link" x1="{x(i["sa"]):.1f}" x2="{x(i["sb"]):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>'
                   f'<circle class="dot s1" cx="{x(i["sa"]):.1f}" cy="{y:.1f}" r="5"/>'
                   f'<circle class="dot s2" cx="{x(i["sb"]):.1f}" cy="{y:.1f}" r="5"/></g>')
    out.append('</svg>')
    return '\n'.join(out)


def table(items, na, nb, cols=('label',), extra=None):
    head = '<tr><th>Work or person</th>' + f'<th class="num">{esc(na)} PhDs</th><th class="num">{esc(na)} %</th>' \
           f'<th class="num">{esc(nb)} PhDs</th><th class="num">{esc(nb)} %</th></tr>'
    body = ''.join(f'<tr><td>{esc(i["label"])}</td><td class="num">{i["ka"]}</td><td class="num">{i["sa"]:.1f}</td>'
                   f'<td class="num">{i["kb"]}</td><td class="num">{i["sb"]:.1f}</td></tr>' for i in items)
    return f'<table><thead>{head}</thead><tbody>{body}</tbody></table>'


def weighted_section(a, b, na, nb, works, people, top):
    """Like-for-like comparison from dw.SINCE: country a unweighted, US weighted by programme."""
    citations, authorship = dw.citation_files()
    if not citations:
        print('weighted section skipped: no per-dissertation citation links')
        return []
    rows_a, rows_b = dw.strict_rows(a), dw.strict_rows(b)
    aha = dw.load_aha()
    w, rep = dw.weights(rows_b, aha)
    win_a = {d for d, _, y in rows_a if y and y >= dw.SINCE}
    all_b = {d for d, _, _ in rows_b}
    by_work, by_person = dw.citing_sets(win_a | all_b, citations, authorship)
    # The links must reproduce works.csv's US counts, or they come from another build.
    stale = [r['work_id'] for r in sorted(works, key=lambda r: -r['kb'])[:50]
             if len(by_work.get(r['work_id'], set()) & all_b) != r['kb']]
    if stale:
        print(f'weighted section skipped: {citations} does not match works.csv ({len(stale)} of the top 50 US works differ)')
        return []
    n_a, n_b = len(win_a), len(w)

    def shares(r, citing):
        ca, us = citing & win_a, citing & w.keys()
        sa, sraw = 100 * len(ca) / n_a, 100 * len(us) / n_b
        sb = 100 * sum(w[d] for d in us) / n_b
        return dict(r, ka=len(ca), kb=len(us), sa=sa, sb=sb, sraw=sraw,
                    tip=f"{r['label']}|{na} {dw.SINCE}–: {len(ca)} PhDs ({sa:.1f}%)|"
                        f"{nb} {dw.SINCE}–, weighted: {sb:.1f}% (unweighted {len(us)} PhDs, {sraw:.1f}%)")

    wworks = [shares(r, by_work.get(r['work_id'], set())) for r in works]
    wpeople = [shares(r, by_person.get(r['person_key'], set())) for r in people]
    canon = sorted(wworks, key=lambda r: -(r['sa'] + r['sb']))[:top]
    canon_people = sorted(wpeople, key=lambda r: -(r['sa'] + r['sb']))[:top]
    movers = sorted((r for r in wworks if r['kb'] >= 25), key=lambda r: -abs(r['sb'] - r['sraw']))[:15]

    def wtable(items):
        head = (f'<tr><th>Work or person</th><th class="num">{esc(na)} PhDs</th><th class="num">{esc(na)} %</th>'
                f'<th class="num">{esc(nb)} PhDs</th><th class="num">{esc(nb)} % unweighted</th>'
                f'<th class="num">{esc(nb)} % weighted</th></tr>')
        body = ''.join(f'<tr><td>{esc(i["label"])}</td><td class="num">{i["ka"]}</td><td class="num">{i["sa"]:.1f}</td>'
                       f'<td class="num">{i["kb"]}</td><td class="num">{i["sraw"]:.1f}</td><td class="num">{i["sb"]:.1f}</td></tr>'
                       for i in items)
        return f'<table><thead>{head}</thead><tbody>{body}</tbody></table>'

    decades = dw.decade_coverage(rows_b, aha)
    dec_rows = ''.join(
        f'<tr><td>{"before 1960" if c["period"] < 1960 else str(c["period"]) + "s"}</td><td class="num">{c["n"]:,}</td><td class="num">{c["institutions"]}</td>'
        f'<td class="num">{c["aha"]:,}</td><td class="num">{100 * c["aha_covered"]:.0f}%</td>'
        f'<td>{esc(c["top"])} ({100 * c["top_share"]:.0f}%)</td>'
        f'<td>{"weighted" if c["period"] >= dw.SINCE else "too thin to weight"}</td></tr>' for c in decades)
    cov = dw.coverage({s for _, s, _ in rows_b}, since=dw.SINCE, aha=aha)
    def university(dept):  # 'Univ. of California, Los Angeles, Meyer and Renee Luskin Dept. of History' -> 'Univ. of California, Los Angeles'
        keep = []
        for part in dept.split(', '):
            if any(k in part for k in ('Dept', 'Program', 'History')):
                break
            keep.append(part)
        return ', '.join(keep) or dept
    missing = '; '.join(f'{university(n)} ({k})' for n, k in cov['missing_top'])
    print(f"weighted section: {n_a} {a} and {n_b} {b} PhDs from {dw.SINCE}; effective {b} n {rep['n_eff']:.0f}")
    return [f'<h2 id="t-weighted">Like for like, {dw.SINCE}–: {na} and {PROSE.get(b, nb)} weighted by programme</h2>',
            f'<p class="note">The {nb} corpus over-represents universities with open repositories. Here both countries are '
            f'limited to PhDs from {dw.SINCE} on, and each {nb} PhD is weighted so that institutions count in proportion to '
            f'their completed History PhDs in the AHA directory, decade by decade (<code>scripts/dissertation_weights.py</code>). '
            f'{nb}: {n_b:,} PhDs at {rep["institutions"]} institutions, effective sample about {rep["n_eff"]:,.0f}. '
            f'{na}: {n_a:,} PhDs, unweighted. Weighting cannot add programmes we hold nothing from: since {dw.SINCE} the institutions held '
            f'award {100 * cov["share_held"]:.0f}% of US History PhDs, and these top-{cov["top"]} programmes have none: {esc(missing)}.</p>',
            '<div class="tiles">',
            f'<div class="tile"><div class="v">{n_a:,}</div><div class="k">{na} PhDs, {dw.SINCE}–</div></div>',
            f'<div class="tile"><div class="v">{n_b:,}</div><div class="k">{nb} PhDs, {dw.SINCE}–</div></div>',
            f'<div class="tile"><div class="v">{rep["n_eff"]:,.0f}</div><div class="k">{nb} effective sample after weighting</div></div>',
            f'<div class="tile"><div class="v">{100 * cov["share_held"]:.0f}%</div><div class="k">of {nb} History PhDs since {dw.SINCE} are at institutions we hold</div></div>',
            '</div>',
            f'<h3>Shared canon, {dw.SINCE}–</h3>',
            dumbbell(canon, a, b, na, nb, 't-weighted'),
            f'<details><summary>Table view</summary>{wtable(canon)}</details>',
            f'<h3>Most-cited people, {dw.SINCE}–</h3>',
            dumbbell(canon_people, a, b, na, nb, 't-weighted'),
            f'<details><summary>Table view</summary>{wtable(canon_people)}</details>',
            f'<h3>What weighting changes</h3>',
            f'<p class="note">{nb} works cited by at least 25 PhDs since {dw.SINCE}, with the largest gap between weighted and unweighted share.</p>',
            wtable(movers),
            f'<h3>How far back the {nb} corpus reaches</h3>',
            f'<p class="note">Per decade: our strict {nb} History PhDs, the institutions they come from, the share of the AHA directory\'s '
            f'{nb} History PhDs awarded by those institutions in that decade, and the largest single institution. Before {dw.SINCE} '
            f'one or two universities supply most of each decade, so weighting would magnify them; those decades are not weighted '
            f'and do not represent {PROSE.get(b, nb)}.</p>',
            f'<table><thead><tr><th>Decade</th><th class="num">PhDs</th><th class="num">Institutions</th>'
            f'<th class="num">AHA PhDs (all US)</th><th class="num">AHA output covered</th><th>Largest institution</th>'
            f'<th>Use</th></tr></thead><tbody>{dec_rows}</tbody></table>']


def families(cc):
    p = D / 'summary/countries' / cc / 'tfidf-families/families.json'
    if not p.exists():
        return None
    return json.load(open(p))


def family_name(f):
    names = []
    for w in f['top_works']:
        a = short_author(w.get('first_author'))
        if a and a not in names:
            names.append(a)
        if len(names) == 3:
            break
    return ' · '.join(names)


def nearest_field(f):
    return (f.get('louvain_hint') or '').replace(' (provisional)', '')


def family_card(f):
    label = family_name(f)
    near = nearest_field(f)
    works = '; '.join(f"{short_author(w.get('first_author'))}, <i>{esc((w.get('title') or '').split(':')[0])}</i>"
                      for w in f['top_works'][:5])
    flag = ' <span class="flag">unstable</span>' if f.get('unstable') else ''
    return (f'<li><strong>{esc(label)}</strong>{flag}<span class="meta"> · {f["dominated_dissertations"]} PhDs · '
            f'stability {f["bootstrap_stability"]:.2f}' + (f' · nearest field: {esc(near)}' if near else '')
            + f'</span><br><span class="works">{works}</span></li>')


def match_families(fa, fb, n=25):
    pairs = []
    for x in fa['families']:
        sx = {w['id'] for w in x['top_works'][:n]}
        for y in fb['families']:
            sy = {w['id'] for w in y['top_works'][:n]}
            j = len(sx & sy) / len(sx | sy)
            if j > 0:
                pairs.append((j, x, y, sx & sy))
    pairs.sort(key=lambda p: -p[0])
    used_a, used_b, out = set(), set(), []
    for j, x, y, shared in pairs:
        if x['id'] in used_a or y['id'] in used_b or j < 0.08:
            continue
        used_a.add(x['id']); used_b.add(y['id'])
        out.append((j, x, y, shared))
    return out


CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ed;--text-primary:#0b0b0b;--text-secondary:#52514e;
 --text-muted:#76756f;--grid:#e3e2dd;--series-1:#2a78d6;--series-2:#eb6834;--link:#b8b7b0}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#242422;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;
 --series-2:#d95926;--link:#5b5a54}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;--series-2:#d95926;--link:#5b5a54}
body{margin:0}
.viz-root{background:var(--surface-1);color:var(--text-primary);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
 padding:28px max(20px,calc(50vw - 520px))}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 6px}h3{font-size:15px;margin:18px 0 6px}
p.lede,.note{color:var(--text-secondary);max-width:820px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}
.tile{background:var(--surface-2);border-radius:8px;padding:12px 14px}.tile .v{font-size:26px;font-weight:600}
.tile .k{color:var(--text-secondary);font-size:13px}
.legend{display:flex;gap:18px;color:var(--text-secondary);font-size:13px;margin:6px 0}
.legend span::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
.legend .l1::before{background:var(--series-1)}.legend .l2::before{background:var(--series-2)}
svg.dumbbell{width:100%;height:auto;display:block}
svg .grid{stroke:var(--grid);stroke-width:1}svg .tick{fill:var(--text-muted);font-size:11px}
svg .lab{fill:var(--text-primary);font-size:12.5px}svg .link{stroke:var(--link);stroke-width:2}
svg .dot{stroke:var(--surface-1);stroke-width:2}svg .s1{fill:var(--series-1)}svg .s2{fill:var(--series-2)}
svg .hit{fill:transparent}svg .row:hover .hit{fill:var(--surface-2)}
#tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--grid);
 border-radius:6px;padding:6px 9px;font-size:12.5px;box-shadow:0 2px 10px rgba(0,0,0,.12);display:none;max-width:340px}
details{margin:8px 0 0}summary{cursor:pointer;color:var(--text-secondary);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}th,td{text-align:left;padding:4px 8px;
 border-bottom:1px solid var(--grid)}th{color:var(--text-secondary);font-weight:600}td.num,th.num{text-align:right;
 font-variant-numeric:tabular-nums}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media (max-width:760px){.cols{grid-template-columns:1fr}}
ol.fam{padding-left:20px}ol.fam li{margin:0 0 10px}.meta{color:var(--text-muted);font-size:12.5px}
.works{color:var(--text-secondary);font-size:13px}.flag{font-size:11px;border:1px solid var(--text-muted);
 border-radius:4px;padding:0 4px;color:var(--text-secondary)}
.k1{color:var(--text-primary);border-left:3px solid var(--series-1);padding-left:6px}
.k2{color:var(--text-primary);border-left:3px solid var(--series-2);padding-left:6px}
"""

JS = """
const tip=document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(g=>{
 g.addEventListener('mousemove',e=>{const p=g.dataset.tip.split('|');
  tip.innerHTML='<strong>'+p[0]+'</strong><br>'+p.slice(1).join('<br>');tip.style.display='block';
  tip.style.left=Math.min(e.clientX+14,innerWidth-360)+'px';tip.style.top=(e.clientY+14)+'px';});
 g.addEventListener('mouseleave',()=>tip.style.display='none');});
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--countries', nargs=2, default=['CA', 'US'])
    ap.add_argument('--top', type=int, default=25)
    args = ap.parse_args()
    a, b = args.countries
    na, nb = NAMES.get(a, a), NAMES.get(b, b)
    strict = strict_counts()
    Na, Nb = strict[a], strict[b]
    works = load_rows('works.csv', a, b)
    people = load_rows('cited-people.csv', a, b)
    for r in works:
        r.update(label=work_label(r), sa=100 * r['ka'] / Na, sb=100 * r['kb'] / Nb)
    for r in people:
        r.update(label=r.get('name') or r.get('person_key'), sa=100 * r['ka'] / Na, sb=100 * r['kb'] / Nb)

    # shared canon: the works with the highest combined share
    shared = sorted(works, key=lambda r: -(r['sa'] + r['sb']))[:args.top]
    shared_people = sorted(people, key=lambda r: -(r['sa'] + r['sb']))[:args.top]
    # most national: large share in one country, little in the other (min 25 PhDs in the leading country)
    nat_a = sorted((r for r in works if r['ka'] >= 25), key=lambda r: -(r['sa'] - 3 * r['sb']))[:20]
    nat_b = sorted((r for r in works if r['kb'] >= 25), key=lambda r: -(r['sb'] - 3 * r['sa']))[:20]
    top_a = {r['work_id'] for r in sorted(works, key=lambda r: -r['ka'])[:500]}
    top_b = {r['work_id'] for r in sorted(works, key=lambda r: -r['kb'])[:500]}
    both500 = len(top_a & top_b)

    fa, fb = families(a), families(b)
    note_b = D / 'summary/countries' / b / 'NOTE.json'
    provisional = note_b.exists()

    parts = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
             f'<title>{na} and {PROSE.get(b, nb)}: History PhD citations compared</title><style>{CSS}</style></head><body><div class="viz-root">',
             f'<h1>{na} and {PROSE.get(b, nb)}: what History PhDs cite</h1>',
             f'<p class="lede">Bibliographies of strict History PhDs in the dissertation citation graph, compared country by country. '
             f'Shares are the percentage of each country\'s PhDs that cite a work or person. Generated {date.today().isoformat()} '
             f'by <code>scripts/render_country_comparison.py</code>.'
             + (f' The {nb} sub-graph is <strong>provisional</strong>: it is just under the 2,000-dissertation threshold'
                + {'GB': ' and Edinburgh theses are still being added.', 'US': ' and Harvard is still being added.'}.get(b, '.')
                if provisional else '') + '</p>',
             '<div class="tiles">',
             f'<div class="tile"><div class="v">{Na:,}</div><div class="k">{na}: strict History PhDs</div></div>',
             f'<div class="tile"><div class="v">{Nb:,}</div><div class="k">{nb}: strict History PhDs</div></div>',
             f'<div class="tile"><div class="v">{both500}</div><div class="k">works in both countries\' top 500</div></div>',
             f'<div class="tile"><div class="v">{len(fa["families"]) if fa else "–"} / {len(fb["families"]) if fb else "–"}</div>'
             f'<div class="k">TF-IDF families ({na} / {nb})</div></div>', '</div>',
             (f'<p class="note">Shares in the next sections are unweighted and cover all years. The {nb} corpus is mostly '
              f'2010s and leans to universities with open repositories; for a like-for-like comparison see '
              f'<a href="#t-weighted">{dw.SINCE}– weighted by programme</a>.</p>' if b == 'US' else ''),
             f'<div class="legend"><span class="l1">{na}</span><span class="l2">{nb}</span></div>',
             f'<h2 id="t-works">The shared canon: most-cited works across both countries</h2>',
             f'<p class="note">Top {args.top} works by combined share. A long bar means one country cites the work far more.</p>',
             dumbbell(shared, a, b, na, nb, 't-works'),
             f'<details><summary>Table view</summary>{table(shared, na, nb)}</details>',
             f'<h2 id="t-people">Most-cited people across both countries</h2>',
             dumbbell(shared_people, a, b, na, nb, 't-people'),
             f'<details><summary>Table view</summary>{table(shared_people, na, nb)}</details>',
             '<h2>National literatures: works one country cites and the other barely does</h2>',
             f'<p class="note">Works cited by at least 25 PhDs in the leading country, ranked by how lopsided they are.</p>',
             '<div class="cols">',
             f'<div><h3 class="k1">Mostly {na}</h3>{table(nat_a, na, nb)}</div>',
             f'<div><h3 class="k2">Mostly {nb}</h3>{table(nat_b, na, nb)}</div>', '</div>']
    if b == 'US':
        parts += weighted_section(a, b, na, nb, works, people, args.top)
    if fa and fb:
        parts += ['<h2>Families of sources (TF-IDF and NMF)</h2>',
                  '<p class="note">Each family is a group of works that tend to appear together in bibliographies, after '
                  'down-weighting works that nearly everyone cites. Each is named by the authors of its most characteristic works; '
                  '"nearest field" is the closest co-citation field, for orientation only. Stability is the mean match across '
                  'bootstrap refits (1 = always reproduced).</p>',
                  '<div class="cols">',
                  f'<div><h3 class="k1">{na} ({len(fa["families"])} families)</h3><ol class="fam">'
                  + ''.join(family_card(f) for f in fa['families']) + '</ol></div>',
                  f'<div><h3 class="k2">{nb} ({len(fb["families"])} families)</h3><ol class="fam">'
                  + ''.join(family_card(f) for f in fb['families']) + '</ol></div>', '</div>']
        pairs = match_families(fa, fb)
        if pairs:
            rows = ''.join(
                f'<tr><td>{esc(family_name(x))}</td>'
                f'<td>{esc(family_name(y))}</td><td class="num">{j:.2f}</td>'
                f'<td>{esc("; ".join(sorted(short_author(w["first_author"]) for w in x["top_works"][:25] if w["id"] in shared_ids)[:6]))}</td></tr>'
                for j, x, y, shared_ids in pairs)
            parts += ['<h3>Families that cross the border</h3>',
                      '<p class="note">Pairs of families whose 25 most characteristic works overlap (Jaccard similarity), '
                      'with authors of the shared works.</p>',
                      f'<table><thead><tr><th>{na} family</th><th>{nb} family</th><th class="num">Overlap</th>'
                      f'<th>Shared works by</th></tr></thead><tbody>{rows}</tbody></table>']
    parts += ['<h2>Notes and limits</h2><ul class="note">',
              '<li>Only strict History PhDs count; non-History and unparsed theses are excluded.</li>',
              '<li>Works are resolved citation records; a few title variants remain unmerged, so counts are slight undercounts.</li>',
              f'<li>The {nb} corpus leans towards universities with open repositories and towards the 2010s; several of the '
              'largest programmes are missing (see the weighted section). Families cover only theses that cite at least 3 widely '
              'cited works, which under-represents older theses.</li>',
              '<li>Source data: <code>works.csv</code>, <code>cited-people.csv</code>, <code>dissertations.csv</code> and '
              '<code>summary/countries/&lt;CC&gt;/tfidf-families/</code>.</li></ul>',
              f'<div id="tip"></div><script>{JS}</script></div></body></html>']
    out = D / 'summary/comparisons' / f'{a.lower()}-{b.lower()}.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(parts), encoding='utf-8')
    print(f'wrote {out.relative_to(ROOT)} ({Na} {a}, {Nb} {b}; {both500} works in both top 500s)')


if __name__ == '__main__':
    main()
