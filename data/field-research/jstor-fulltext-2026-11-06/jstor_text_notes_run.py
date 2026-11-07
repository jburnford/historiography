"""Notes cut from page text (jstor_text_notes.notes) for items JSTOR delivered without a note list, then the rule
parser (jstor_notes.citations); 2026-11-06.

Scope (user, 2026-11-06: "if there is citations we can use them"): every non-review item without a JSTOR list whose
text carries notes by rule B of jstor_ft_coverage.noted(): research articles, review essays and articles, misc items.

Writes to /mnt/e/jstor-fulltext-2026-11-06/ (temporary name, then rename):
  textnotes-pieces.jsonl.gz   {iid, pieces: [...]}  (note text: E: only, never committed; input for a later LLM pass)
  textnotes-rules.jsonl.gz    citation rows like rules/part-*.jsonl.gz, plus source='text'
"""
import gzip, json, os, signal, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jstor_notes as J  # noqa: E402
import jstor_text_notes as T  # noqa: E402
from jstor_ft_coverage import noted  # noqa: E402

E = '/mnt/e/jstor-fulltext-2026-11-06'
KEYS = ('note', 'cit', 'rule', 'kind', 'conf', 'ref', 'authors', 'surnames', 'title', 'container', 'place', 'publisher',
        'year', 'volume', 'pages', 'editors')


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def main():
    want = set()
    with open(f'{E}/signals.tsv', encoding='utf-8') as f:
        next(f)
        for line in f:
            iid, g, pages, chars, refs, imp, ibid, pg = line.rstrip('\n').split('\t')
            if g != 'book_review' and refs == '0' and noted(max(int(pages), 1), int(imp), int(ibid), int(pg)):
                want.add(iid)
    print('items in scope', len(want), flush=True)
    signal.signal(signal.SIGALRM, _alarm)
    tp, tr = f'{E}/textnotes-pieces.jsonl.gz.tmp', f'{E}/textnotes-rules.jsonl.gz.tmp'
    stats = dict(items=0, with_notes=0, pieces=0, rows=0, timeouts=0); t0 = time.time()
    with gzip.open(f'{E}/noref_items.jsonl.gz', 'rt', encoding='utf-8') as f, \
            gzip.open(tp, 'wt', encoding='utf-8') as op, gzip.open(tr, 'wt', encoding='utf-8') as orow:
        for line in f:
            iid = line[9:45]
            if iid not in want:
                continue
            r = json.loads(line); stats['items'] += 1
            signal.alarm(30)
            try:
                pieces = T.notes(r['full_text'])
                rows = J.citations(pieces) if pieces else []
            except Timeout:
                stats['timeouts'] += 1
                continue
            except Exception as e:
                orow.write(json.dumps({'iid': iid, 'rule': 'error', 'error': repr(e)[:200], 'source': 'text'}) + '\n')
                continue
            finally:
                signal.alarm(0)
            if not pieces:
                continue
            stats['with_notes'] += 1; stats['pieces'] += len(pieces)
            op.write(json.dumps({'iid': iid, 'pieces': pieces}, ensure_ascii=False) + '\n')
            for row in rows:
                out = {'iid': iid, 'source': 'text'}
                out.update({k: row[k] for k in KEYS if row.get(k) not in (None, [], '')})
                orow.write(json.dumps(out, ensure_ascii=False) + '\n'); stats['rows'] += 1
    os.replace(tp, tp[:-4]); os.replace(tr, tr[:-4])
    print('done', stats, round(time.time() - t0), 's', flush=True)


if __name__ == '__main__':
    main()
