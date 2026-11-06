"""Deliverable 1: coverage of the JSTOR full-text delivery by journal x decade x genre.

One streaming pass over the delivery (never loaded whole). For every item that is not a book review it
scores note-like patterns in the OCR text (pages are flat strings: no line breaks, so footnotes run into
the page end and can only be found by citation patterns). It also writes two shards to E: so later
passes need not reread 3.5 GB:
  reviews.jsonl.gz          book reviews (iid, full_text)
  noref_items.jsonl.gz      research articles, review essays, review articles and misc items with no JSTOR note list
Outputs on E: (not committed): signals.tsv, the two shards.
Committed: coverage.tsv (counts only) via --aggregate.

Usage:  python3 jstor_ft_coverage.py stream      # one pass, ~8 min
        python3 jstor_ft_coverage.py aggregate   # writes coverage.tsv + coverage-summary.json beside this script
"""
import gzip, json, os, re, sqlite3, sys, time
from collections import defaultdict

SRC = '/mnt/e/7d08e73a-0591-4390-a0d3-dc940b06cdb6.jsonl.gz'
OUT = '/mnt/e/jstor-fulltext-2026-11-06'
HERE = os.path.dirname(os.path.abspath(__file__))
DB = 'file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro'

# Note-like patterns. Counted per item; none is decisive alone.
PATS = {
    # (Place: Publisher, 1954) / (Cambridge, 1981) / (Paris, 1890), also 1954) with page refs
    'imprint': re.compile(r'\(\s*[A-ZÀ-Ý][^()]{1,90}?,\s*(?:1[5-9]|20)\d\d\s*\)'),
    'ibid': re.compile(r'\b(?:[Ii]bid|[Ii]bidem|[Ii]d\.|op\.\s?cit|loc\.\s?cit|a\.\s?a\.\s?O|cit\.,)'),
    'pages': re.compile(r'\b(?:pp?|S|Bd|vol|t)\.\s?[IVXLCivxlc\d]+'),
}


def meta():
    c = sqlite3.connect(DB, uri=True)
    m = {}
    for iid, j, y, g in c.execute('select item_id, journal_title, year, genre from records where included'):
        m[iid.split(':')[-1]] = (j, y, g)
    return m


def short_genre(g):
    return {'research_article_as_deposited': 'article', 'book_review_as_deposited': 'book_review',
            'review_essay_as_deposited': 'review_essay', 'review_article_as_deposited': 'review_article'}.get(g, 'other')


def stream():
    m = meta()
    tmp = {k: f'{OUT}/{k}.part' for k in ('signals.tsv', 'reviews.jsonl.gz', 'noref_items.jsonl.gz')}
    sig = open(tmp['signals.tsv'], 'w', encoding='utf-8')
    sig.write('iid\tgenre\tpages\tchars\trefs\timprint\tibid\tpages_refs\n')
    rev = gzip.open(tmp['reviews.jsonl.gz'], 'wt', encoding='utf-8', compresslevel=5)
    nor = gzip.open(tmp['noref_items.jsonl.gz'], 'wt', encoding='utf-8', compresslevel=5)
    n = 0; t0 = time.time()
    with gzip.open(SRC, 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line); n += 1
            iid = r['iid']; ft = r.get('full_text') or []; refs = r.get('references') or []
            g = short_genre(m[iid][2])
            chars = sum(len(p) for p in ft)
            if g == 'book_review':
                rev.write(json.dumps({'iid': iid, 'full_text': ft}, ensure_ascii=False) + '\n')
                sig.write(f'{iid}\t{g}\t{len(ft)}\t{chars}\t{len(refs)}\t\t\t\n')
            else:
                text = ' '.join(ft)
                c = [len(p.findall(text)) for p in PATS.values()]
                sig.write(f'{iid}\t{g}\t{len(ft)}\t{chars}\t{len(refs)}\t{c[0]}\t{c[1]}\t{c[2]}\n')
                if not refs:
                    nor.write(json.dumps({'iid': iid, 'full_text': ft}, ensure_ascii=False) + '\n')
            if n % 25000 == 0:
                print(n, round(time.time() - t0), flush=True)
    sig.close(); rev.close(); nor.close()
    for k, p in tmp.items():
        os.replace(p, f'{OUT}/{k}')
    print('done', n, round(time.time() - t0), flush=True)


BIBLIO_TITLE = re.compile(r'bibliograph|books received|recent (?:publications|books|literature|articles)|publications re[cç]ues|'
                          r'livres re[cç]us|neuerscheinungen|zeitschriftenschau|periodical literature|theses|dissertations|'
                          r'list of (?:books|articles)|bulletin bibliographique|bollettino bibliografico|notes and news', re.I)


def noted(pages, imp, ibid, pg):
    """Rule B (2026-11-06): imprints + ibid/op. cit. + a third of the page references, >= 5 per 10 pages.
    Calibrated on research articles that do have >= 10 JSTOR notes (their text carries the same notes):
    recall 70% before 1950, 84% 1950-99, 81% from 2000 (rule A, without page references: 47/69/70%)."""
    return imp + ibid + pg / 3 >= 5 * max(pages, 10) / 10


def aggregate():
    """Counts per journal x decade. An item without a JSTOR note list is 'text_notes' when noted() fires."""
    m = meta()
    c = sqlite3.connect(DB, uri=True)
    titles = {i.split(':')[-1]: t or '' for i, t in c.execute('select item_id, title from records where included')}
    agg = defaultdict(lambda: defaultdict(int))
    with open(f'{OUT}/signals.tsv', encoding='utf-8') as f:
        next(f)
        for line in f:
            iid, g, pages, chars, refs, imp, ibid, pg = line.rstrip('\n').split('\t')
            j, y, _ = m[iid]
            dec = (y // 10 * 10) if y else 0
            a = agg[(j, dec)]
            if g == 'book_review':
                a['book_reviews'] += 1
                continue
            refs = int(refs); pages = max(int(pages), 1)
            is_noted = noted(pages, int(imp), int(ibid), int(pg))
            key = {'article': 'art', 'review_essay': 'ess', 'review_article': 'ess', 'other': 'oth'}[g]
            a[f'{key}_items'] += 1
            if refs:
                a[f'{key}_jstor_notes'] += 1
                a[f'{key}_note_pieces'] += refs
            elif is_noted:
                a[f'{key}_text_notes'] += 1
            else:
                a[f'{key}_no_notes'] += 1
            if not refs and BIBLIO_TITLE.search(titles.get(iid, '')):
                a['bibliography_lists'] += 1
    cols = ['art_items', 'art_jstor_notes', 'art_text_notes', 'art_no_notes', 'art_note_pieces',
            'ess_items', 'ess_jstor_notes', 'ess_text_notes', 'ess_no_notes', 'ess_note_pieces',
            'oth_items', 'oth_jstor_notes', 'oth_text_notes', 'oth_no_notes', 'bibliography_lists', 'book_reviews']
    rows = sorted(agg.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    tmp = f'{HERE}/coverage.tsv.part'
    with open(tmp, 'w', encoding='utf-8') as o:
        o.write('journal\tdecade\t' + '\t'.join(cols) + '\n')
        for (j, d), a in rows:
            o.write(f'{j}\t{d}\t' + '\t'.join(str(a.get(c, 0)) for c in cols) + '\n')
    os.replace(tmp, f'{HERE}/coverage.tsv')
    tot = defaultdict(int)
    for _, a in rows:
        for c in cols:
            tot[c] += a.get(c, 0)
    print(json.dumps(tot, indent=1))


if __name__ == '__main__':
    {'stream': stream, 'aggregate': aggregate}[sys.argv[1]]()
