"""Render the field-as-practice summary as a self-contained HTML page (not a site asset).

Reads data/evidence-layer/generated/<version>/summary.json and writes field-practice.html
beside it: review volume by theme across H-Net and Reviews in History, coloured by whether
the atlas has an entry for the theme, plus the atlas fields with no practice signal.
Palette: categorical slots 1-2 of the dataviz reference palette, validated for both modes.
"""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = 30


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", default="v1")
    args = ap.parse_args()
    base = ROOT / "data/evidence-layer/generated" / args.version
    s = json.loads((base / "summary.json").read_text())
    themes = s["review_themes"][:TOP]
    maxv = max(t["reviews"] for t in themes)
    hn, rih = s["per_source"]["hnet"], s["per_source"]["rih"]
    general = hn["items_by_axis"].get("general", 0)
    row_h, label_w, bar_w, top_pad = 22, 300, 500, 8
    height = top_pad + row_h * len(themes) + 28
    bars, rows = [], []
    for i, t in enumerate(themes):
        none = t["target"].startswith("none:")
        label = t["label"].replace("No atlas entry: ", "").replace("_", " ")
        label = label[:1].upper() + label[1:]
        y = top_pad + i * row_h
        w = max(2, round(bar_w * t["reviews"] / maxv))
        cls = "s2" if none else "s1"
        kind = "No atlas entry" if none else "Atlas entry"
        tip = f"{label} — {t['reviews']:,} reviews ({t['reviews_since_2010']:,} since 2010) · {kind}"
        value = (f'<text class="val" x="{label_w + w + 6}" y="{y + 15}">{t["reviews"]:,}</text>' if i < 10 else "")
        bars.append(
            f'<g class="bar" tabindex="0" data-tip="{html.escape(tip)}">'
            f'<rect class="hit" x="0" y="{y}" width="{label_w + bar_w + 60}" height="{row_h}"/>'
            f'<text class="lab" x="{label_w - 8}" y="{y + 15}" text-anchor="end">{html.escape(label)}</text>'
            f'<path class="{cls}" d="M{label_w},{y + 4} h{w - 4} a4,4 0 0 1 4,4 v6 a4,4 0 0 1 -4,4 h-{w - 4} z"/>'
            f'{value}</g>')
        rows.append(f"<tr><td>{html.escape(label)}</td><td>{kind}</td><td>{t['reviews']:,}</td>"
                    f"<td>{t['reviews_since_2010']:,}</td></tr>")
    missing = "".join(f"<li>{html.escape(e.split(' (', 1)[1][:-1])}</li>"
                      for e in s["atlas_entries_without_practice_evidence"])
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Field as practice — review volume by theme</title>
<style>
.viz-root {{ color-scheme: light; --surface-1:#fcfcfb; --text-primary:#0b0b0b; --text-secondary:#52514e;
  --grid:#e4e3df; --series-1:#2a78d6; --series-2:#eb6834; }}
@media (prefers-color-scheme: dark) {{ :root:where(:not([data-theme="light"])) .viz-root {{ color-scheme: dark;
  --surface-1:#1a1a19; --text-primary:#ffffff; --text-secondary:#c3c2b7; --grid:#383835; --series-1:#3987e5; --series-2:#d95926; }} }}
body {{ margin:0; }}
.viz-root {{ background:var(--surface-1); color:var(--text-primary); font:14px/1.45 system-ui, sans-serif; padding:24px 28px; max-width:1360px; }}
h1 {{ font-size:20px; margin:0 0 4px; }} h2 {{ font-size:15px; margin:24px 0 6px; }}
.sub, .note, .lab, .val, figcaption {{ color:var(--text-secondary); fill:var(--text-secondary); }}
.sub {{ margin:0 0 14px; max-width:880px; }}
.wrap {{ display:flex; gap:32px; flex-wrap:wrap; align-items:flex-start; }}
.legend {{ display:flex; gap:18px; margin:6px 0 8px; font-size:13px; }}
.legend span::before {{ content:""; display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:6px; vertical-align:-1px; }}
.legend .k1::before {{ background:var(--series-1); }} .legend .k2::before {{ background:var(--series-2); }}
svg text {{ font-size:12.5px; }} .lab {{ fill:var(--text-primary); }}
.s1 {{ fill:var(--series-1); }} .s2 {{ fill:var(--series-2); }}
.hit {{ fill:transparent; }} .bar:hover .hit, .bar:focus .hit {{ fill:var(--grid); }} .bar:focus {{ outline:none; }}
#tip {{ position:fixed; pointer-events:none; background:var(--surface-1); color:var(--text-primary); border:1px solid var(--grid);
  border-radius:6px; padding:6px 9px; font-size:12.5px; box-shadow:0 2px 8px rgb(0 0 0 / .15); display:none; max-width:320px; }}
aside {{ max-width:330px; }} aside ul {{ columns:2; column-gap:18px; padding-left:16px; margin:6px 0; font-size:12.5px; }}
table {{ border-collapse:collapse; font-size:12.5px; }} td, th {{ padding:3px 10px 3px 0; text-align:left; border-bottom:1px solid var(--grid); }}
td:nth-child(n+3), th:nth-child(n+3) {{ text-align:right; }}
</style></head><body><div class="viz-root">
<h1>What the review record says historians work on — and what the atlas names</h1>
<p class="sub">Reviews per theme across H-Net ({hn['years'][0]}–{hn['years'][1]}) and Reviews in History
({rih['years'][0]}–{rih['years'][1]}), via the editorial crosswalk from networks and subject headings. A review counts
once per theme it maps to, so bars overlap and must not be summed. {general:,} of {hn['items']:,} H-Net reviews
(mostly H-Soz-u-Kult) come from general networks and appear under no theme. These corpora are not the profession;
counts measure participation, not influence.</p>
<div class="wrap"><figure style="margin:0">
<div class="legend"><span class="k1">Theme has an atlas entry</span><span class="k2">No atlas entry for this theme</span></div>
<svg width="{label_w + bar_w + 70}" height="{height}" role="img" aria-label="Horizontal bar chart of reviews per theme">
<line x1="{label_w}" x2="{label_w}" y1="0" y2="{height - 24}" stroke="var(--grid)"/>
{''.join(bars)}</svg>
<figcaption>Top {TOP} themes. Hover or focus a bar for exact counts; values labelled on the ten largest.</figcaption>
</figure>
<aside><h2>{len(s['atlas_entries_without_practice_evidence'])} of 77 atlas fields have no signal here</h2>
<p class="note">Networks, subject headings and journal directories classify by theme, region and period. Approaches
and schools never appear, so these atlas fields cannot be seen this way. Seeing their practice needs evidence from
what reviews say.</p><ul>{missing}</ul></aside></div>
<details><summary>Table view</summary><table><thead><tr><th>Theme</th><th>Atlas</th><th>Reviews</th><th>Since 2010</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></details>
<p class="note">Built {s['built']} from data/evidence-layer/practice-crosswalk.csv (proposed, unreviewed mappings).</p>
<div id="tip" role="tooltip"></div></div>
<script>
const tip = document.getElementById('tip');
function show(e, g) {{ tip.textContent = g.dataset.tip; tip.style.display = 'block';
  const r = g.getBoundingClientRect(); const x = e && e.clientX ? e.clientX : r.left + 280; const y = e && e.clientY ? e.clientY : r.top;
  tip.style.left = Math.min(x + 14, innerWidth - 340) + 'px'; tip.style.top = (y + 14) + 'px'; }}
document.querySelectorAll('.bar').forEach(g => {{
  g.addEventListener('mousemove', e => show(e, g)); g.addEventListener('focus', () => show(null, g));
  g.addEventListener('mouseleave', () => tip.style.display = 'none'); g.addEventListener('blur', () => tip.style.display = 'none'); }});
</script></body></html>"""
    (base / "field-practice.html").write_text(page)
    print(base / "field-practice.html")


if __name__ == "__main__":
    main()
