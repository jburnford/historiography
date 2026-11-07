"""Book reviews -> reviewed books (heading) and reviewer signature, with Qwen (vLLM) on Nibi (2026-11-06 pilot).

Input JSON lines, one per review: {id, journal, year, meta_title, creators, head, tail}. `head` is the text around
where the review's title first appears (a page can open with the end of the previous review); `tail` is the end of
the item's text (the last page can run on into the next review). The model returns the books under review and the
signature as printed. Writes answers.jsonl (id, result, ok, raw on failure) and summary.json. Resumable.

    python jstor_llm_reviews.py --items reviews-pilot.jsonl --model $MODEL_DIR --out results/reviews-pilot
"""

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

SYSTEM = """You read book reviews from history journals (OCR text, 1840s to today, any language) and record two things.

1. The book or books under review, from the review's heading (e.g. "Title. By Author. Place: Publisher, 1969. Pp. xiii, 306. $7.00." or "AUTHOR. Title. (Publisher. 1933. 15s.)" or "Author, Title, Paris, Fayard, 1986, 954 p."). A review may cover several books, each with its own heading. For each book give: "authors" (["Family, Given"]), "editors" (same form, when the book is edited), "translators", "title" (with subtitle), "series", "place", "publisher", "year" (integer), "pages" (as printed, e.g. "xiii, 306"), "price", "isbn" (as printed, may be a list).
2. The signature: the reviewer's name exactly as printed, the institution printed with it (or null), and "where": "end" (signed at the end), "start" (named at the start), "bio" (a contributor note such as "X teaches at Y"), or null if unsigned in this text.

The metadata title and names identify THIS review: the text can begin with the end of the previous review and end with the start of the next one; ignore those. The reviewer is usually one of the metadata names that is not an author of the reviewed book. Use only what is printed; use null for anything missing. Do not copy the review's text.

Reply with JSON only:
{"books": [{"authors": [], "editors": [], "translators": [], "title": "", "series": null, "place": null, "publisher": null, "year": null, "pages": null, "price": null, "isbn": null}], "reviewer": {"name": null, "institution": null, "where": null}}"""


def prompt(r):
    return (f"Journal: {r['journal']} ({r['year']})\nMetadata title: {r['meta_title']}\nMetadata names: {r['creators']}\n\n"
            f"BEGINNING OF TEXT:\n{r['head']}\n\nEND OF TEXT:\n{r['tail']}")


def parse(text):
    m = re.search(r'\{.*\}', text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group())
    except json.JSONDecodeError:
        return None
    return d if isinstance(d, dict) and isinstance(d.get('books'), list) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--items', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--max-model-len', type=int, default=8192)
    ap.add_argument('--max-num-seqs', type=int, default=64)
    ap.add_argument('--max-tokens', type=int, default=900)
    ap.add_argument('--chunk', type=int, default=200)
    args = ap.parse_args()
    from vllm import LLM, SamplingParams
    recs = [json.loads(l) for l in open(args.items)][:args.limit]
    llm = LLM(model=args.model, max_model_len=args.max_model_len, gpu_memory_utilization=0.90,
              max_num_seqs=args.max_num_seqs, limit_mm_per_prompt={'image': 0, 'video': 0}, enable_prefix_caching=False)
    params = SamplingParams(temperature=0.0, max_tokens=args.max_tokens)
    kw = {'chat_template_kwargs': {'enable_thinking': False}}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'answers.jsonl'
    done = {json.loads(l)['id'] for l in open(path)} if path.exists() else set()
    todo = [r for r in recs if r['id'] not in done]
    report = Counter()
    t0 = time.time(); pieces = 0
    with open(path, 'a') as fh:
        for i in range(0, len(todo), args.chunk):
            part = todo[i:i + args.chunk]
            msgs = [[{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt(r)}] for r in part]
            outs = llm.chat(msgs, params, use_tqdm=False, **kw)
            for r, o in zip(part, outs):
                t = o.outputs[0].text
                c = parse(t)
                report['ok' if c is not None else 'failed'] += 1
                report['out_tokens'] += len(o.outputs[0].token_ids)
                row = dict(id=r['id'], result=c, ok=c is not None)
                if c is None:
                    row['raw'] = t[-300:]
                fh.write(json.dumps(row, ensure_ascii=False) + '\n')
                pieces += 1
            fh.flush()
            el = time.time() - t0
            print(f'{len(done) + i + len(part)}/{len(recs)} requests, {el:.0f} s, {pieces / el:.1f} reviews/s', flush=True)
    summary = dict(report, requests=len(recs), seconds=round(time.time() - t0))
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
