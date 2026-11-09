"""Open history dissertations OpenAlex knows and we hold no PDF for -> browser download pages (2026-11-08; user: "we
were using OpenAlex for dissertations? ie identifying missing dissertations I could download").

Input: the dissertation slices of scripts/openalex_history_harvest.py (/mnt/e/openalex-history-2026-11-08/dissertations,
357,136 works with a History or History and Philosophy of Science topic anywhere). Kept here:
- primary topic History (1202) or HPS (1207): a topic model, not the degree programme, so the ingest's History screen
  still decides what enters the graph;
- an open copy (best_oa_location with a PDF or landing page; ProQuest links dropped, they are not open);
- not held: no PDF of ours under the same title key (scripts/find_aha_repository_links.py held_titles(): the extracted
  dissertations plus registered browser downloads), and not already offered on an AHA link page;
- level from the repositories' own type labels on every location (raw_type): 'doctoral' (doctoralThesis, PhD,
  COAR c_db06, Väitöskirja, tesis doctoral, doutorado ...), 'not_doctoral' (master/bachelor/mémoire/mestrado/pregrado
  ..., dropped), else 'probable' ('Dissertation', 'Hochschulschrift', ETD) or 'unknown' ('Thesis', no label). The
  registration guard (>= 100 pages) catches master's theses that slip through.
Institution = the host of the repository the copy sits in (OpenAlex rarely has the author's affiliation on a thesis);
aggregators (LA Referencia, Americanae, RCAAP, OpenGrey ...) have none. Country = the host institution's country
(OpenAlex institutions, cached in hosts.json), else the repository's own country (OpenAlex sources, sources.json).

Writes <out>/links.csv (metadata only) and <out>/pages/<country>.html (aggregators get their own page): first the
theses the repository labels doctoral, then those with no degree stated; institutions with the most missing theses
first, newest first.

    python3 scripts/openalex_dissertation_links.py --out data/field-research/openalex-dissertation-links-2026-11-08
"""
import argparse, collections, csv, glob, gzip, html, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from find_aha_repository_links import held_titles, title_key  # noqa: E402

SRC = '/mnt/e/openalex-history-2026-11-08/dissertations'
AHA_LINKS = ROOT / 'data/field-research/aha-repository-links-2026-11-04'
KEY = Path(os.path.expanduser('~/.config/openalex/key'))
UA = 'historiography-kg/0.1 (https://github.com/jburnford/historiography)'

DOCTORAL = re.compile(r'doctor|\bph\.?\s?d\b|c_db06|väitöskirja|tesis doctoral|doutorado|thèse de doctorat|dr\.\s?phil|'
                      r'proefschrift|doktor|habilitation|thesis \(phd\)|dphil|d\.phil', re.I)
NOT_DOC = re.compile(r'master|bachelor|\bmémoire|mestrado|maestr[ií]a|pregrado|licenciatura|honou?rs|undergrad|'
                     r'c_bdcc|c_7a1f|student|\bma thesis|\bm\.a\.|\bmphil|\bm\.phil|magister|diplom|tcc|trabajo de grado|'
                     r'trabalho de conclus|specialization|especializa', re.I)
AGGREGATOR = re.compile(r'LA Referencia|Americanae|RCAAP|OpenGrey|Institutional Repositories DataBase|\bBASE\b|NARCIS|'
                        r'DART-Europe|\bCORE\b|Directory of Open Access|OpenAIRE|Zenodo', re.I)
PROBABLE = re.compile(r'dissertation|hochschulschrift|\betd\b|electronic thesis or dissertation|tesis\b|thèse\b', re.I)


def level(w):
    ts = ' | '.join((l.get('raw_type') or '') for l in w.get('locations') or [])
    if DOCTORAL.search(ts):
        return 'doctoral'
    if NOT_DOC.search(ts):
        return 'not_doctoral'
    if PROBABLE.search(ts):
        return 'probable'
    return 'unknown'


def offered_before():
    """Title keys already on an AHA link page (matches tables of the 2026-11-04 route)."""
    keys = set()
    for p in AHA_LINKS.glob('*.csv'):
        with p.open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r.get('title'):
                    keys.add(title_key(r['title']))
    return keys


def hosts(ids, cache_path, entity='institutions'):
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    want = sorted(i for i in ids if i and i not in cache)
    key = KEY.read_text().strip()
    for i in range(0, len(want), 50):
        q = dict(filter='openalex:' + '|'.join(x.rsplit('/', 1)[-1] for x in want[i:i + 50]),
                 select='id,display_name,country_code', per_page=50, api_key=key)
        for t in range(6):
            try:
                with urllib.request.urlopen(urllib.request.Request(f'https://api.openalex.org/{entity}?' +
                                                                   urllib.parse.urlencode(q), headers={'User-Agent': UA}),
                                            timeout=60) as r:
                    d = json.load(r)
                break
            except Exception:
                time.sleep(2 * 2 ** t)
        else:
            continue
        for r in d['results']:
            cache[r['id']] = dict(name=r['display_name'], country=r.get('country_code') or '')
        for x in want[i:i + 50]:
            cache.setdefault(x, dict(name='', country=''))
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
    return cache


def rows():
    for p in sorted(glob.glob(f'{SRC}/*.jsonl.gz')):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    held, offered = held_titles(), offered_before()
    rep, keep = collections.Counter(), []
    for w in rows():
        rep['dissertations'] += 1
        pt = ((w.get('primary_topic') or {}).get('subfield') or {}).get('id', '')
        if not (pt.endswith('/1202') or pt.endswith('/1207')):
            continue
        rep['primary_topic_history'] += 1
        oa = w.get('best_oa_location') or {}
        pdf, land = oa.get('pdf_url') or '', oa.get('landing_page_url') or ''
        if 'proquest' in (pdf + land).lower():
            pdf = land = ''
        if not (pdf or land):
            rep['no_open_copy'] += 1; continue
        lv = level(w)
        if lv == 'not_doctoral':
            rep['not_doctoral'] += 1; continue
        tk = title_key(w.get('title') or '')
        if len(tk) < 12:
            rep['title_too_short'] += 1; continue
        if tk in held:
            rep['held'] += 1; continue
        if tk in offered:
            rep['offered_on_aha_pages'] += 1; continue
        src = oa.get('source') or {}
        a = (w.get('authorships') or [{}])[0]
        keep.append(dict(openalex=w['id'].rsplit('/', 1)[-1], level=lv, year=w.get('publication_year') or '',
                         author=((a.get('author') or {}).get('display_name') or a.get('raw_author_name') or ''),
                         title=re.sub(r'\s+', ' ', w.get('title') or '').strip(),
                         host=src.get('host_organization') or '', repository=src.get('display_name') or '',
                         source=(src.get('id') or '').rsplit('/', 1)[-1],
                         pdf_url=pdf, landing_url=land, doi=w.get('doi') or ''))
        rep['to_offer_' + lv] += 1
    # one row per title key (the same thesis in two repositories): the one with a PDF link, then doctoral
    rank = {'doctoral': 0, 'probable': 1, 'unknown': 2}
    best = {}
    for r in keep:
        k = (title_key(r['title']), r['author'].split()[-1].lower() if r['author'] else '')
        if k not in best or (not best[k]['pdf_url'], rank[best[k]['level']]) > (not r['pdf_url'], rank[r['level']]):
            best[k] = r
    keep = list(best.values())
    rep['offered_after_dedup'] = len(keep)
    H = hosts({r['host'] for r in keep if r['host'].startswith('https://openalex.org/I')}, args.out / 'hosts.json')
    S = hosts({'https://openalex.org/' + r['source'] for r in keep if r['source'] and not r['host']},
              args.out / 'sources.json', 'sources')
    for r in keep:
        h = H.get(r['host']) or S.get('https://openalex.org/' + r['source']) or {}
        if AGGREGATOR.search(r['repository']):          # an aggregator's host country is not the thesis's
            r['institution'], r['country'] = '', 'aggregator-' + re.sub(r'\W+', '-', r['repository'].split('(')[0].strip())
        else:
            r['institution'] = (h.get('name') or '') if r['host'] else ''
            r['country'] = h.get('country') or ''
    cols = ['openalex', 'level', 'year', 'author', 'title', 'institution', 'country', 'repository', 'pdf_url',
            'landing_url', 'doi']
    with open(args.out / 'links.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, cols, extrasaction='ignore'); wr.writeheader()
        wr.writerows(sorted(keep, key=lambda r: (r['country'], r['institution'], r['title'])))
    pages = args.out / 'pages'; pages.mkdir(exist_ok=True)
    by_c = collections.defaultdict(list)
    for r in keep:
        by_c[r['country'] or 'no-country'].append(r)
    index = []
    for c, rs in sorted(by_c.items(), key=lambda x: -len(x[1])):
        gap = collections.Counter(r['institution'] or r['repository'] for r in rs)
        rs.sort(key=lambda r: (-gap[r['institution'] or r['repository']], r['institution'] or r['repository'],
                               -(r['year'] or 0)))
        parts = ['<!doctype html><meta charset="utf-8"><title>Open history dissertations: ' + html.escape(c) + '</title>',
                 '<style>body{font:14px system-ui;max-width:64em;margin:2em auto}a:visited{color:#999}li{margin:.3em 0}'
                 'h2{margin-top:2em}.l{color:#888;font-size:12px}</style>',
                 f'<h1>{html.escape(c)}: {len(rs)} open history dissertations we hold no PDF for</h1>',
                 '<p>From OpenAlex (primary topic History or HPS; level from the repository\'s own label). Visited links '
                 'turn grey. Save PDFs into <code>E:\\historiography-dissertation-pdfs</code>. "PDF" links open the file; '
                 'others open the repository page.</p>']
        for title, part in (('Labelled doctoral by the repository', [r for r in rs if r['level'] == 'doctoral']),
                            ('Degree not stated (Dissertation / Thesis / no label): check it is a PhD before saving',
                             [r for r in rs if r['level'] != 'doctoral'])):
            if not part:
                continue
            parts.append(f'<h2 style="border-top:3px solid #333;padding-top:.5em">{html.escape(title)}: {len(part)}</h2>')
            gp = collections.Counter(r['institution'] or r['repository'] for r in part)
            inst = None
            for r in part:
                name = r['institution'] or r['repository'] or '(repository unknown)'
                if name != inst:
                    if inst is not None:
                        parts.append('</ol>')
                    parts.append(f'<h3>{html.escape(name)} ({gp[r["institution"] or r["repository"]]})</h3><ol>')
                    inst = name
                url = r['pdf_url'] or r['landing_url']
                parts.append(f'<li><a href="{html.escape(url)}">{html.escape(r["author"] or "?")} ({r["year"]})</a> — '
                             f'{html.escape(r["title"][:300])} <span class="l">{r["level"]}{", PDF" if r["pdf_url"] else ""}'
                             f'</span></li>')
            parts.append('</ol>')
        (pages / f'{c}.html').write_text('\n'.join(parts) + '\n', encoding='utf-8')
        index.append((c, len(rs), sum(r['level'] == 'doctoral' for r in rs), sum(bool(r['pdf_url']) for r in rs)))
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(rep.items())), indent=1) + '\n')
    with open(args.out / 'countries.csv', 'w', newline='') as f:
        wr = csv.writer(f); wr.writerow(['country', 'theses', 'doctoral_label', 'direct_pdf']); wr.writerows(index)
    print(json.dumps(dict(sorted(rep.items()))))
    for c, n, d, p in index[:25]:
        print(f'{c:12s} {n:6d}  doctoral {d:6d}  pdf {p:6d}')


if __name__ == '__main__':
    main()
