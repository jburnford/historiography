"""Cited works and their candidate graph works -> prompts for a local model (Qwen on Nibi), with a gold set (2026-11-04).

translation_check_groups.py gives, for each cited work no crosswalk matched, every keyed person holding one of its
cited authors and that person's works in the graph. Sol judged the works cited by 10+ theses with the web; the tail
(2-9 theses, ~57k items with candidates) is for a local model, which only decides whether the cited work IS one of
the candidates (the same work, a translation or an edition) or none of them; it finds no identifiers.

Long candidate lists are trimmed to --cap works: the ones whose titles share most character trigrams with the cited
title, books kept ahead of articles for a cited book (a translation shares few words with its original), never a
candidate the gold answer names (so the gold set is not made easier or harder by the trim).

--gold reads Sol's rounds (round dirs with groups.json + g*/verdicts.json): items Sol answered with a candidate
work (same/translation/edition) or `none` become the gold set the model is scored on before the tail is trusted.

    python3 scripts/qwen_match_inputs.py --groups data/identifiers/qwen-tail-2026-11-04/groups.json --out tail.jsonl
    python3 scripts/qwen_match_inputs.py --gold data/identifiers/translation-check-2026-11-03c data/identifiers/translation-check-2026-11-03d --out gold.jsonl
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path


def fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]+', ' ', s)


def grams(s):
    s = ' '.join(fold(s).split())
    return {s[i:i + 3] for i in range(len(s) - 2)}


def trim(item, cap, keep=()):
    cited = grams(item['cited_title'])
    flat = [dict(w, person=c['name']) for c in item['candidates'] for w in c['works']]
    if len(flat) <= cap:
        return flat

    def score(w):
        g = grams(w.get('title'))
        sim = len(cited & g) / (len(cited | g) or 1)
        return (w['work'] in keep, w.get('kind') == 'book', sim)
    return sorted(flat, key=score, reverse=True)[:cap]


def record(item, cap, gold=None):
    keep = {gold} if gold else ()
    works = trim(item, cap, keep)
    return dict(id=item['id'], cited_title=item['cited_title'], cited_year=item.get('cited_year'),
                cited_authors=item.get('cited_authors'), theses=item.get('cited_by_theses'),
                candidates=[dict(work=w['work'], title=(w.get('title') or '')[:300], year=w.get('year'), kind=w.get('kind'),
                                 person=w['person']) for w in works], **({'gold': gold or 'none'} if gold is not None else {}))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--groups', type=Path, nargs='*', default=[])
    ap.add_argument('--gold', type=Path, nargs='*', default=[], help="Sol round dirs: score set from Sol's answers")
    ap.add_argument('--cap', type=int, default=40)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    out = []
    for f in args.groups:
        out += [record(i, args.cap) for g in json.loads(f.read_text()) for i in g['items'] if any(c['works'] for c in i['candidates'])]
    for d in args.gold:
        items, verdicts = {}, {}
        for f in sorted(d.glob('*/groups.json')) + sorted(d.glob('groups.json')):
            for g in json.loads(f.read_text()):
                for i in g['items']:
                    items.setdefault(i['id'], i)
        for f in sorted(d.glob('*/g*/verdicts.json')) + sorted(d.glob('g*/verdicts.json')):
            for v in json.loads(f.read_text()):
                verdicts[v.get('id')] = v                      # later rounds win
        for vid, v in verdicts.items():
            it = items.get(vid)
            if not it or not any(c['works'] for c in it['candidates']):
                continue
            ok = {w['work'] for c in it['candidates'] for w in c['works']}
            rel = v.get('relation')
            if rel in ('same', 'translation', 'edition') and v.get('work') in ok:
                out.append(record(it, args.cap, v['work']))
            elif rel == 'none':
                out.append(record(it, args.cap, ''))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w') as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(json.dumps(dict(items=len(out), gold_match=sum(1 for r in out if r.get('gold') not in (None, 'none')),
                          gold_none=sum(1 for r in out if r.get('gold') == 'none'))))


if __name__ == '__main__':
    main()
