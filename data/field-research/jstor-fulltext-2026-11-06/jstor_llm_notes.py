"""Parse JSTOR note pieces with Qwen (vLLM) on Nibi: the hard half the rules miss (2026-11-06 pilot).

Input JSON lines, one per request: {id, iid, journal, year, first, pieces: [str, ...]} where `pieces` are up to 8
consecutive note pieces of one article in note order and `first` is the index of the first piece. The model returns
every citation in each piece (works, Ibid./short/author-date back-references, primary sources). Back-references are
resolved afterwards in Python (jstor_notes.py logic), across the whole article.

Writes answers.jsonl (id, iid, first, citations: [...], ok, raw on failure) and summary.json. Resumable.

Compact answers (2026-11-07, after pilot 26350911 spent about 115 output tokens per piece, mostly on null fields):
the model omits null and empty fields, gives no volume or pages, and gives a primary source as its type, piece and a
short title only. `parse` fills the omitted fields back with null, so the answer rows keep the pilot's shape. A year
must be printed in the citation itself (the pilot once took the year of the events from the article).

    python jstor_llm_notes.py --items pilot.jsonl --model $MODEL_DIR --out results/notes-pilot
"""
import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

SYSTEM = """You extract citations from the footnotes of history journal articles. The notes come from OCR and were split into numbered pieces by a machine: a piece may be a whole note, part of a note, or several citations; an author's name may sit at the end of the previous piece. Notes may be in any language and any era (1840s to today).

For every piece, list each work or source it cites, in order. For each citation give:
- "p": the piece number
- "type": "work" (a full or nearly full reference), "ibid" (Ibid., idem, ebd., ivi, id.), "short" (a shortened reference to a work cited earlier: surname + short title, op. cit., cit., art. cit., "n. 12 above"), "authordate" (Surname Year, as in "Hamilton 1972, 45"), or "primary" (archival documents, manuscripts, letters, newspapers or magazines cited by date, government records, laws, court cases, interviews, census tables, classical texts cited by book and line)
- "authors": the authors' names as ["Family, Given"] (editors of an edited volume go here when there is no author, with "editors": true); for "short" and "authordate" give the surname(s) printed
- "title": the title of the book, article, chapter or thesis as printed (for "short": the short title, or null); never a journal name
- "container": the journal, edited book or series the title appears in, else null
- "place", "publisher", "year" (publication year as an integer, printed in this citation; not a date range of the subject, never taken from the article's topic)
- "kind": "book", "article", "chapter", "thesis", "periodical", "web" or "other"
For a "primary" citation give only "p", "type" and a short "title".

Use only what is printed; fix obvious OCR hyphenation ("Dis- covery" -> "Discovery") but do not invent missing parts. Leave out every field that would be null or empty. Ignore commentary that cites nothing. A piece with no citation gets no entry.

Reply with compact JSON only, e.g. {"citations":[{"p":3,"type":"work","authors":["Hill, Christopher"],"title":"The World Turned Upside Down","place":"London","year":1972,"kind":"book"},{"p":4,"type":"ibid"}]}"""

FIELDS = ('p', 'type', 'authors', 'title', 'container', 'place', 'publisher', 'year', 'volume', 'pages', 'kind')


def prompt(r):
    lines = [f"Journal: {r['journal']} ({r['year']})", '']
    for k, p in enumerate(r['pieces']):
        lines.append(f"[{r['first'] + k}] {p}")
    return '\n'.join(lines)


def parse(text):
    m = re.search(r'\{.*\}', text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group())
    except json.JSONDecodeError:
        return None
    c = d.get('citations')
    if not isinstance(c, list):
        return None
    out = []
    for x in c:
        if isinstance(x, dict):
            y = {k: x.get(k) for k in FIELDS}
            y['authors'] = y['authors'] or []
            if x.get('editors'):
                y['editors'] = True
            if y['type'] == 'primary':
                y['kind'] = 'primary'
            out.append(y)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--items', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--max-model-len', type=int, default=8192)
    ap.add_argument('--max-num-seqs', type=int, default=64)
    ap.add_argument('--max-tokens', type=int, default=2500)
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
                row = dict(id=r['id'], iid=r['iid'], first=r['first'], n=len(r['pieces']), citations=c or [], ok=c is not None)
                if c is None:
                    row['raw'] = t[-300:]
                fh.write(json.dumps(row, ensure_ascii=False) + '\n')
                pieces += len(r['pieces'])
            fh.flush()
            el = time.time() - t0
            print(f'{len(done) + i + len(part)}/{len(recs)} requests, {pieces} pieces, {el:.0f} s, {pieces / el:.1f} pieces/s', flush=True)
    summary = dict(report, requests=len(recs), pieces=pieces, seconds=round(time.time() - t0))
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
