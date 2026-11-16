"""Helpers for the USER-RUN OAI listing (list-holdings.sh): pick-sets and build. Reads only files the user saved.
  python3 user_run_us.py pick-sets   -> listing-sets.tsv
  python3 user_run_us.py build       -> listing-ai-excluded-urls.tsv (+ .records.csv) for fetch.sh"""
import collections, csv, sys
import xml.etree.ElementTree as ET
from common import *
from match import link
from analyze import pass_one
sys.path.insert(0, str(ROOT / 'scripts'))
from user_run_canada import flatten, direct_dspace  # noqa: E402

LISTINGS = Path('/mnt/e/us-theses-resurvey-2026-11-16/listings')
OAI = '{http://www.openarchives.org/OAI/2.0/}'
DC = '{http://purl.org/dc/elements/1.1/}'
HOSTS = {'oaktrust.library.tamu.edu': 'Texas A&M Univ.', 'jscholarship.library.jhu.edu': 'Johns Hopkins Univ.',
         'digital.lib.washington.edu': 'Univ. of Washington', 'udspace.udel.edu': 'Univ. of Delaware',
         'academiccommons.columbia.edu': 'Columbia Univ.'}
SET_YES = re.compile(r'(histor|doctor|dissert|ph\.? ?d|theses|retrospect|digiti[sz]ed|etd)', re.I)
SET_NO = re.compile(r'(art history|history of art|architectur|undergrad|honors|honours|master|senior|capstone)', re.I)


def pick_sets():
    rows = []
    for host in HOSTS:
        sets = []
        for p in sorted((LISTINGS / host).glob('sets-*.xml')):
            root = ET.fromstring(p.read_text())
            for s in root.iter(OAI + 'set'):
                sets.append((s.findtext(OAI + 'setSpec', ''), s.findtext(OAI + 'setName', '')))
        if not sets:
            print(f'{host}: no ListSets saved (run: bash list-holdings.sh sets)')
            continue
        if host == 'academiccommons.columbia.edu':
            chosen = [(sp, nm) for sp, nm in sets if sp == 'degree_level:Doctoral'] or [(sp, nm) for sp, nm in sets if 'octor' in nm]
            prefix = 'oai_dc'
        else:
            cols = [(sp, nm) for sp, nm in sets if sp.startswith('col_')]
            hist = [(sp, nm) for sp, nm in cols if re.search(r'histor', nm, re.I) and not SET_NO.search(nm)]
            gen = [(sp, nm) for sp, nm in cols if SET_YES.search(nm) and not SET_NO.search(nm)
                   and re.search(r'(doctor|dissert|ph\.? ?d|electronic theses|retrospect|digiti|etd)', nm, re.I)]
            chosen = list(dict.fromkeys(hist + gen))
            prefix = 'xoai'
        rows += [(host, prefix, sp, nm) for sp, nm in chosen]
        print(f'{host}: {len(sets)} sets, {len(chosen)} chosen')
    with (OUT / 'listing-sets.tsv').open('w') as f:
        f.write('host\tprefix\tset\tlabel\n')
        for r in rows:
            f.write('\t'.join(x.replace('\t', ' ') for x in r) + '\n')
    print('wrote listing-sets.tsv', len(rows), '(edit by hand if a set looks wrong)')


def records(host):
    for page in sorted((LISTINGS / host).glob('records-*/page-*.xml')):
        try:
            root = ET.fromstring(page.read_text())
        except ET.ParseError:
            continue
        for rec in root.iter(OAI + 'record'):
            h = rec.find(OAI + 'header')
            md = rec.find(OAI + 'metadata')
            if h is None or h.get('status') == 'deleted' or md is None or not len(md):
                continue
            ident = h.findtext(OAI + 'identifier')
            if md[0].tag.endswith('dc'):
                el = md[0]
                vals = lambda t: [x.text or '' for x in el.iter(DC + t)]  # noqa: E731
                ids = vals('identifier')
                files = [u for u in ids if '/download' in u or u.lower().endswith('.pdf')]
                yield {'id': ident, 'title': (vals('title') or [''])[0], 'authors': vals('creator') + vals('contributor')[:1],
                       'year': int((re.findall(r'(1[89]\d\d|20\d\d)', ' '.join(vals('date'))) or [0])[0]) or None,
                       'files': files, 'landing': next((u for u in ids if u.startswith('http')), '')}
            else:
                m, bits = flatten(md[0])
                files = [direct_dspace(d.get('url'), host) or d.get('url') for b, d in bits
                         if b == 'ORIGINAL' and (d.get('format') or '').endswith('pdf') and d.get('url')]
                yield {'id': ident, 'title': (m.get('dc.title') or [''])[0],
                       'authors': m.get('dc.contributor.author') or m.get('dc.creator') or [],
                       'year': int(((m.get('dc.date.issued') or ['0'])[0])[:4] or 0) or None,
                       'files': files, 'landing': next((v for v in m.get('dc.identifier.uri', []) if v.startswith('http')), ''),
                       'embargo': '; '.join(v for k in m if 'embargo' in k for v in m[k])[:80]}


def build():
    U, _ = universe()
    byinst = collections.defaultdict(list)
    for r in U:
        byinst[r['inst_name']].append(r)
    p1 = pass_one()
    already = set()
    for f in ('open-urls.tsv', 'ai-excluded-urls.tsv', 'ai-excluded-landing.tsv'):
        p = OUT / f
        if p.exists():
            already |= {l.split('\t')[1] for l in p.read_text().splitlines() if l}
    rows, nofile = [], []
    for host, inst in HOSTS.items():
        works = [dict(w, locations=[]) for w in records(host)]
        recs = [r for r in byinst[inst] if not (r['id'] in p1 and p1[r['id']]['status'] == 'downloaded')]
        for aid, (w, s, n) in link(recs, works).items():
            r = next(x for x in recs if x['id'] == aid)
            name = file_name(r)
            if name in already:
                continue
            if w['files']:
                rows.append((w['files'][0], name, host, '10', aid, w['id'], w['title']))
            else:
                nofile.append((aid, host, w['id'], w.get('landing', ''), w.get('embargo', '')))
        print(host, len(works), 'records in listing')
    with (OUT / 'listing-ai-excluded-urls.tsv').open('w') as f:
        for r in rows:
            f.write('\t'.join(r[:4]) + '\n')
    with (OUT / 'listing-ai-excluded-urls.records.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['url', 'file', 'host', 'delay', 'aha_id', 'oai_id', 'title'])
        w.writerows(rows)
    with (OUT / 'listing-no-file.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['aha_id', 'host', 'oai_id', 'landing', 'embargo'])
        w.writerows(nofile)
    print(len(rows), 'new file links;', len(nofile), 'matched records without a public file')


def file_name(r):
    """aha-b7-<Surname>-<Given>-<YEAR>-<Univ>-aha<ID>-<title>.pdf (register_aha_browser_downloads.file_hints)."""
    def slug(s, n):
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
        return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:n].strip('-')
    r = dict(r, inst_name=r.get('inst_name') or r.get('institution'), id=r.get('id') or r.get('aha_id'))
    sur, _, giv = r['dissertator'].partition(',')
    giv = re.sub(r'\b(Jr|Sr|II|III|IV)\b\.?', '', giv).strip().split(' ')[0] if giv.strip() else 'X'
    return (f"aha-b7-{slug(sur, 30)}-{slug(giv, 20) or 'X'}-{r['year']}-{slug(r['inst_name'], 30)}-aha{r['id']}-"
            f"{slug(r['title'], 40)}.pdf")


if __name__ == '__main__':
    {'pick-sets': pick_sets, 'build': build}[sys.argv[1]]()
