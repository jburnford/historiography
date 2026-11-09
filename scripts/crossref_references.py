"""Open reference lists of history journal articles from Crossref (2026-11-08; user, on G. Wynn, 'Forests, Frontiers,
and Extractivism', Environmental History 2023, which cites Clifford's JHG 2022 article: "why are you not making the
link?"). The JSTOR full-text delivery ends around 2020 for most journals, so later articles never reached the graph.
Crossref holds the deposited reference lists of many publishers (Chicago, Cambridge, Taylor & Francis, Wiley, SAGE,
Springer ...; Crossref references are open metadata), each reference with a DOI where the publisher matched one,
otherwise structured fields or the citation string.

Journals: the catalogue's ISSNs (data/journal-catalogue/catalogue.csv), plus every journal in which OpenAlex places at
least --min-works works whose primary topic is History or History and Philosophy of Science
(data/journal-catalogue/openalex-history-venues-2026-11-08.jsonl.gz, from scripts/openalex_history_harvest.py), so the
citing side reaches journals outside history (Water History, Environmental Humanities: user, 2026-11-08, "we're using
me to identify trends"). The Crossref public data file would have given all of this at once, but its requester-pays
S3 bucket is out of reach from the account we have. Catalogue journals first, then the venues by history share, three
at a time. Records with references only, published from --since on. Raw pages go to E: (one jsonl.gz per journal; metadata only, no text); the matching and the citing work
keys are separate steps (scripts/key_crossref_articles.py, scripts/export_crossref_citations.py).

    python3 scripts/crossref_references.py count  --since 2000
    python3 scripts/crossref_references.py harvest --since 2000 [--min-works 10 --min-share 0.01] [--workers 3]
"""
import argparse, concurrent.futures as cf, csv, gzip, json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / 'data/journal-catalogue/catalogue.csv'
VENUES = ROOT / 'data/journal-catalogue/openalex-history-venues-2026-11-08.jsonl.gz'
OUT = Path('/mnt/e/crossref-refs-2026-11-08')
API = 'https://api.crossref.org/journals/{}/works'
UA = 'historiography-kg/0.1 (https://github.com/jburnford/historiography; mailto:jic823@usask.ca)'
SELECT = 'DOI,type,title,author,issued,container-title,ISSN,reference,references-count'


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120) as r:
                return json.load(r)
        except Exception as e:                       # 429 / 5xx / timeouts: back off
            if getattr(e, 'code', None) == 404:
                return None
            time.sleep(min(60, 3 * 2 ** i))
    raise RuntimeError(f'gave up on {url}')


def journals(min_works=None, min_share=0.01):
    """-> [(id, title, [issns])], one entry per journal: the catalogue, then (with min_works) the OpenAlex history
    venues whose ISSNs the catalogue lacks, ids 'journal_oa_S...'. Catalogue journals come first, then the venues by
    the share of their OpenAlex works that are history (general journals such as Nature or The Lancet hold thousands of
    history pieces but come last)."""
    venues = [json.loads(l) for l in gzip.open(VENUES, 'rt', encoding='utf-8')]
    out, seen = [], set()
    for r in csv.DictReader(open(CATALOGUE, encoding='utf-8')):
        issns = [x.strip() for x in r['issns'].split('|') if x.strip()]
        if issns:
            out.append((r['id'], r['title'], issns, 2.0))
            seen.update(issns)
    if min_works is not None:
        for v in venues:
            if v['history_works'] >= min_works and not seen & set(v['issn']):
                issns = ([v['issn_l']] if v['issn_l'] else []) + [i for i in v['issn'] if i != v['issn_l']]
                share = v['history_works'] / max(v.get('works_total') or v['history_works'], v['history_works'])
                if share < min_share:               # physics/chemistry journals OpenAlex tags with a few history works
                    continue
                out.append(('journal_oa_' + v['id'], v['name'], issns, share))
                seen.update(v['issn'])
    out.sort(key=lambda j: -j[3])
    return [j[:3] for j in out]


def query(issn, since, rows, cursor=None):
    f = f'from-pub-date:{since},has-references:true'
    q = dict(filter=f, rows=rows, select=SELECT)
    if cursor:
        q['cursor'] = cursor
    return get(API.format(issn) + '?' + urllib.parse.urlencode(q))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('phase', choices=('count', 'harvest'))
    ap.add_argument('--since', default='2000')
    ap.add_argument('--only', help='comma-separated ISSNs (pilot)')
    ap.add_argument('--min-works', type=int, help='add OpenAlex history venues with at least this many history works')
    ap.add_argument('--min-share', type=float, default=0.01, help='least share of a venue\'s works that are history')
    ap.add_argument('--workers', type=int, default=3)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    counts_file = OUT / f'counts-{args.since}.json'
    counts = json.loads(counts_file.read_text()) if counts_file.exists() else {}
    js = journals(args.min_works, args.min_share)
    if args.only:
        want = set(args.only.split(','))
        js = [j for j in js if want & set(j[2])]
    if args.phase == 'count':
        for jid, title, issns in js:
            if jid in counts:
                continue
            best = (0, None)
            for issn in issns:                       # print and online ISSN usually answer alike; keep the larger
                d = query(issn, args.since, 0)
                n = d['message']['total-results'] if d else 0
                best = max(best, (n, issn), key=lambda x: x[0])
            counts[jid] = dict(title=title, issn=best[1], with_refs=best[0])
            counts_file.write_text(json.dumps(counts, indent=0, ensure_ascii=False))
        tot = sum(v['with_refs'] for v in counts.values())
        top = sorted(counts.values(), key=lambda v: -v['with_refs'])[:40]
        print(len(counts), 'journals;', sum(1 for v in counts.values() if v['with_refs']), 'with references;', tot, 'records')
        for v in top:
            print(f"{v['with_refs']:7d}  {v['issn']}  {v['title']}")
        return
    def one(j):
        jid, title, issns = j
        dest = OUT / f'{jid}.jsonl.gz'
        if dest.exists():
            return None
        tmp = dest.with_suffix('.part')
        n = 0
        with gzip.open(tmp, 'wt', encoding='utf-8') as f:
            for issn in issns:                       # print and online ISSN usually answer alike: the first with records
                cursor = '*'
                while True:
                    d = query(issn, args.since, 500, cursor)
                    items = d['message']['items'] if d else []
                    for it in items:
                        it['_journal'] = jid
                        f.write(json.dumps(it, ensure_ascii=False) + '\n')
                    n += len(items)
                    cursor = d['message'].get('next-cursor') if d else None
                    if not items or not cursor:
                        break
                if n:
                    break
        os.replace(tmp, dest)                        # E: can drop out: write by rename; an empty file marks 'none'
        return n, title
    done = got = recs = 0
    t0 = time.time()
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for r in ex.map(one, js):
            done += 1
            if r:
                recs += r[0]; got += bool(r[0])
                if r[0]:
                    print(f'{done}/{len(js)}  {r[0]:6d}  {r[1]}  ({recs:,} records, {time.time() - t0:.0f}s)', flush=True)

if __name__ == '__main__':
    main()
