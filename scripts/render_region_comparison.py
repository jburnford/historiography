#!/usr/bin/env python3
"""Render the five-region citation comparison page: Canada, the United States, Britain, France and the
rest of Europe.

User (2026-10-22): "could you create a webpage with this comparison visualized". Reads the
region tables written by ``region_top_citations.py`` (``summary/regions/top-people.csv``,
``top-works.csv``) and the strict thesis counts in ``dissertations.csv``, and writes one
self-contained page (inline SVG, no external assets) to
``summary/comparisons/europe-ca-us.html``. Re-run after ``region_top_citations.py``:

    python3 scripts/region_top_citations.py --out <D>
    python3 scripts/render_region_comparison.py

Shares are per region: the percentage of the region's strict History PhDs that cite the person
or work (presence, one count per thesis). Colours: Canada blue, United States orange, Britain
purple, France green, and the rest of Europe a hollow green ring. User (2026-10-30): "make France
its own and then Europe (other) for the rest"; until then Europe was pooled.
"""
import csv
from collections import Counter
from datetime import date
import html
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from region_top_citations import REGIONS, REGION_NAMES, regions_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
REG = D / 'summary' / 'regions'
esc = lambda s: html.escape(str(s if s is not None else ''), quote=True)  # noqa: E731
SERIES = [('CA', 'Canada', 's1', 'dot'), ('US', 'United States', 's2', 'dot'), ('GB', 'Britain', 's4', 'dot'),
          ('FR', 'France', 's3', 'dot'), ('EUO', 'Rest of Europe', 's3', 'ring')]


def proper(name):
    """Normal case for surnames printed in capitals ('RICOEUR, Paul', 'LE GOFF, Jacques')."""
    def fix(word):
        return '-'.join(p[:1] + p[1:].lower() if len(p) > 1 and p.isupper() else p for p in word.split('-'))
    return ' '.join(fix(w) for w in name.split(' '))


AUTHORS = {}  # work id -> printed first-author surname, filled from works.csv in main()


def work_label(r):
    surname = AUTHORS.get(r['id']) or r['id'].split(':', 1)[1].split('|', 1)[0].title()
    return f"{surname}, {r['label']}"


def load(name):
    rows = list(csv.DictReader((REG / name).open(newline='', encoding='utf-8')))
    for r in rows:
        for k in list(r):
            if k.startswith('share_'):
                r[k] = float(r[k])
        r['label'] = proper(r['label']) if name == 'top-people.csv' else work_label(r)
    return rows


def unique(rows):
    seen = {}
    for r in rows:
        seen.setdefault(r['id'], r)
    return list(seen.values())


def top(rows, region, n):
    return [r for r in rows if r['region'] == region][:n]


def nice_max(v):
    for m in (2, 4, 5, 8, 10, 12, 15, 20, 25, 30, 40, 50):
        if v <= m:
            return m
    return 100


def dotplot(rows, title_id, label_width=345):
    """Cleveland dot plot: one row per item, four marks on a shared percentage axis."""
    vmax = nice_max(max(max(r[f'share_{c}'] for c, *_ in SERIES) for r in rows))
    step = {2: 0.5, 4: 1, 5: 1, 8: 2, 10: 2, 12: 2, 15: 5, 20: 5, 25: 5, 30: 5, 40: 10, 50: 10}.get(vmax, 20)
    W, rh, top_, x0, x1 = 900, 26, 34, label_width, 880
    H = top_ + rh * len(rows) + 30
    x = lambda v: x0 + (x1 - x0) * v / vmax  # noqa: E731
    out = [f'<svg class="dots" viewBox="0 0 {W} {H}" role="img" aria-labelledby="{title_id}">']
    t = 0.0
    while t <= vmax + 1e-9:
        out.append(f'<line class="grid" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top_ - 6}" y2="{H - 24}"/>'
                   f'<text class="tick" x="{x(t):.1f}" y="{top_ - 12}" text-anchor="middle">{t:g}%</text>'
                   f'<text class="tick" x="{x(t):.1f}" y="{H - 8}" text-anchor="middle">{t:g}%</text>')
        t += step
    for i, r in enumerate(rows):
        y = top_ + rh * i + rh / 2
        vals = [r[f'share_{c}'] for c, *_ in SERIES]
        tip = ' · '.join(f'{name} {r[f"share_{c}"]:.1f}%' for c, name, *_ in SERIES)
        label = r['label'] if len(r['label']) <= 48 else r['label'][:46].rstrip(' ,:') + '…'
        out.append(f'<g class="row" data-tip="{esc(r["label"])}|{esc(tip)}">'
                   f'<rect class="hit" x="0" y="{y - rh / 2:.1f}" width="{W}" height="{rh}"/>'
                   f'<text class="lab" x="{x0 - 12}" y="{y + 4:.1f}" text-anchor="end">{esc(label)}</text>'
                   f'<line class="link" x1="{x(min(vals)):.1f}" x2="{x(max(vals)):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>')
        # the hollow ring is drawn first and larger, so a filled dot at the same value sits inside it
        for c, name, cls, shape in sorted(SERIES, key=lambda s: s[3] != 'ring'):
            v = r[f'share_{c}']
            if shape == 'ring':
                out.append(f'<circle class="ring {cls}" cx="{x(v):.1f}" cy="{y:.1f}" r="7.5"/>')
            else:
                out.append(f'<circle class="dot {cls}" cx="{x(v):.1f}" cy="{y:.1f}" r="5.5"/>')
        out.append('</g>')
    out.append('</svg>')
    return '<div class="scroll">' + '\n'.join(out) + '</div>'


def table(rows, caption):
    head = ''.join(f'<th>{esc(name)}</th>' for _, name, *_ in SERIES)
    body = ''.join(f'<tr><td>{esc(r["label"])}</td>' + ''.join(f'<td>{r[f"share_{c}"]:.1f}%</td>' for c, *_ in SERIES) + '</tr>'
                   for r in rows)
    return (f'<details><summary>Table: {esc(caption)}</summary><table><thead><tr><th></th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></details>')


def section(heading, hid, intro, rows, caption):
    return (f'<h2 id="{hid}">{esc(heading)}</h2><p class="note">{intro}</p>{LEGEND}{dotplot(rows, hid)}{table(rows, caption)}')


LEGEND = ('<div class="legend"><span class="l1">Canada</span><span class="l2">United States</span>'
          '<span class="l5">Britain</span><span class="l3">France</span><span class="l4">Rest of Europe</span></div>')


IN = {'CA': 'Canada', 'US': 'the United States', 'GB': 'Britain', 'FR': 'France', 'EUO': 'the rest of Europe'}


def overall(rows, n):
    """Ranked by the mean of the five regional shares, so no single region sets the list."""
    return sorted(unique(rows), key=lambda r: -sum(r[f'share_{c}'] for c in REGIONS) / len(REGIONS))[:n]


def distinctive(region, n):
    rows = [r for r in csv.DictReader((REG / 'distinctive.csv').open(newline='', encoding='utf-8')) if r['lead'] == region]
    for r in rows:
        for k in list(r):
            if k.startswith('share_'):
                r[k] = float(r[k])
        r['label'] = work_label(r)
    return sorted(rows, key=lambda r: -float(r['lead_margin']))[:n]


def main():
    counts = Counter()
    for r in csv.DictReader((D / 'dissertations.csv').open(newline='', encoding='utf-8')):
        if r['in_analysis'] == 'True':
            for g in regions_of(r['country']):
                counts[g] += 1
    wanted = {r['id'] for r in csv.DictReader((REG / 'top-works.csv').open(newline='', encoding='utf-8'))}
    wanted |= {r['id'] for r in csv.DictReader((REG / 'distinctive.csv').open(newline='', encoding='utf-8'))}
    csv.field_size_limit(10 ** 8)
    for r in csv.DictReader((D / 'works.csv').open(newline='', encoding='utf-8')):
        if r['work_id'] in wanted and r['authors']:
            AUTHORS[r['work_id']] = proper(r['authors'].split(';')[0].split(',')[0].strip())
    people, works = load('top-people.csv'), load('top-works.csv')
    shared = sorted((r for r in unique(works) if min(r[f'share_{c}'] for c in REGIONS) >= 1.0),
                    key=lambda r: -min(r[f'share_{c}'] for c in REGIONS))[:15]
    tiles = ''.join(f'<div class="tile"><div class="v">{counts[c]:,}</div><div class="k">History PhDs: {esc(REGION_NAMES[c])}</div></div>'
                    for c in REGIONS)
    def lead_sentence(c):
        w = top(works, c, 1)[0]
        return (f'The most cited work in {IN[c]} is '
                f'<i>{esc(w["label"].split(" (")[0])}</i>, cited by {w[f"share_{c}"]:.1f}% of its History PhDs.')
    body = [
        '<h1>Who History PhDs cite: Canada, the United States, Britain, France and the rest of Europe</h1>',
        '<p class="lede">The share of each region\'s History PhDs whose bibliography cites a person or work, from the '
        'dissertation citation graph. One count per thesis: a thesis that cites a work twenty times counts once. '
        'Translations and editions of a work mapped through Wikidata count as one work.</p>',
        f'<div class="tiles">{tiles}</div>',
        '<p class="note">Hover over a row for the five values; every chart has a table below it. The regions differ in '
        'size, and the rest of Europe pools many national traditions (Sweden, Germany, Spain, Italy, Belgium and others), '
        'so its shares are thinner than any one country\'s would be.</p>',
        section('The most cited people', 'people',
                'Ranked by the mean of the five regional shares of History PhDs citing any work by the person (first author).',
                overall(people, 25), 'most cited people across the five regions'),
        section('The most cited works', 'works',
                'Ranked by the mean of the five regional shares.', overall(works, 20), 'most cited works across the five regions'),
        *(section(f'The most cited works in {IN[c]}', f'top-{c.lower()}',
                  lead_sentence(c), top(works, c, 15), f'most cited works in {REGION_NAMES[c]}') for c in ('GB', 'FR', 'EUO')),
        *(section(f'Read in {IN[c]} more than anywhere else', f'dist-{c.lower()}',
                  'Works cited by at least 2% of some region\'s History PhDs, whose share here most exceeds the next '
                  'highest region\'s.', distinctive(c, 10), f'works most distinctive of {REGION_NAMES[c]}') for c in REGIONS),
        section('Common ground', 'shared',
                'Works cited by at least 1% of the History PhDs in every one of the five regions, ranked by the lowest of the '
                'five shares.', shared, 'works cited in all five regions'),
        '<h2 id="notes">How to read this</h2><ul class="note">'
        '<li><b>Sources.</b> Strict History PhDs (explicit History programme or department) with a parsed bibliography '
        'or a bibliography rebuilt from their notes. British theses come from UK repositories (the OpenAIRE collection and '
        'Oxford\'s ORA). French and other European theses come mostly from the BASE harvest, where non-English '
        'bibliographies parse less cleanly than English ones, so their shares are, if anything, low.</li>'
        '<li><b>Works.</b> A work is first-author surname plus main title. Translations are merged only where Wikidata maps '
        'them to one work: some remain split (Weber\'s French <i>Économie et société</i>, Foucault\'s French <i>Histoire de '
        'la sexualité</i>), which lowers those works\' shares outside their language.</li>'
        '<li><b>People.</b> First authors only; a person\'s share counts theses citing any of their works.</li>'
        '<li><b>Citation is not engagement.</b> A citation can be a frame, a foil or a ritual reference.</li></ul>',
        f'<p class="note">Built {date.today().isoformat()} from <code>summary/regions/</code> '
        '(<code>scripts/region_top_citations.py</code>, <code>scripts/render_region_comparison.py</code>). '
        'See also <a href="ca-us.html">Canada and the United States</a>, <a href="ca-gb.html">Canada and Britain</a> '
        'and <a href="us-gb.html">the United States and Britain</a>.</p>',
    ]
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Who History PhDs cite: Canada, the United States, Britain, France and the rest of Europe</title>
<style>
.viz-root{{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ed;--text-primary:#0b0b0b;--text-secondary:#52514e;
 --text-muted:#76756f;--grid:#e3e2dd;--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--series-4:#8a5cc9;--link:#b8b7b0}}
@media (prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])) .viz-root{{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#242422;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;
 --series-2:#d95926;--series-3:#199e70;--series-4:#9a70d6;--link:#5b5a54}}}}
:root[data-theme="dark"] .viz-root{{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;--series-4:#9a70d6;--link:#5b5a54}}
body{{margin:0}}
.viz-root{{background:var(--surface-1);color:var(--text-primary);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
 padding:28px max(20px,calc(50vw - 520px))}}
h1{{font-size:26px;margin:0 0 4px}}h2{{font-size:19px;margin:40px 0 6px}}
p.lede,.note{{color:var(--text-secondary);max-width:820px}}ul.note li{{margin:4px 0}}
a{{color:var(--series-1)}}code{{font-size:13px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}}
.tile{{background:var(--surface-2);border-radius:8px;padding:12px 14px}}.tile .v{{font-size:26px;font-weight:600}}
.tile .k{{color:var(--text-secondary);font-size:13px}}
.legend{{display:flex;flex-wrap:wrap;gap:18px;color:var(--text-secondary);font-size:13px;margin:6px 0}}
.legend span::before{{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px;box-sizing:border-box}}
.legend .l1::before{{background:var(--series-1)}}.legend .l2::before{{background:var(--series-2)}}
.legend .l3::before{{background:var(--series-3)}}.legend .l4::before{{border:2px solid var(--series-3)}}.legend .l5::before{{background:var(--series-4)}}
svg.dots{{width:100%;min-width:680px;height:auto;display:block}}.scroll{{overflow-x:auto}}
svg .grid{{stroke:var(--grid);stroke-width:1}}svg .tick{{fill:var(--text-muted);font-size:11px}}
svg .lab{{fill:var(--text-primary);font-size:12.5px}}svg .link{{stroke:var(--link);stroke-width:2}}
svg .dot{{stroke:var(--surface-1);stroke-width:2}}svg .s1{{fill:var(--series-1)}}svg .s2{{fill:var(--series-2)}}
svg .dot.s3{{fill:var(--series-3)}}svg .dot.s4{{fill:var(--series-4)}}svg .ring{{fill:var(--surface-1);stroke:var(--series-3);stroke-width:2.5}}
svg .hit{{fill:transparent}}svg .row:hover .hit{{fill:var(--surface-2)}}
#tip{{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--grid);
 border-radius:6px;padding:6px 9px;font-size:12.5px;max-width:360px;box-shadow:0 2px 8px rgba(0,0,0,.12);display:none}}
#tip b{{display:block;margin-bottom:2px}}
details{{margin:8px 0 0}}summary{{color:var(--text-secondary);font-size:13px;cursor:pointer}}
table{{border-collapse:collapse;font-size:13px;margin:8px 0}}th,td{{padding:3px 10px;text-align:right;border-bottom:1px solid var(--grid)}}
th:first-child,td:first-child{{text-align:left;max-width:420px}}
</style></head><body><main class="viz-root">
{chr(10).join(body)}
<div id="tip"></div><script>
const tip=document.getElementById('tip');
document.querySelectorAll('g.row').forEach(g=>{{
 g.addEventListener('mousemove',e=>{{const [t,v]=g.dataset.tip.split('|');tip.innerHTML='<b></b><span></span>';
  tip.querySelector('b').textContent=t;tip.querySelector('span').textContent=v;tip.style.display='block';
  const x=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8);tip.style.left=x+'px';tip.style.top=(e.clientY+14)+'px';}});
 g.addEventListener('mouseleave',()=>{{tip.style.display='none';}});}});
</script></main></body></html>
"""
    dest = D / 'summary' / 'comparisons' / 'europe-ca-us.html'
    dest.write_text(page, encoding='utf-8')
    print(f'wrote {dest.relative_to(ROOT)} (' + ', '.join(f'{REGION_NAMES[c]} {counts[c]}' for c in REGIONS) + ')')


if __name__ == '__main__':
    main()
