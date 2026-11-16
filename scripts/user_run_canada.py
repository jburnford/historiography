"""Canada stage of scripts/user_run_download_lists.py (2026-11-14). Run: python3 scripts/user_run_download_lists.py canada

Steps (all requests through user_run_download_lists helpers; no thesis file is requested):
 1. robots.txt of every Canadian History-PhD repository host (and old addresses, and LAC), classed.
 2. OAI-PMH (xoai) of the thesis sets of OPEN DSpace 7 hosts only (robots allows the OAI path for '*' and
    names no AI client): History doctoral records with their public ORIGINAL bitstreams.
 3. AHA directory records for Canadian departments, all years, not held, looked up in OpenAlex + DataCite by
    scripts/find_aha_repository_links.py (run separately, output in /mnt/e/user-run-downloads-2026-11-14/canada-aha).
 4. OpenAlex repository-source listing (History subfield 1202 topics, type dissertation) for the
    ai-excluded/browser hosts, as an unscreened candidate count (no degree/department in OpenAlex).
Held = the project's registry: dissertations.csv (extracted PDFs) by id and folded title, doctorates.json
aha_id for held records, and registered browser downloads (find_aha_repository_links.held_titles/held_aha_ids).
"""
import collections, csv, difflib, html, json, re, sys, threading, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import user_run_download_lists as U  # noqa: E402
from find_aha_repository_links import held_titles, held_aha_ids  # noqa: E402

ROOT = U.ROOT
F = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
AHA_RUN = Path('/mnt/e/user-run-downloads-2026-11-14/canada-aha')
OUTDIR = U.OUT

DS7 = (['/server/api/core/bitstreams/00000000-0000-0000-0000-000000000000/content',
        '/bitstreams/00000000-0000-0000-0000-000000000000/download'], ['/server/oai/request'])
EPRINTS = (['/1234/1/thesis.pdf', '/id/eprint/1234/1/thesis.pdf'], ['/cgi/oai2'])
BEPRESS = (['/cgi/viewcontent.cgi?article=1&context=etd'], ['/do/oai/'])
ISLANDORA = (['/_flysystem/fedora/2024-01/etd.pdf', '/system/files/etd.pdf'], ['/oai/request'])
UBCOC = (['/media/download/pdf/24/1.0000000/0'], ['/oai'])
LAC = (['/obj/s4/f2/dsk1/tape1/PQDD_0001/NQ00001.pdf', '/'], ['/oai'])

# key, university, AHA department prefix, registry key, OpenAlex source, [(host, software, paths, role)],
# history PhD note, OAI sets harvested (open hosts only)
UNIS = [
    ('toronto', 'University of Toronto', 'Univ. of Toronto', 'toronto', 'S4306400261',
     [('utoronto.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'TSpace'), ('tspace.library.utoronto.ca', 'old address', DS7, 'redirect')],
     'History PhD', []),
    ('york', 'York University', 'York Univ.', 'york', 'S4306400473',
     [('yorkspace.library.yorku.ca', 'DSpace 7', DS7, 'YorkSpace')], 'History PhD',
     [('col_10315_27577', 'History (ETD)'), ('col_10315_32816', 'Department of History'),
      ('col_10315_26313', 'Doctoral Theses (retrospective, prior to 2013)')]),
    ('mcgill', 'McGill University', 'McGill Univ.', 'mcgill', 'S4306401568',
     [('mcgill.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'eScholarship@McGill'), ('escholarship.mcgill.ca', 'old address', DS7, 'redirect')],
     'History PhD (Dept of History and Classical Studies)', []),
    ('ubc', 'University of British Columbia', 'Univ. of British Columbia', 'ubc', 'S4377196297',
     [('open.library.ubc.ca', 'UBC Open Collections (theses)', UBCOC, 'Open Collections'),
      ('circle.library.ubc.ca', 'DSpace (cIRcle back end)', DS7, 'cIRcle')], 'History PhD', []),
    ('queens', "Queen's University", "Queen's Univ., Can.", 'queens', 'S4306402568',
     [('queensu.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'QSpace'), ('qspace.library.queensu.ca', 'old address', DS7, 'redirect')],
     'History PhD', []),
    ('alberta', 'University of Alberta', 'Univ. of Alberta', 'alberta', 'S7407053046',
     [('ualberta.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'ERA'), ('era.library.ualberta.ca', 'old address', DS7, 'redirect')],
     'History PhD (Dept of History, Classics and Religion)', []),
    ('western', 'Western University', 'Univ. of Western Ontario', 'western', 'S4306400648',
     [('uwo.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'Scholarship@Western'), ('ir.lib.uwo.ca', 'old bepress address (moved notice)', BEPRESS, 'redirect')],
     'History PhD', []),
    ('mcmaster', 'McMaster University', 'McMaster Univ.', 'mcmaster', 'S4306402139',
     [('macsphere.mcmaster.ca', 'DSpace 7', DS7, 'MacSphere')], 'History PhD',
     [('col_11375_272', 'Open Access Dissertations and Theses'), ('col_11375_15484', 'Digitized Open Access Dissertations and Theses')]),
    ('ottawa', 'University of Ottawa', 'Univ. of Ottawa', 'ottawa', 'S4306400902',
     [('ruor.uottawa.ca', 'DSpace 7', DS7, 'uO Research')], 'History PhD (Histoire)',
     [('col_10393_244', 'Theses, 1910-2010'), ('col_10393_11105', 'Theses, 2011-'), ('col_10393_19749', 'Theses - Embargo')]),
    ('montreal', 'Université de Montréal', 'Univ. de Montreal', 'montreal', 'S4306402422',
     [('umontreal.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'Papyrus'), ('papyrus.bib.umontreal.ca', 'old address', DS7, 'redirect')],
     'Histoire PhD (+ médiévales, histoire des sciences: adjacent)', []),
    ('laval', 'Université Laval', 'Univ. Laval', 'laval', '',
     [('corpus.ulaval.ca', 'DSpace 7 (CorpusUL)', DS7, 'CorpusUL')], 'Histoire PhD', []),
    ('uqam', 'UQAM', 'Univ. du Quebec, Montreal', 'uqam', '',
     [('archipel.uqam.ca', 'EPrints', EPRINTS, 'Archipel')], 'Histoire PhD', []),
    ('dalhousie', 'Dalhousie University', 'Dalhousie Univ.', 'dalhousie', 'S7407064432',
     [('dal.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'DalSpace'), ('dalspace.library.dal.ca', 'old address', DS7, 'redirect')],
     'History PhD', []),
    ('manitoba', 'University of Manitoba', 'Univ. of Manitoba', 'manitoba', 'S4306400554',
     [('mspace.lib.umanitoba.ca', 'DSpace 7', DS7, 'MSpace')], 'History PhD (joint Manitoba/Winnipeg)',
     [('col_1993_6', 'FGPS - Electronic Theses and Practica'), ('col_1993_3098', 'Manitoba Heritage Theses')]),
    ('usask', 'University of Saskatchewan', 'Univ. of Saskatchewan', 'usask', 'S7407063267',
     [('harvest.usask.ca', 'DSpace 7', DS7, 'HARVEST')], 'History PhD',
     [('col_10388_381', 'Graduate Theses and Dissertations'), ('col_10388_12056', 'History')]),
    ('calgary', 'University of Calgary', 'Univ. of Calgary', 'calgary', 'S4306402261',
     [('ucalgary.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'PRISM'), ('prism.ucalgary.ca', 'old address', DS7, 'redirect')],
     'History PhD', []),
    ('sfu', 'Simon Fraser University', 'Simon Fraser Univ.', 'sfu', '',
     [('summit.sfu.ca', 'Islandora (Drupal)', ISLANDORA, 'Summit')], 'History PhD', []),
    ('carleton', 'Carleton University', 'Carleton Univ.', 'carleton', '',
     [('carleton.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'CURVE'), ('repository.library.carleton.ca', 'old address', DS7, 'redirect')],
     'History PhD', []),
    ('concordia', 'Concordia University', 'Concordia Univ., Can.', 'concordia', 'S4306400871',
     [('spectrum.library.concordia.ca', 'EPrints', EPRINTS, 'Spectrum')], 'History PhD', []),
    ('memorial', 'Memorial University', 'Memorial Univ., Newfoundland', 'memorial', 'S4306401319',
     [('memorial.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'Research Repository'), ('research.library.mun.ca', 'old address', DS7, 'redirect')],
     'History PhD', []),
    ('unb', 'University of New Brunswick', 'Univ. of New Brunswick', 'unb', '',
     [('unbscholar.lib.unb.ca', 'DSpace 7', DS7, 'UNB Scholar')], 'History PhD', []),
    ('guelph', 'University of Guelph', 'Univ. of Guelph', 'guelph', 'S4306401043',
     [('atrium.lib.uoguelph.ca', 'DSpace 7', DS7, 'Atrium')], 'History PhD (Tri-University programme)', []),
    ('waterloo', 'University of Waterloo', 'Univ. of Waterloo', 'waterloo', 'S4306401661',
     [('uwspace.uwaterloo.ca', 'DSpace 7', DS7, 'UWSpace')], 'History PhD (Tri-University programme)', []),
    ('uvic', 'University of Victoria', 'Univ. of Victoria', 'uvic', '',
     [('dspace.library.uvic.ca', 'DSpace 7', DS7, 'UVicSpace')], 'History PhD',
     [('col_1828_12', 'Electronic Theses and Dissertations (ETD)'), ('col_1828_20823', 'Digitized Theses and Dissertations')]),
    ('sherbrooke', 'Université de Sherbrooke', None, 'sherbrooke', '',
     [('usherbrooke.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'Savoirs UdeS'), ('savoirs.usherbrooke.ca', 'old address', DS7, 'redirect')],
     'Histoire PhD', []),
    ('laurier', 'Wilfrid Laurier University', 'Wilfrid Laurier Univ.', 'laurier', 'S4306401971',
     [('scholars.wlu.ca', 'bepress Digital Commons', BEPRESS, 'Scholars Commons')], 'History PhD (Tri-University programme)', []),
    ('windsor', 'University of Windsor', None, None, 'S4306400430',
     [('scholar.uwindsor.ca', 'old bepress address', BEPRESS, 'redirect'), ('uwindsor.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'Scholarship at UWindsor')],
     'no History PhD (MA only) — not a target', []),
    ('brock', 'Brock University', None, None, 'S4306401333',
     [('brocku.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'Brock Digital Repository'), ('dr.library.brocku.ca', 'old address', DS7, 'redirect')],
     'no History PhD (MA only) — not a target', []),
    ('trent', 'Trent University', 'Trent Univ.', None, '',
     [('digitalcollections.trentu.ca', 'Islandora (Drupal)', ISLANDORA, 'Trent Digital Collections')],
     'PhD in Canadian Studies / Cultural Studies (History-adjacent); 1 AHA record', []),
    ('lakehead', 'Lakehead University', None, None, '',
     [('knowledgecommons.lakeheadu.ca', 'DSpace 7', DS7, 'Knowledge Commons')], 'no History PhD (MA only) — not a target', []),
    ('regina', 'University of Regina', None, None, 'S4306402576',
     [('uregina.scholaris.ca', 'DSpace 7 (Scholaris)', DS7, 'oURspace'), ('ourspace.uregina.ca', 'old address', DS7, 'redirect')],
     'History PhD exists only by special case (Canadian Plains Studies PhD is adjacent) — check', []),
    ('moncton', 'Université de Moncton', None, None, '', [], 'no History PhD (maîtrise only) — not a target', []),
    ('lac', 'Library and Archives Canada (Theses Canada)', None, None, '',
     [('recherche-collection-search.bac-lac.gc.ca', 'LAC Collection Search', LAC, 'Collection Search'),
      ('central.bac-lac.gc.ca', 'LAC object server', LAC, 'object files'),
      ('www.collectionscanada.gc.ca', 'old Theses Canada PDF host', LAC, 'old PDFs'),
      ('library-archives.canada.ca', 'LAC website', LAC, 'website'),
      ('amicus.collectionscanada.gc.ca', 'old AMICUS', LAC, 'retired')],
     'national fallback: Theses Canada (microfiche 1965-, digital PDF c.1998-2014 for many)', []),
]

# published contact / sanctioned interface pages (read from the projects' own source-check notes or the
# repository's documentation; blank = not looked up, never guessed)
ASK = {
    'corpus.ulaval.ca': ('CorpusUL open-data page (documented API/OAI): https://www.bibl.ulaval.ca/services/soutien-a-ledition-savante-et-a-la-recherche/corpusul-depot-institutionnel/donnees-ouvertes-de-corpusul', ''),
    'open.library.ubc.ca': ('Open Collections API with a registered key: https://wiki.prod.apps.ctlt.ubc.ca/Library%3AOpen_Collections', 'block page names UBC IT Service Centre help@it.ubc.ca for wrongful blocks'),
    'circle.library.ubc.ca': ('Open Collections API (as above)', ''),
    'www.collectionscanada.gc.ca': ('', ''),
}

HIST = re.compile(r'\b(histor|histoire)', re.I)
NOT_HIST = re.compile(r'(art history|history of art|histoire de l.art|history and theory|art and art history|visual art)', re.I)
DOCT = re.compile(r'(doctor|ph\.? ?d|doctorat|docteur|^d\.? ?phil)', re.I)


def flatten(meta):
    """xoai metadata element -> {dotted.field: [values]} and ORIGINAL bitstreams [(name, format, url, size)]."""
    out = collections.defaultdict(list)
    bits = []
    X = '{http://www.lyncode.com/xoai}'

    def walk(el, path):
        for ch in el:
            if ch.tag == X + 'element':
                name = ch.get('name')
                if name == 'bundles':
                    for b in ch.findall(X + 'element'):
                        bname = next((f.text for f in b.findall(X + 'field') if f.get('name') == 'name'), '')
                        for bs in b.iter(X + 'element'):
                            if bs.get('name') == 'bitstream':
                                d = {f.get('name'): f.text for f in bs.findall(X + 'field')}
                                bits.append((bname, d))
                    continue
                walk(ch, path + ([name] if name == 'dc' or (name not in ('none',) and not re.fullmatch(r'[a-z]{2}(_[A-Z]{2})?|\*', name or '')) else []))
            elif ch.tag == X + 'field' and ch.get('name') == 'value' and ch.text:
                out['.'.join(path)].append(html.unescape(ch.text.strip()))
    walk(meta, [])
    return out, bits


def screen(m):
    keys = [k for k in m if re.search(r'(department|discipline|program|degree\.name|degree\.grantor|faculty|thesis\.degree)', k)]
    deptvals = [v for k in keys for v in m[k]]
    hist = any(HIST.search(v) and not NOT_HIST.search(v) for v in deptvals)
    degvals = [v for k in m if re.search(r'(degree|type)', k) for v in m[k]]
    doct = any(DOCT.search(v) for v in degvals) and not any(re.search(r'\b(master|maîtrise|m\.a\.|ma thesis)', v, re.I) for v in degvals
                                                            if not DOCT.search(v))
    return hist, doct, deptvals, degvals


def harvest_open(host, sets, store):
    base = f'https://{host}/server/oai/request'
    rows = {}
    try:
        for spec, label in sets:
            for rec in U.oai_records(base, 'xoai', spec, gap=2.0):
                h = rec.find(U.OAI + 'header')
                if h is not None and h.get('status') == 'deleted':
                    continue
                ident = h.findtext(U.OAI + 'identifier')
                md = rec.find(U.OAI + 'metadata')
                if md is None or not len(md):
                    continue
                m, bits = flatten(md[0])
                hist, doct, dept, deg = screen(m)
                if not (hist and doct):
                    continue
                files = [d for b, d in bits if b == 'ORIGINAL' and (d.get('format') or '').endswith('pdf')]
                rows[ident] = dict(oai_id=ident, set=label, title=(m.get('dc.title') or [''])[0],
                                   author=(m.get('dc.contributor.author') or m.get('dc.creator') or [''])[0],
                                   year=((m.get('dc.date.issued') or m.get('dc.date.accessioned') or [''])[0])[:4],
                                   dept='; '.join(sorted(set(dept)))[:200], degree='; '.join(sorted(set(deg)))[:200],
                                   handle=next((v for v in m.get('dc.identifier.uri', []) if 'handle' in v), ''),
                                   embargo='; '.join(v for k in m if 'embargo' in k for v in m[k])[:80],
                                   files=[(d.get('name'), d.get('url'), d.get('size')) for d in files])
        store[host] = ('ok', list(rows.values()))
    except Exception as e:  # noqa: BLE001
        store[host] = (f'stopped: {e}', list(rows.values()))


def held_index():
    titles = held_titles()
    ids = held_aha_ids()
    recs = json.loads((F / 'doctorates.json').read_text())
    with (F / 'dissertations.csv').open(newline='') as f:
        held_rows = list(csv.DictReader(f))
    held_ids = {r['id'] for r in held_rows}
    per_inst = collections.Counter(r['institution'] for r in held_rows if r['country'] == 'CA')
    reg = collections.defaultdict(list)
    for r in recs:
        if ':' not in r['institution'] and r.get('country') in (None, 'CA'):
            reg[r['institution']].append(r)
    return titles, ids, held_ids, per_inst, reg


def is_held(title, titles):
    return U.title_key(title) in titles


def direct_dspace(url, host):
    m = re.search(r'/bitstreams/([0-9a-f-]{36})/(download|content)', url or '')
    return f'https://{host}/server/api/core/bitstreams/{m.group(1)}/content' if m else ''


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    titles, aha_held, held_ids, per_inst, reg = held_index()

    # 1. robots
    hostrows = []
    hostclass = {}
    for key, uni, aha, regkey, src, hosts, note, sets in UNIS:
        for host, sw, (fpaths, oaipaths), role in hosts:
            c = U.classify(host, fpaths, oaipaths)
            fh = urllib.parse.urlparse(c['final_url']).netloc
            if role == 'redirect' or (fh and fh != host):
                c['cls_note'] = f'old address; robots.txt request lands on {fh or "?"}'
            if host == 'corpus.ulaval.ca':
                c['cls'] = 'browser'
                c['rule'] = 'robots.txt request answered with a WAF page "Request Rejected" (support ID), not a robots file'
            if host == 'open.library.ubc.ca':
                c['cls'] = 'browser'
                c['rule'] = 'robots.txt request answered with the UBC "unusual activity" block page'
            if role == 'redirect' and fh and fh != host:
                c['cls'] = 'redirect'
                c['rule'] = f'old address: robots.txt request redirects to {fh}; classed there'
            ask, contact = ASK.get(host, ('', ''))
            hostclass[host] = c['cls']
            hostrows.append(dict(country='CA', university=uni, repository=role, host=host, software=sw, robots_class=c['cls'],
                                 robots_rule=c['rule'], robots_url=c['robots_url'], robots_status=c['robots_status'],
                                 checked=c['checked'], crawl_delay=c['crawl_delay'], oai_path=c['oai_path'],
                                 oai_allowed_star=c['oai_allowed_star'], oai_allowed_ai=c['oai_allowed_ai'],
                                 ai_clients_named=c['ai_excluded'][:300], purpose_comments=c['purpose_comments'][:400],
                                 contacts_in_robots=c['contacts'], sanctioned_bulk=ask, ask_route=contact,
                                 history_selection=note, note=c.get('cls_note', '')))
            print(f'{host:45s} {c["cls"]:12s} {c["rule"][:90]}', flush=True)

    # 2. OAI on open DSpace 7 hosts (cached in canada-oai-history-phd.json; rerun a host by removing its entry)
    cache = U.CACHE.parent / 'canada-oai-history-phd-v3.json'  # v3: 'dc' kept, entities unescaped
    store = {h: v for h, v in (json.loads(cache.read_text()).items() if cache.exists() else []) if v[0] == 'ok'}
    threads = []
    for key, uni, aha, regkey, src, hosts, note, sets in UNIS:
        if sets and hostclass.get(hosts[0][0]) == 'open':
            row = next(r for r in hostrows if r['host'] == hosts[0][0])
            if row['oai_allowed_star'] == 'yes' and row['oai_allowed_ai'] == 'yes' and hosts[0][0] not in store:
                t = threading.Thread(target=harvest_open, args=(hosts[0][0], sets, store))
                t.start()
                threads.append(t)
    for t in threads:
        t.join()
    json.dump(store, open(cache, 'w'))
    for h, (st, rows) in store.items():
        print('OAI', h, st, len(rows), flush=True)

    # 3. AHA records (OpenAlex + DataCite results of find_aha_repository_links.py)
    aha_q = list(csv.DictReader((AHA_RUN / 'queue.csv').open(newline='')))
    aha_m = {r['id']: r for r in csv.DictReader((AHA_RUN / 'matches.csv').open(newline=''))} if (AHA_RUN / 'matches.csv').exists() else {}
    aha_all = [r for r in csv.DictReader((ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.csv').open(newline=''))
               if r['status'] == 'completed']

    # 4. assemble per university
    already = set()
    for f in (ROOT / 'data/field-research/aha-repository-links-2026-11-04/wget').glob('*-urls.tsv'):
        already |= {l.split('\t')[0] for l in f.read_text().splitlines() if l}
    lists = collections.defaultdict(list)
    missing = []
    browser_items = []
    summary = []
    seen_keys = set(titles)
    for key, uni, aha, regkey, src, hosts, note, sets in UNIS:
        a_all = [r for r in aha_all if aha and r['department'].startswith(aha)]
        a_q = [r for r in aha_q if aha and r['department'].startswith(aha)]
        held = per_inst.get(regkey, 0) if regkey else 0
        regn = len(reg.get(regkey, [])) if regkey else 0
        oai_rows = store.get(hosts[0][0], ('', []))[1] if hosts else []
        oai_new = 0
        n_open = n_ai = n_browser = n_none = 0
        listed_titles = set()
        # 4a. OAI rows not held
        for r in oai_rows:
            tk = U.title_key(r['title'])
            if tk in seen_keys or tk in listed_titles:
                continue
            listed_titles.add(tk)
            oai_new += 1
            rid = 'oai-' + re.sub(r'[^A-Za-z0-9]+', '-', r['oai_id'].split(':')[-1])
            name = f"ca-{key}-{rid}-{U.slug(r['author'].split(',')[0], 30)}-{r['year']}.pdf"
            pdfs = [f for f in r['files'] if f[1]]
            if pdfs:
                pdfs.sort(key=lambda f: -int(f[2] or 0))
                url = direct_dspace(pdfs[0][1], hosts[0][0])
                if url and url not in already:
                    lists['open'].append((url, name, hosts[0][0], str(int(float(next(x for x in hostrows if x['host'] == hosts[0][0])['crawl_delay'] or 10))), key, rid, r['title'], r['year']))
                    n_open += 1
                    continue
            n_none += 1
            missing.append(dict(university=uni, record_id=rid, author=r['author'], year=r['year'], title=r['title'],
                                source=f'OAI {hosts[0][0]} ({r["set"]})', status='record without public PDF bitstream' + (f' (embargo {r["embargo"]})' if r['embargo'] else ''),
                                landing=r['handle'], lac_pointer=''))
        # 4b. AHA records not held (first: any record of the open host's harvested thesis sets with the same title,
        # whatever its department fields say; retrospective theses often carry no department)
        a_linked = 0
        idx = oai_title_index(hosts[0][0]) if hosts and hostclass.get(hosts[0][0]) == 'open' else {}
        for r in a_q:
            tk = U.title_key(r['title'])
            if tk in listed_titles:
                continue
            listed_titles.add(tk)
            hit = idx.get(tk)
            if hit and hit['files']:
                rid = f"aha{r['id']}"
                url = direct_dspace(sorted(hit['files'], key=lambda f: -int(f[2] or 0))[0][1], hosts[0][0])
                name = f"ca-{key}-{rid}-{U.slug(r['dissertator'].split(',')[0], 30)}-{r['year']}.pdf"
                delay = str(int(float(next(x for x in hostrows if x['host'] == hosts[0][0])['crawl_delay'] or 10)))
                if url and url not in already:
                    lists['open'].append((url, name, hosts[0][0], delay, key, rid, r['title'], r['year']))
                    n_open += 1
                    a_linked += 1
                    continue
            m = aha_m.get(r['id']) or {}
            url = m.get('pdf_url') or ''
            land = m.get('landing_url') or ''
            rid = f"aha{r['id']}"
            name = f"ca-{key}-{rid}-{U.slug(r['dissertator'].split(',')[0], 30)}-{r['year']}.pdf"
            target = url or land
            th = urllib.parse.urlparse(target).netloc
            if target:
                a_linked += 1
            if url:
                d = direct_dspace(url, th) or url
                cls = hostclass.get(th) or classify_other(th)
                if d in already:
                    continue
                if cls == 'open':
                    lists['open'].append((d, name, th, '10', key, rid, r['title'], r['year'])); n_open += 1
                elif cls == 'ai-excluded':
                    lists['ai-excluded'].append((d, name, th, '10', key, rid, r['title'], r['year'])); n_ai += 1
                else:
                    browser_items.append((uni, rid, r['dissertator'], r['year'], r['title'], d, land, cls)); n_browser += 1
            elif land:
                browser_items.append((uni, rid, r['dissertator'], r['year'], r['title'], '', land, hostclass.get(th) or classify_other(th)))
                n_browser += 1
            else:
                n_none += 1
                missing.append(dict(university=uni, record_id=rid, author=r['dissertator'], year=r['year'], title=r['title'],
                                    source='AHA directory', status='no open copy found (OpenAlex, DataCite)' + (' — pre-1998: print/microfiche era' if r['year'].isdigit() and int(r['year']) < 1998 else ''),
                                    landing='', lac_pointer=lac_pointer(r)))
        summary.append(dict(university=uni, key=key, programme=note, aha_records=len(a_all),
                            aha_not_held=len(a_q), aha_not_held_linked=a_linked, registry_records=regn, held=held,
                            oai_history_phd=len(oai_rows), oai_not_held=oai_new,
                            open_list=n_open, ai_excluded_list=n_ai, browser_page=n_browser, no_link=n_none))
    # 5. OpenAlex repository listing (History-subfield topics, type dissertation): unscreened candidates
    cand = []
    aha_keys = {U.title_key(r['title']): r['id'] for r in aha_all}
    listed = {U.title_key(x[6]) for v in lists.values() for x in v} | {U.title_key(b[4]) for b in browser_items} \
        | {U.title_key(m['title']) for m in missing}
    for s in summary:
        u = next(x for x in UNIS if x[0] == s['key'])
        src = u[4]
        if not src:
            s['openalex_history_topic_dissertations'] = ''
            s['openalex_not_held_unscreened'] = ''
            continue
        works = U.openalex_source_all(src, 'type:dissertation,topics.subfield.id:1202', tag='hist1202')
        n_new = 0
        for w in works:
            tk = U.title_key(w.get('title'))
            if not tk or tk in titles or tk in listed:
                continue
            n_new += 1
            loc = next((l for l in w.get('locations') or [] if (l.get('source') or {}).get('id', '').endswith(src)), {}) or {}
            pdf = loc.get('pdf_url') or ''
            host = urllib.parse.urlparse(pdf or loc.get('landing_page_url') or '').netloc
            cand.append(dict(university=s['university'], openalex_id=w['id'].rsplit('/', 1)[-1], year=w.get('publication_year'),
                             author='; '.join((a.get('author') or {}).get('display_name') or '' for a in (w.get('authorships') or [])[:2]),
                             title=w.get('title'), primary_topic=((w.get('primary_topic') or {}).get('display_name') or ''),
                             primary_subfield=(((w.get('primary_topic') or {}).get('subfield') or {}).get('display_name') or ''),
                             aha_id=aha_keys.get(tk, ''), file_url=direct_dspace(pdf, host) or pdf,
                             landing=loc.get('landing_page_url') or '', host=host, host_class=hostclass.get(host, '')))
        s['openalex_history_topic_dissertations'] = len(works)
        s['openalex_not_held_unscreened'] = n_new
    with (OUTDIR / 'canada-openalex-unscreened-candidates.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(cand[0]) if cand else ['university'])
        w.writeheader()
        w.writerows(cand)
    write_outputs(hostrows, lists, browser_items, missing, summary)


_other = {}
_idx = {}


def oai_title_index(host):
    """title_key -> {files, handle} for every record in the cached OAI pages of an open host (no requests)."""
    if host in _idx:
        return _idx[host]
    import xml.etree.ElementTree as ET
    out = {}
    stem = 'https_' + re.sub(r'[^A-Za-z0-9]+', '_', host) + '_server_oai_request'
    for p in (U.CACHE / 'oai').glob(stem + '*ListRecords*.xml'):
        try:
            root = ET.fromstring(p.read_text())
        except ET.ParseError:
            continue
        for rec in root.iter(U.OAI + 'record'):
            md = rec.find(U.OAI + 'metadata')
            if md is None or not len(md):
                continue
            m, bits = flatten(md[0])
            tk = U.title_key((m.get('dc.title') or [''])[0])
            files = [(d.get('name'), d.get('url'), d.get('size')) for b, d in bits
                     if b == 'ORIGINAL' and (d.get('format') or '').endswith('pdf') and d.get('url')]
            if tk and (tk not in out or files):
                out[tk] = dict(files=files, handle=next((v for v in m.get('dc.identifier.uri', []) if 'handle' in v), ''))
    _idx[host] = out
    return out


def classify_other(host):
    """Hosts reached through OpenAlex/DataCite links that are not in UNIS (resolvers, other repositories)."""
    if not host:
        return 'browser'
    if host in ('hdl.handle.net', 'doi.org', 'dx.doi.org'):
        return 'browser'
    if host not in _other:
        c = U.classify(host, ['/'], ['/oai/request'])
        _other[host] = c['cls']
    return _other[host]


def lac_pointer(r):
    if not r['year'].isdigit():
        return ''
    y = int(r['year'])
    q = urllib.parse.quote(f"{r['dissertator'].split(',')[0]} {r['title'][:60]}")
    if y >= 1965:
        return f'https://recherche-collection-search.bac-lac.gc.ca/eng/Home/Result?q_any={q}&DataSource=Library|ThesesCanada (Theses Canada: microfiche/PDF; search by hand)'
    return ''


def write_outputs(hostrows, lists, browser_items, missing, summary):
    with (OUTDIR / 'canada-hosts.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(hostrows[0]))
        w.writeheader()
        w.writerows(hostrows)
    for cls in ('open', 'ai-excluded'):
        rows = lists.get(cls, [])
        seen = set()
        with (OUTDIR / f'canada-{cls}-urls.tsv').open('w') as f:
            for url, name, host, delay, *_ in rows:
                if url in seen:
                    continue
                seen.add(url)
                f.write('\t'.join([url, name, host, delay]) + '\n')
        with (OUTDIR / f'canada-{cls}-urls.records.csv').open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['url', 'file', 'host', 'delay', 'university', 'record_id', 'title', 'year'])
            w.writerows(rows)
    parts = ['<!doctype html><meta charset="utf-8"><title>Canadian History PhDs: browser links</title>',
             '<style>body{font:14px system-ui;max-width:64em;margin:2em auto}a:visited{color:#999}li{margin:.3em 0}</style>',
             f'<h1>Canadian History PhDs not held: {len(browser_items)} links to open in a browser</h1>',
             '<p>Direct file link first where known, then the landing page. Save into '
             '<code>E:\\historiography-dissertation-pdfs\\canada-wget-2026-11-14\\browser\\</code> with the record id '
             '(aha… / oai-…) in the file name.</p>']
    by = collections.defaultdict(list)
    for it in browser_items:
        by[it[0]].append(it)
    for uni, items in sorted(by.items(), key=lambda x: -len(x[1])):
        parts.append(f'<h2>{html.escape(uni)} ({len(items)})</h2><ol>')
        for u, rid, who, yr, title, d, land, cls in items:
            links = ' '.join(f'<a href="{html.escape(x)}" target="_blank">{lab}</a>' for x, lab in ((d, 'file'), (land, 'landing')) if x)
            parts.append(f'<li>{links} — {html.escape(who)} ({yr}) {html.escape(title)} <small>[{rid}; {cls}]</small></li>')
        parts.append('</ol>')
    (OUTDIR / 'canada-browser.html').write_text('\n'.join(parts) + '\n')
    with (OUTDIR / 'canada-missing-no-link.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['university', 'record_id', 'author', 'year', 'title', 'source', 'status', 'landing', 'lac_pointer'])
        w.writeheader()
        w.writerows(missing)
    with (OUTDIR / 'canada-summary.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    for s in summary:
        print(s)


# ---------------------------------------------------------------- user-run listing of AI-excluded hosts
LISTINGS = Path('/mnt/e/user-run-downloads-2026-11-14/canada-listings')
LIST_HOSTS = {'utoronto.scholaris.ca': 'toronto', 'queensu.scholaris.ca': 'queens', 'uwo.scholaris.ca': 'western',
              'dal.scholaris.ca': 'dalhousie', 'mcgill.scholaris.ca': 'mcgill', 'ualberta.scholaris.ca': 'alberta',
              'umontreal.scholaris.ca': 'montreal', 'ucalgary.scholaris.ca': 'calgary', 'carleton.scholaris.ca': 'carleton',
              'memorial.scholaris.ca': 'memorial', 'usherbrooke.scholaris.ca': 'sherbrooke', 'atrium.lib.uoguelph.ca': 'guelph',
              'archipel.uqam.ca': 'uqam'}
SET_YES = re.compile(r'(histor|histoire|doctor|doctorat|dissert|ph\.? ?d|th[eè]ses?\b|retrospect|digiti[sz]ed|etd)', re.I)
SET_NO = re.compile(r'(art history|history of art|histoire de l.art|undergrad|honours|honors|master|maîtrise|mémoire|'
                    r'3mt|three minute|bachelor|course|syllab|conference|journal|data ?set)', re.I)


def pick_sets():
    """From saved ListSets pages, choose collection sets that can hold History doctoral theses."""
    import xml.etree.ElementTree as ET
    rows = []
    for host in LIST_HOSTS:
        d = LISTINGS / host
        sets = []
        for p in sorted(d.glob('sets-*.xml')):
            root = ET.fromstring(p.read_text())
            for s in root.iter(U.OAI + 'set'):
                sets.append((s.findtext('o:setSpec', '', U.OAI_NS), s.findtext('o:setName', '', U.OAI_NS)))
        if not sets:
            print(f'{host}: no ListSets saved (run: bash canada-list-holdings.sh sets)')
            continue
        eprints = host == 'archipel.uqam.ca'
        if eprints:
            chosen = [(sp, nm) for sp, nm in sets if re.search(r'histoire', nm, re.I) and not SET_NO.search(nm)]
        else:
            cols = [(sp, nm) for sp, nm in sets if sp.startswith('col_')]
            hist = [(sp, nm) for sp, nm in cols if re.search(r'(histor|histoire)', nm, re.I) and not SET_NO.search(nm)]
            gen = [(sp, nm) for sp, nm in cols if SET_YES.search(nm) and not SET_NO.search(nm)
                   and re.search(r'(doctor|doctorat|dissert|ph\.? ?d|th[eè]ses|retrospect|digiti|etd)', nm, re.I)]
            chosen = list(dict.fromkeys(hist + gen))
        for sp, nm in chosen:
            rows.append((host, 'oai_dc' if eprints else 'xoai', sp, nm))
        print(f'{host}: {len(sets)} sets, {len(chosen)} chosen')
    with (OUTDIR / 'canada-listing-sets.tsv').open('w') as f:
        f.write('host\tprefix\tset\tlabel\n')
        for r in rows:
            f.write('\t'.join(x.replace('\t', ' ') for x in r) + '\n')
    print('wrote canada-listing-sets.tsv', len(rows), '(edit by hand if a set looks wrong)')


def parse_eprints_dc(md):
    D = '{http://purl.org/dc/elements/1.1/}'
    g = lambda t: [e.text.strip() for e in md.iter(D + t) if e.text]  # noqa: E731
    return dict(title=(g('title') or [''])[0], author=(g('creator') or [''])[0], year=next((x[:4] for x in g('date')), ''),
                types=g('type'), ids=g('identifier') + g('relation'), subjects=g('subject'))


def build_from_listings():
    import xml.etree.ElementTree as ET
    titles, aha_held, held_ids, per_inst, reg = held_index()
    already_urls, already_titles = set(), set(titles)
    for name in ('canada-open-urls.records.csv', 'canada-ai-excluded-urls.records.csv'):
        p = OUTDIR / name
        if p.exists():
            for r in csv.DictReader(p.open(newline='')):
                already_urls.add(r['url'])
                if name.startswith('canada-open'):
                    already_titles.add(U.title_key(r['title']))
    for f in (ROOT / 'data/field-research/aha-repository-links-2026-11-04/wget').glob('*-urls.tsv'):
        already_urls |= {l.split('\t')[0] for l in f.read_text().splitlines() if l}
    aha_titles = {}
    for r in csv.DictReader((ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.csv').open(newline='')):
        aha_titles.setdefault(U.title_key(r['title']), r['id'])
    new_rows, nofile, per = [], [], collections.Counter()
    seen = set()
    for host, key in LIST_HOSTS.items():
        for page in sorted((LISTINGS / host).glob('records-*/page-*.xml')):
            try:
                root = ET.fromstring(page.read_text())
            except ET.ParseError:
                continue
            for rec in root.iter(U.OAI + 'record'):
                h = rec.find(U.OAI + 'header')
                if h is None or h.get('status') == 'deleted':
                    continue
                ident = h.findtext(U.OAI + 'identifier')
                md = rec.find(U.OAI + 'metadata')
                if md is None or not len(md) or ident in seen:
                    continue
                seen.add(ident)
                if host == 'archipel.uqam.ca':
                    e = parse_eprints_dc(md[0])
                    if not any(re.search(r'doctora', t, re.I) for t in e['types']):
                        continue
                    # the set is every doctoral thesis; the printed citation names the programme
                    if not any(re.search(r"doctorat en histoire(?!\s+de\s+l)", t, re.I) for t in e['ids']):
                        continue
                    title, author, year = e['title'], e['author'], e['year']
                    files = [(u, '0') for u in e['ids'] if u.lower().endswith('.pdf')]
                    embargo = ''
                else:
                    m, bits = flatten(md[0])
                    hist, doct, dept, deg = screen(m)
                    if not (hist and doct):
                        continue
                    title = (m.get('dc.title') or [''])[0]
                    author = (m.get('dc.contributor.author') or m.get('dc.creator') or [''])[0]
                    year = ((m.get('dc.date.issued') or [''])[0])[:4]
                    files = [(direct_dspace(d.get('url'), host), d.get('size') or '0') for b, d in bits
                             if b == 'ORIGINAL' and (d.get('format') or '').endswith('pdf') and d.get('url')]
                    embargo = '; '.join(v for k in m if 'embargo' in k for v in m[k])[:80]
                per[(key, 'history_phd')] += 1
                tk = U.title_key(title)
                if tk in already_titles:
                    per[(key, 'held_or_listed')] += 1
                    continue
                already_titles.add(tk)
                rid = 'oai-' + re.sub(r'[^A-Za-z0-9]+', '-', ident.split(':')[-1])
                aha = aha_titles.get(tk, '')
                if not files:
                    per[(key, 'no_public_file')] += 1
                    nofile.append(dict(university=key, record_id=rid, author=author, year=year, title=title,
                                       source=f'user-run listing {host}', status='no public PDF bitstream in listing'
                                       + (f' (embargo {embargo})' if embargo else ''), landing=ident, lac_pointer=''))
                    continue
                files.sort(key=lambda x: -int(x[1] or 0))
                url = files[0][0]
                if url in already_urls:
                    continue
                name = f"ca-{key}-{rid}{'-aha' + aha if aha else ''}-{U.slug(author.split(',')[0], 30)}-{year}.pdf"
                new_rows.append((url, name, host, '10', key, rid, title, year))
                per[(key, 'listed')] += 1
    p = OUTDIR / 'canada-ai-excluded-urls.records.csv'
    old = list(csv.reader(p.open(newline='')))[1:] if p.exists() else []
    allrows = [tuple(r) for r in old] + new_rows
    with p.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['url', 'file', 'host', 'delay', 'university', 'record_id', 'title', 'year'])
        w.writerows(allrows)
    seen_u = set()
    with (OUTDIR / 'canada-ai-excluded-urls.tsv').open('w') as f:
        for r in allrows:
            if r[0] in seen_u:
                continue
            seen_u.add(r[0])
            f.write('\t'.join(r[:4]) + '\n')
    with (OUTDIR / 'canada-listing-no-file.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['university', 'record_id', 'author', 'year', 'title', 'source', 'status', 'landing', 'lac_pointer'])
        w.writeheader()
        w.writerows(nofile)
    for k, v in sorted(per.items()):
        print(k, v)
    print('ai-excluded list now', len(seen_u), 'links;', len(new_rows), 'from listings')


def lac_queue():
    """Missing AHA records (no open link) -> canada-lac-queue.tsv for the user-run LAC lookup."""
    rows = list(csv.DictReader((OUTDIR / 'canada-missing-no-link.csv').open(newline='')))
    with (OUTDIR / 'canada-lac-queue.tsv').open('w') as f:
        for r in rows:
            if not r['record_id'].startswith('aha'):
                continue
            words = ' '.join(U.fold(r['title']).split()[:8])
            q = f"{r['author'].split(',')[0]} {words}".strip()
            f.write(f"{r['record_id']}\t{q}\n")
    print('canada-lac-queue.tsv', sum(1 for r in rows if r['record_id'].startswith('aha')))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'survey'
    {'survey': main, 'pick-sets': pick_sets, 'build-from-listings': build_from_listings, 'lac-queue': lac_queue}[cmd]()
