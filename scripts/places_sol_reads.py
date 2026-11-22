"""Place layer: title reads by the outside reviewer (Sol, 2026-11-19, job 9-place-titles) -> a tracked tag table.

Sol read every title holding an ambiguous Canadian or Sri Lankan place name that no adopted rule or LC heading had
tagged (26,719 work-name cases; data/identifiers/sol-review-2026-11-19/9-place-titles/). This turns the reads into
per-work place tags, read by scripts/places_build.py as source `title-read-sol`. It is not a rule: only the works read
are tagged, each by its own reading.

Kept (audit 2026-11-21, data/graph/places/audit/sol-title-reads-audit-2026-11-21.csv):
- `about-place`, confidence high: the work is tagged to the queued place (audit: 59/60 about-place rows right, the
  one miss a medium-confidence row; 56/56 high-confidence rows right). Confidence `title-read-sol`.
- `other-place-same-name`, confidence high, when the reason names exactly one other place from TARGETS and that
  place's LC heading is held by exactly one row of places.csv.gz (London, England -> London (England), Q84). Audit:
  40/40 right. Confidence `title-read-sol:other-place`.
British North America (Q248452) is the one place added (NEW_PLACES). Held, and counted in the report: medium/low
confidence rows, `unclear`, other-place rows with no single named target, and rows whose place QID is not in
places.csv.gz (St. John's, N.L. Q2082: its LC authority has no Wikidata QID and the
place has no cached Wikidata facts). The latest line per case wins (Sol appends superseding lines).

    python3 scripts/places_sol_reads.py          # writes data/graph/places/title-readings/sol-2026-11-19/
"""
import csv
import gzip
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data/identifiers/sol-review-2026-11-19/9-place-titles/verdicts.jsonl'
PLACES = ROOT / 'data/graph/places/places.csv.gz'
OUT = ROOT / 'data/graph/places/title-readings/sol-2026-11-19'
PROVENANCE = 'Sol (Codex) title read 2026-11-19, job 9-place-titles; audited 2026-11-21'

# queued name -> [(phrase in Sol's reason, LC heading of the place it names)]
TARGETS = {
    'London': [(r"\bLondon, England\b", 'London (England)'), (r"\bNew London, Connecticut\b", 'New London (Conn.)')],
    'Sydney': [(r"(?<!North )(?<!Greater )\bSydney, (Australia|New South Wales)\b", 'Sydney (N.S.W.)')],
    'Victoria': [(r"\bVictoria, Australia\b", 'Victoria'), (r"\bLake Victoria\b", 'Victoria, Lake')],
    'Vancouver': [(r"\bVancouver Island\b", 'Vancouver Island (B.C.)')],
    'Kingston': [(r"\bKingston, Jamaica\b", 'Kingston (Jamaica)'), (r"\bKingston, New York\b", 'Kingston (N.Y.)')],
    'Halifax': [(r"\bHalifax, (West )?Yorkshire\b", 'Halifax (England)')],
    'Hamilton': [(r"\bHamilton, New Zealand\b", 'Hamilton (N.Z.)'), (r"\bHamilton, Scotland\b", 'Hamilton (Scotland)'),
                 (r"\bHamilton, Ohio\b", 'Hamilton (Ohio)')],
    'Windsor': [(r"(?<!Old )\bWindsor, England\b", 'Windsor (Windsor and Maidenhead, England)'),
                (r"\bWindsor, Nova Scotia\b", 'Windsor (N.S.)')],
}
# places not yet in places.csv.gz that the reads may add, because places_build.py holds their Wikidata facts
# (build/places/wd-extra2): British North America was dropped as a period node of Canada (it also names the colonies
# that became the US); a work Sol read as about the British North American colonies is tagged to the place itself,
# and Canada's period links stay as they are.
NEW_PLACES = {'Q248452': 'British North America'}
FIELDS = ['work', 'qid', 'name', 'verdict', 'sol_confidence', 'title', 'year', 'kind', 'reason', 'provenance']


def latest(path=SRC):
    rows = {}
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            d = json.loads(line)
            rows[(d['work'], d['name'])] = d
    return rows


def target_of(d, by_heading):
    """The one other place Sol's reason names, as a QID held by places.csv.gz, else None."""
    text = d.get('reason', '') + ' ' + d.get('why', '')
    hits = {h for rx, h in TARGETS.get(d['name'], []) if re.search(rx, text)}
    if len(hits) != 1:
        return None
    q = by_heading.get(hits.pop(), [])
    return q[0] if len(q) == 1 else None


def build(rows, places):
    """rows: latest verdict per case; places: qid -> places.csv.gz row. Returns (tag rows, held counts)."""
    by_heading = {}
    for q, p in places.items():
        by_heading.setdefault(p['lc_heading'], []).append(q)
    out, held = [], Counter()
    for (work, name), d in sorted(rows.items()):
        v = d['verdict']
        if v not in ('about-place', 'other-place-same-name'):
            continue
        if d['confidence'] != 'high':
            held[f'{v}: not high confidence'] += 1
            continue
        if v == 'about-place':
            q = d['place_qid']
            if q not in places and q not in NEW_PLACES:
                held[f'about-place: {name} {q} not in places.csv.gz'] += 1
                continue
        else:
            q = target_of(d, by_heading)
            if not q:
                held['other-place-same-name: no single named target held in places.csv.gz'] += 1
                continue
        out.append(dict(work=work, qid=q, name=name, verdict=v, sol_confidence=d['confidence'],
                        title=(d.get('title') or '')[:300], year=d.get('year') or '', kind=d.get('kind') or '',
                        reason=(d.get('reason') or '')[:300], provenance=PROVENANCE))
    return out, held


def main():
    with gzip.open(PLACES, 'rt', encoding='utf-8') as fh:
        places = {r['qid']: r for r in csv.DictReader(fh)}
    rows = latest()
    out, held = build(rows, places)
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / 'title-reads.csv.gz', 'wt', newline='', encoding='utf-8', compresslevel=9) as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    label = {q: p['label'] + (f" ({p['lc_heading']})" if p['lc_heading'] else '') for q, p in places.items()}
    label.update({q: n + ' (new place)' for q, n in NEW_PLACES.items()})
    rep = dict(cases=len(rows), verdicts=dict(Counter(d['verdict'] for d in rows.values()).most_common()),
               tags=len(out), tags_by_verdict=dict(Counter(r['verdict'] for r in out).most_common()),
               tags_by_place={label[q]: n for q, n in Counter(r['qid'] for r in out).most_common()},
               held=dict(held.most_common()))
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
