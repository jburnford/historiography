"""Is a cited work one of its candidate graph works? Qwen (vLLM) judges each item; scored on a gold set (2026-11-04).

Input: JSON lines from qwen_match_inputs.py (cited title, year and authors; numbered candidate works by keyed
people holding the cited authors). The model answers with the number of the candidate that IS the cited work (the
same work, a translation of it, or another edition of it) or none, and how sure it is. It finds no identifiers;
apply_work_verdicts.py accepts a candidate answer only for a work among the item's candidates.

Writes answers.jsonl (id, work, relation, confidence, raw) and, when the input carries `gold`, score.json:
precision of chosen works against Sol's answers, overall and by confidence.

    python work_match_judge.py --items gold.jsonl --model $MODEL_DIR --out results/work-match-gold
"""
import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

SYSTEM = """You match bibliography entries from history dissertations to works in a scholarly catalogue.

You get one cited work (title, year, authors, as a dissertation's bibliography gives it) and a numbered list of candidate works by people who share a name with its author. Decide whether the cited work IS one of the candidates:
- "same": the same work; titles may differ by a subtitle, abbreviation, capitalisation, typo or punctuation.
- "translation": the cited title is a translation of the candidate (or the candidate translates it): same author, same book in another language. The years may differ by decades.
- "edition": another edition, reprint or revised edition of the same work.
- "none": none of them. Answer none when the cited work is a different work by the same author, a chapter, essay or introduction inside one of the candidate books, a review of a candidate, a candidate that is only on a similar topic, or when you cannot tell. A volume of selected or collected writings is not the single work it contains; a dissertation and the book later made from it are different works.

When several candidates are versions of the cited work (an original and its translations or editions), choose the original: the earliest version, in the language the author wrote it in. A Portuguese translation of a French book matches the French original, not its English translation.

A wrong match is worse than a missed one. Reply with JSON only:
{"match": <candidate number or null>, "relation": "same|translation|edition|none", "confidence": "high|medium|low"}"""


def prompt(r):
    lines = [f"Cited: {r['cited_title']}", f"Year: {r.get('cited_year') or '?'}", f"Authors: {r.get('cited_authors') or '?'}", '',
             'Candidates:']
    for n, c in enumerate(r['candidates'], 1):
        lines.append(f"{n}. {c['title']} ({c.get('year') or '?'}; {c.get('kind') or 'work'}; {c['person']})")
    return '\n'.join(lines)


def parse(text, r):
    m = re.search(r'\{.*?\}', text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group())
    except json.JSONDecodeError:
        return None
    rel = d.get('relation') if d.get('relation') in ('same', 'translation', 'edition', 'none') else 'none'
    n = d.get('match')
    work = None
    if rel != 'none' and isinstance(n, int) and 1 <= n <= len(r['candidates']):
        work = r['candidates'][n - 1]['work']
    return dict(work=work, relation=rel if work else 'none', confidence=d.get('confidence') or 'low')


def score(rows):
    s = {}
    for conf in ('all', 'high', 'medium', 'low'):
        sub = [r for r in rows if conf == 'all' or r['confidence'] == conf]
        chose = [r for r in sub if r['work']]
        right = sum(1 for r in chose if r['work'] == r['gold'])
        gold_match = sum(1 for r in sub if r['gold'] != 'none')
        found = sum(1 for r in sub if r['gold'] != 'none' and r['work'] == r['gold'])
        s[conf] = dict(items=len(sub), chose=len(chose), right=right,
                       precision=round(right / len(chose), 3) if chose else None,
                       recall=round(found / gold_match, 3) if gold_match else None,
                       wrong_when_gold_none=sum(1 for r in chose if r['gold'] == 'none'))
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--items', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--max-model-len', type=int, default=6144)
    ap.add_argument('--max-num-seqs', type=int, default=64)
    ap.add_argument('--chunk', type=int, default=500)
    ap.add_argument('--prefix-caching', action='store_true', help='off by default: tail jobs 26154056/7 hung with it on')
    args = ap.parse_args()
    from vllm import LLM, SamplingParams
    recs = [json.loads(l) for l in open(args.items)][:args.limit]
    # Qwen3.8 is a hybrid model: each running sequence holds a state-cache block (see stage2_judge.py).
    llm = LLM(model=args.model, max_model_len=args.max_model_len, gpu_memory_utilization=0.90,
              max_num_seqs=args.max_num_seqs, limit_mm_per_prompt={'image': 0, 'video': 0},
              enable_prefix_caching=args.prefix_caching)
    params = SamplingParams(temperature=0.0, max_tokens=60)
    kw = {'chat_template_kwargs': {'enable_thinking': False}}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    # Chunks, appended as they finish, and a rerun skips answered items: job 26148882 (256 concurrent sequences)
    # stalled at 52% with the GPU busy and no request finishing for 44 minutes.
    path = out / 'answers.jsonl'
    rows = [json.loads(l) for l in open(path)] if path.exists() else []
    done = {r['id'] for r in rows}
    todo = [r for r in recs if r['id'] not in done]
    report = Counter()
    with open(path, 'a') as fh:
        for i in range(0, len(todo), args.chunk):
            part = todo[i:i + args.chunk]
            msgs = [[{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt(r)}] for r in part]
            texts = [o.outputs[0].text for o in llm.chat(msgs, params, use_tqdm=False, **kw)]
            for r, t in zip(part, texts):
                a = parse(t, r)
                report['parsed' if a else 'unparsed'] += 1
                a = a or dict(work=None, relation='none', confidence='low')
                row = dict(id=r['id'], **a, raw=t.strip()[:200])
                if 'gold' in r:
                    row['gold'] = r['gold']
                rows.append(row)
                fh.write(json.dumps(row, ensure_ascii=False) + '\n')
            fh.flush()
            print(f'{len(done) + i + len(part)}/{len(recs)} after {round(time.time() - t0)} s', flush=True)
    for row in rows:
        report[f"relation:{row['relation']}"] += 1
        report[f"confidence:{row['confidence']}"] += 1
    summary = dict(report, items=len(recs), seconds=round(time.time() - t0))
    if rows and 'gold' in rows[0]:
        summary['score'] = score(rows)
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
