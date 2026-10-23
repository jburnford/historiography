#!/usr/bin/env python3
"""Render the Europe / Canada / United States citation comparison page.

User (2026-10-22): "could you create a webpage with this comparison visualized". Reads the
region tables written by ``region_top_citations.py`` (``summary/regions/top-people.csv``,
``top-works.csv``) and the strict thesis counts in ``dissertations.csv``, and writes one
self-contained page (inline SVG, no external assets) to
``summary/comparisons/europe-ca-us.html``. Re-run after ``region_top_citations.py``:

    python3 scripts/region_top_citations.py --out <D>
    python3 scripts/render_region_comparison.py

Shares are per region: the percentage of the region's strict History PhDs that cite the person
or work (presence, one count per thesis). Colours follow the Canada-US page (Canada blue, United
States orange) with Europe in aqua; Europe without France is a hollow aqua ring.
"""
import csv
from collections import Counter
from datetime import date
import html
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from region_top_citations import regions_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
REG = D / 'summary' / 'regions'
esc = lambda s: html.escape(str(s if s is not None else ''), quote=True)  # noqa: E731
SERIES = [('CA', 'Canada', 's1', 'dot'), ('US', 'United States', 's2', 'dot'), ('EUROPE', 'Europe', 's3', 'dot'),
          ('EUROPE_EX_FR', 'Europe without France', 's3', 'ring')]


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
          '<span class="l3">Europe</span><span class="l4">Europe without France</span></div>')


def main():
    counts = Counter()
    for r in csv.DictReader((D / 'dissertations.csv').open(newline='', encoding='utf-8')):
        if r['in_analysis'] == 'True':
            for g in regions_of(r['country']):
                counts[g] += 1
            if r['country'] == 'FR':
                counts['FR'] += 1
    wanted = {r['id'] for r in csv.DictReader((REG / 'top-works.csv').open(newline='', encoding='utf-8'))}
    csv.field_size_limit(10 ** 8)
    for r in csv.DictReader((D / 'works.csv').open(newline='', encoding='utf-8')):
        if r['work_id'] in wanted and r['authors']:
            AUTHORS[r['work_id']] = proper(r['authors'].split(';')[0].split(',')[0].strip())
    people, works = load('top-people.csv'), load('top-works.csv')
    pool = unique(works)
    na = lambda r: max(r['share_CA'], r['share_US'])  # noqa: E731
    eu_fav = sorted((r for r in pool if r['share_EUROPE'] - na(r) > 0), key=lambda r: na(r) - r['share_EUROPE'])[:15]
    na_fav = sorted((r for r in pool if na(r) - r['share_EUROPE'] > 0), key=lambda r: r['share_EUROPE'] - na(r))[:15]
    exfr = top(works, 'EUROPE_EX_FR', 15)
    lead = top(works, 'EUROPE', 1)[0]
    shared = sorted((r for r in pool if min(r['share_EUROPE'], r['share_CA'], r['share_US']) >= 1.0),
                    key=lambda r: -min(r['share_EUROPE'], r['share_CA'], r['share_US']))[:12]
    tiles = ''.join(f'<div class="tile"><div class="v">{v:,}</div><div class="k">{esc(k)}</div></div>' for k, v in (
        ('History PhDs in Europe', counts['EUROPE']), ('of them in France', counts['FR']),
        ('History PhDs in Canada', counts['CA']), ('History PhDs in the United States', counts['US'])))
    body = [
        '<h1>Who History PhDs cite: Europe, Canada and the United States</h1>',
        '<p class="lede">The share of each region\'s History PhDs whose bibliography cites a person or work, from the '
        'dissertation citation graph. One count per thesis: a thesis that cites a work twenty times counts once. '
        'Translations and editions of a work mapped through Wikidata count as one work.</p>',
        f'<div class="tiles">{tiles}</div>',
        '<p class="note">France is about half of the European PhDs, so each chart also shows Europe without France '
        '(hollow ring). Hover over a row for the four values; every chart has a table below it.</p>',
        section('The most cited people in Europe', 'people',
                'Ranked by the share of European History PhDs citing any work by the person (first author). Foucault is '
                'the one figure cited about equally everywhere; the French historians of the Annales and of the '
                "historian's craft are cited far more in Europe than in North America.", top(people, 'EUROPE', 25),
                'most cited people in Europe'),
        section('The most cited works in Europe', 'works',
                f'European citation is more dispersed than North American: the most cited work in Europe, '
                f'<i>{esc(lead["label"].split(" (")[0])}</i>, is cited by {lead["share_EUROPE"]:.1f}% of European History PhDs, '
                f'against {lead["share_CA"]:.1f}% in Canada and {lead["share_US"]:.1f}% in the United States.',
                top(works, 'EUROPE', 20), 'most cited works in Europe'),
        section('Cited in Europe, rare in North America', 'eu-fav',
                'Works whose European share most exceeds the higher of the Canadian and US shares: mostly French '
                'reflection on history, memory and the historian\'s craft, with Swedish work on the uses of history.',
                eu_fav, 'works cited more in Europe'),
        section('Cited in North America, rare in Europe', 'na-fav',
                'Works whose Canadian or US share most exceeds the European share. Each country\'s own staples (Canadian '
                'liberal order and imperialism, US urban, Sunbelt and immigration history) and the North American '
                'theory canon barely travel to Europe.', na_fav, 'works cited more in North America'),
        section('Europe without France', 'exfr',
                'The most cited works in the other European countries (Sweden, Germany, Italy, Spain, Belgium and '
                'others): the shared theory canon, Koselleck and Weber, and a Swedish canon on the uses of history.',
                exfr, 'most cited works in Europe without France'),
        section('Common ground', 'shared',
                'Works cited by at least 1% of the History PhDs in each of Europe, Canada and the United States, ranked '
                'by the lowest of the three shares.', shared, 'works cited in all three regions'),
        '<h2 id="notes">How to read this</h2><ul class="note">'
        '<li><b>Sources.</b> Strict History PhDs (explicit History programme or department) with a parsed bibliography '
        'or a bibliography rebuilt from their notes. European theses come mostly from the BASE harvest, where non-English '
        'bibliographies parse less cleanly than Canadian and US ones, so European shares are, if anything, low.</li>'
        '<li><b>Works.</b> A work is first-author surname plus main title. Translations are merged only where Wikidata maps '
        'them to one work: some remain split (Weber\'s French <i>Économie et société</i>, Foucault\'s French <i>Histoire de '
        'la sexualité</i>), which lowers those works\' European shares.</li>'
        '<li><b>People.</b> First authors only; a person\'s share counts theses citing any of their works.</li>'
        '<li><b>Citation is not engagement.</b> A citation can be a frame, a foil or a ritual reference.</li></ul>',
        f'<p class="note">Built {date.today().isoformat()} from <code>summary/regions/</code> '
        '(<code>scripts/region_top_citations.py</code>, <code>scripts/render_region_comparison.py</code>). '
        'See also <a href="network.html">the map of the most cited works</a> and <a href="ca-us.html">Canada and the United States</a>.</p>',
    ]
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Who History PhDs cite: Europe, Canada and the United States</title>
<style>
.viz-root{{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ed;--text-primary:#0b0b0b;--text-secondary:#52514e;
 --text-muted:#76756f;--grid:#e3e2dd;--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--link:#b8b7b0}}
@media (prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])) .viz-root{{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#242422;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;
 --series-2:#d95926;--series-3:#199e70;--link:#5b5a54}}}}
:root[data-theme="dark"] .viz-root{{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--text-muted:#9c9b92;--grid:#34342f;--series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;--link:#5b5a54}}
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
.legend .l3::before{{background:var(--series-3)}}.legend .l4::before{{border:2px solid var(--series-3)}}
svg.dots{{width:100%;min-width:680px;height:auto;display:block}}.scroll{{overflow-x:auto}}
svg .grid{{stroke:var(--grid);stroke-width:1}}svg .tick{{fill:var(--text-muted);font-size:11px}}
svg .lab{{fill:var(--text-primary);font-size:12.5px}}svg .link{{stroke:var(--link);stroke-width:2}}
svg .dot{{stroke:var(--surface-1);stroke-width:2}}svg .s1{{fill:var(--series-1)}}svg .s2{{fill:var(--series-2)}}
svg .dot.s3{{fill:var(--series-3)}}svg .ring{{fill:var(--surface-1);stroke:var(--series-3);stroke-width:2.5}}
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
    print(f'wrote {dest.relative_to(ROOT)} (Europe {counts["EUROPE"]}, France {counts["FR"]}, Canada {counts["CA"]}, US {counts["US"]})')


if __name__ == '__main__':
    main()
