"""World stage of scripts/user_run_download_lists.py (2026-11-14). Run: python3 scripts/user_run_download_lists.py world

Germany: re-reads the DNB harvest table (data/field-research/dnb-germany-harvest-2026-11-14/theses.csv.gz) and its
hosts.csv; splits class C into named-AI exclusion (user-run), challenge/disallow/403 (browser) and unreadable
robots (retry); writes a FALLBACK list of home-repository copies for DNB-list rows (same file names as the DNB
list, so whichever copy arrives first wins) and a NEW list for screened rows the DNB list does not cover.
US: resolves the handle.net and doi.org links of the AHA hybrid route through the handle/DOI proxy APIs (no
request to the repository), re-classes them by the target host's robots.txt.
Other countries: robots.txt of the main thesis repositories, classed (no listing).
"""
import collections, csv, gzip, json, re, sys, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import user_run_download_lists as U  # noqa: E402

ROOT = U.ROOT
OUT = U.OUT
DE = ROOT / 'data/field-research/dnb-germany-harvest-2026-11-14'
DE_E = Path('/mnt/e/german-theses-2026-11-14')
AHA = ROOT / 'data/field-research/aha-repository-links-2026-11-04'


def germany():
    hosts = {r['host']: r for r in csv.DictReader((DE / 'hosts.csv').open(newline=''))}

    def de_class(h):
        r = hosts.get(h)
        if not r:
            return ''
        reason = r['reason']
        if r['class'] == 'A':
            return 'open'
        if r['class'] == 'C':
            if reason == 'named AI-client exclusion':
                return 'ai-excluded'
            if 'unreadable (error' in reason or 'unreadable (503)' in reason:
                return 'retry'
            if 'unreadable (30' in reason:
                return 'redirect'
            return 'browser'
        return r['class']
    dnb_list = {l.split('\t')[1][:-4]: l.split('\t')[0] for l in (DE_E / 'dnb-copy-urls.tsv').read_text().splitlines() if l.strip()}
    got = set()
    for r in csv.DictReader((DE_E / 'manifest.csv').open(newline='')):
        if r['status'] in ('downloaded', 'skipped:held') or r['status'].startswith('ok'):
            got.add(r['dnb_id'])
    for p in DE_E.rglob('*.pdf'):
        got.add(p.stem)
    rows = list(csv.DictReader(gzip.open(DE / 'theses.csv.gz', 'rt', newline='')))
    fallback, new, counts = [], [], collections.Counter()
    for r in rows:
        if r['duplicate_of'] or r['held_id']:
            continue
        if not (r['confidence'] in ('high', 'medium') or r['screen'] == 'history'):
            continue
        h = r['host']
        cls = de_class(h)
        link = r['resolved_link'] or (r['free_links'] or '').split('|')[0].strip()
        lh = urllib.parse.urlparse(link).netloc
        if r['resolved_link'] and lh != h:
            cls = de_class(lh) or cls
            h = lh
        counts[(cls or 'no-link', r['dnb_id'] in dnb_list, r['dnb_id'] in got)] += 1
        if cls != 'ai-excluded' or r['dnb_id'] in got:
            continue
        direct = link if (r['free_link_is_pdf'] == 'yes' or link.lower().endswith('.pdf')) else ''
        delay = hosts.get(h, {}).get('crawl_delay') or '10'
        delay = str(max(10, int(float(delay))))
        if r['dnb_id'] in dnb_list:
            fallback.append((direct or link, f"{r['dnb_id']}.pdf", h, delay, 'direct' if direct else 'landing'))
        elif direct:
            new.append((direct, f"{r['dnb_id']}.pdf", h, delay, 'direct'))
        else:
            new.append((link, f"{r['dnb_id']}.pdf", h, delay, 'landing'))
    with (OUT / 'germany-ai-excluded-home-fallback.tsv').open('w') as f:
        for u, n, h, d, kind in fallback:
            if kind == 'direct':
                f.write('\t'.join([u, n, h, d]) + '\n')
    with (OUT / 'germany-ai-excluded-urls.tsv').open('w') as f:
        for u, n, h, d, kind in new:
            if kind == 'direct':
                f.write('\t'.join([u, n, h, d]) + '\n')
    with (OUT / 'germany-ai-excluded-landing-pages.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['dnb_id', 'landing', 'host', 'in_dnb_copy_list'])
        for u, n, h, d, kind in fallback + new:
            if kind == 'landing':
                w.writerow([n[:-4], u, h, n[:-4] in dnb_list])
    print('germany', dict(counts))
    print('fallback direct', sum(k == 'direct' for *_, k in fallback), 'fallback landing', sum(k == 'landing' for *_, k in fallback),
          'new direct', sum(k == 'direct' for *_, k in new), 'new landing', sum(k == 'landing' for *_, k in new))
    return counts, fallback, new


def us_resolvers():
    """handle.net / doi.org links of the AHA hybrid route -> target URL via the proxy REST APIs (the repository is
    not contacted). Returns rows (aha id, link, resolved url, target host)."""
    out = []
    seen = set()
    for f in ('matches.csv', 'oai-matches.csv', 'openalex-source-matches.csv'):
        for r in csv.DictReader((AHA / f).open(newline='')):
            u = r['pdf_url'] or r['landing_url']
            m = re.match(r'https?://(?:dx\.)?(hdl\.handle\.net|doi\.org)/(.+)', u or '')
            if not m or (r['id'], u) in seen:
                continue
            seen.add((r['id'], u))
            pid = urllib.parse.unquote(m.group(2)).split('?')[0]
            rest = ''
            if m.group(1) == 'hdl.handle.net':
                parts = pid.split('/')
                pid, rest = '/'.join(parts[:2]), '/'.join(parts[2:])
                d = U.handle_resolve(pid)
            else:
                d = U.doi_resolve(pid)
            target = U.handle_url(d)
            if target and rest:
                target = target.rstrip('/') + '/' + rest
            out.append(dict(aha_id=r['id'], department=r['department'], year=r['year'], dissertator=r['dissertator'],
                            title=r['title'], link=u, kind='pdf' if r['pdf_url'] else 'landing', resolved=target,
                            target_host=urllib.parse.urlparse(target).netloc))
    return out


DS7 = (['/server/api/core/bitstreams/00000000-0000-0000-0000-000000000000/content',
        '/bitstreams/00000000-0000-0000-0000-000000000000/download'], ['/server/oai/request'])
DS6 = (['/bitstream/handle/1/1/thesis.pdf', '/bitstream/1/1/1/thesis.pdf'], ['/oai/request'])
EPR = (['/id/eprint/1234/1/thesis.pdf', '/1234/1/thesis.pdf'], ['/cgi/oai2'])
PURE = (['/files/1234/thesis.pdf', '/ws/files/1234/thesis.pdf', '/portal/files/1234/thesis.pdf'], ['/ws/oai'])
FIG = (['/ndownloader/files/1234'], ['/v2/oai'])
HAL = (['/tel-01234567/document', '/tel-01234567v1/file/thesis.pdf'], ['/oai/hal/'])
GEN = (['/thesis.pdf'], ['/oai/request'])
BEP = (['/cgi/viewcontent.cgi?article=1&context=etd'], ['/do/oai/'])

# country, university, host, software, paths, what we know (held figure comes from dissertations.csv)
WORLD = [
    # UK
    ('GB', 'Oxford (ORA)', 'ora.ox.ac.uk', 'Hyrax/ORA', (['/objects/uuid:0000/files/x', '/objects/uuid:0000/download_file?file_format=pdf'], ['/oai/request']), 'uk:oxford'),
    ('GB', 'Cambridge (Apollo)', 'www.repository.cam.ac.uk', 'DSpace 7', DS7, 'uk:cambridge'),
    ('GB', 'Edinburgh (ERA)', 'era.ed.ac.uk', 'DSpace 7', DS7, 'uk:edinburgh'),
    ('GB', 'Glasgow (Enlighten Theses)', 'theses.gla.ac.uk', 'EPrints', EPR, 'uk:glasgow'),
    ('GB', 'St Andrews (Research Repository)', 'research-repository.st-andrews.ac.uk', 'DSpace 7', DS7, 'uk:st-andrews'),
    ('GB', 'Birmingham (eTheses)', 'etheses.bham.ac.uk', 'EPrints', EPR, 'uk:birmingham'),
    ('GB', 'Sussex (SRO)', 'sussex.figshare.com', 'Figshare', FIG, 'uk:sussex'),
    ('GB', 'White Rose eTheses (Leeds/Sheffield/York)', 'etheses.whiterose.ac.uk', 'EPrints', EPR, ''),
    ('GB', 'UCL Discovery', 'discovery.ucl.ac.uk', 'EPrints', EPR, 'uk:university-college-london'),
    ('GB', 'KCL Pure', 'kclpure.kcl.ac.uk', 'Pure', PURE, ''),
    ('GB', 'LSE Theses Online', 'etheses.lse.ac.uk', 'EPrints', EPR, ''),
    ('GB', 'Durham e-Theses', 'etheses.dur.ac.uk', 'EPrints', EPR, ''),
    ('GB', 'Warwick WRAP', 'wrap.warwick.ac.uk', 'EPrints', EPR, ''),
    ('GB', 'Manchester (Research Explorer)', 'research.manchester.ac.uk', 'Pure', PURE, 'uk:manchester'),
    ('GB', 'Exeter (ORE)', 'ore.exeter.ac.uk', 'DSpace', DS7, ''),
    ('GB', 'Nottingham eTheses', 'eprints.nottingham.ac.uk', 'EPrints', EPR, ''),
    ('GB', 'Bristol (Research Portal)', 'research-information.bris.ac.uk', 'Pure', PURE, ''),
    ('GB', 'QMUL (QMRO)', 'qmro.qmul.ac.uk', 'DSpace', DS6, ''),
    ('GB', 'SOAS Research Online', 'eprints.soas.ac.uk', 'EPrints', EPR, ''),
    ('GB', 'Kent Academic Repository', 'kar.kent.ac.uk', 'EPrints', EPR, 'uk:kent'),
    ('GB', 'Leicester (Figshare)', 'figshare.le.ac.uk', 'Figshare', FIG, 'uk:leicester'),
    ('GB', 'Royal Holloway (Pure)', 'pure.royalholloway.ac.uk', 'Pure', PURE, ''),
    ('GB', 'Birkbeck (BIROn)', 'eprints.bbk.ac.uk', 'EPrints', EPR, ''),
    ('GB', 'Aberdeen (AURA)', 'aura.abdn.ac.uk', 'DSpace', DS7, ''),
    ('GB', 'Strathclyde (STAX theses)', 'stax.strath.ac.uk', 'custom', GEN, 'uk:strathclyde'),
    ('GB', 'British Library EThOS (offline since 2023 cyber attack)', 'ethos.bl.uk', 'EThOS', GEN, ''),
    # Ireland, Netherlands
    ('IE', 'Trinity College Dublin (TARA)', 'www.tara.tcd.ie', 'DSpace', DS7, ''),
    ('IE', 'University College Dublin (Research Repository)', 'researchrepository.ucd.ie', 'DSpace 7', DS7, ''),
    ('IE', 'University College Cork (CORA)', 'cora.ucc.ie', 'DSpace 7', DS7, ''),
    ('IE', 'University of Galway (ARAN)', 'researchrepository.universityofgalway.ie', 'Esploro', GEN, ''),
    ('IE', 'Maynooth (MURAL)', 'mural.maynoothuniversity.ie', 'EPrints', EPR, ''),
    ('NL', 'Leiden (Scholarly Publications)', 'scholarlypublications.universiteitleiden.nl', 'Islandora', GEN, ''),
    ('NL', 'Utrecht (Repository)', 'dspace.library.uu.nl', 'DSpace', DS7, ''),
    ('NL', 'Amsterdam (UvA-DARE)', 'dare.uva.nl', 'Pure', PURE, ''),
    ('NL', 'Groningen (research portal)', 'research.rug.nl', 'Pure', PURE, ''),
    ('NL', 'Radboud Repository', 'repository.ubn.ru.nl', 'DSpace', DS7, ''),
    ('NL', 'Erasmus (RePub)', 'repub.eur.nl', 'custom', GEN, ''),
    # Australia, New Zealand
    ('AU', 'ANU Open Research', 'openresearch-repository.anu.edu.au', 'DSpace 7', DS7, ''),
    ('AU', 'Melbourne (Minerva Access)', 'minerva-access.unimelb.edu.au', 'Figshare', FIG, ''),
    ('AU', 'Sydney eScholarship', 'ses.library.usyd.edu.au', 'DSpace', DS6, ''),
    ('AU', 'UNSW (UNSWorks)', 'unsworks.unsw.edu.au', 'Esploro', GEN, 'base:hdl:1959.4'),
    ('AU', 'Monash (Bridges)', 'bridges.monash.edu', 'Figshare', FIG, 'base:doi:10.26180'),
    ('AU', 'Queensland (UQ eSpace)', 'espace.library.uq.edu.au', 'Fez/custom', GEN, ''),
    ('AU', 'Adelaide (Figshare)', 'adelaide.figshare.com', 'Figshare', FIG, ''),
    ('AU', 'UWA Research Repository', 'research-repository.uwa.edu.au', 'Pure', PURE, ''),
    ('AU', 'Trove (NLA; lists theses, links out)', 'trove.nla.gov.au', 'catalogue', GEN, ''),
    ('NZ', 'Auckland (ResearchSpace)', 'researchspace.auckland.ac.nz', 'DSpace', DS6, ''),
    ('NZ', 'Otago (OUR Archive)', 'ourarchive.otago.ac.nz', 'Esploro', GEN, ''),
    ('NZ', 'Victoria Wellington (Open Access)', 'openaccess.wgtn.ac.nz', 'Figshare', FIG, ''),
    ('NZ', 'Canterbury (UC Research Repository)', 'ir.canterbury.ac.nz', 'DSpace', DS7, ''),
    # France, Brazil, Mexico, others
    ('FR', 'HAL theses (TEL)', 'theses.hal.science', 'HAL', HAL, 'base:theses.hal.science'),
    ('FR', 'theses.fr (ABES; ESR-restricted files stay out)', 'theses.fr', 'theses.fr', GEN, ''),
    ('BR', 'USP Teses', 'www.teses.usp.br', 'custom', GEN, 'br:usp'),
    ('BR', 'CAPES Catálogo de Teses', 'catalogodeteses.capes.gov.br', 'CAPES', GEN, ''),
    ('BR', 'BDTD (IBICT)', 'bdtd.ibict.br', 'VuFind', GEN, ''),
    ('MX', 'UNAM TESIUNAM', 'tesiunam.dgb.unam.mx', 'Aleph/custom', GEN, 'mx:unam'),
    ('MX', 'Colmex (captcha: stays out)', 'repositorio.colmex.mx', 'custom', GEN, ''),
    ('ZA', 'UCT OpenUCT', 'open.uct.ac.za', 'DSpace 7', DS7, ''),
    ('ZA', 'Wits WIReDSpace', 'wiredspace.wits.ac.za', 'DSpace 7', DS7, ''),
    ('ZA', 'Stellenbosch SUNScholar', 'scholar.sun.ac.za', 'DSpace 7', DS7, ''),
    ('ZA', 'UNISA (UnisaIR)', 'uir.unisa.ac.za', 'DSpace 7', DS7, 'base:hdl:10500'),
    ('ZA', 'Pretoria (UPSpace)', 'repository.up.ac.za', 'DSpace 7', DS7, ''),
    ('IN', 'Shodhganga (INFLIBNET)', 'shodhganga.inflibnet.ac.in', 'DSpace', DS6, ''),
    ('HK', 'HKU Scholars Hub', 'hub.hku.hk', 'DSpace', DS6, ''),
    ('HK', 'CUHK Digital Repository', 'repository.lib.cuhk.edu.hk', 'Islandora', GEN, ''),
    # US hosts of the AHA route not yet classed in aha .../wget/hosts.csv (landing-only hosts)
    ('US', 'UNC Carolina Digital Repository', 'cdr.lib.unc.edu', 'Hyrax', (['/downloads/abc123'], ['/oai']), 'unc'),
    ('US', 'Virginia LibraETD', 'libraetd.lib.virginia.edu', 'custom', GEN, 'virginia'),
    ('US', 'Notre Dame CurateND', 'curate.nd.edu', 'Hyrax', GEN, ''),
    ('US', 'Northwestern Arch', 'arch.library.northwestern.edu', 'Hyrax', GEN, ''),
    ('US', 'Brown Digital Repository', 'repository.library.brown.edu', 'custom', GEN, ''),
    ('US', 'USC Digital Library', 'digitallibrary.usc.edu', 'custom', GEN, ''),
    ('US', 'William & Mary ScholarWorks', 'scholarworks.wm.edu', 'bepress', BEP, ''),
    ('US', 'Delaware UDSpace', 'udspace.udel.edu', 'DSpace 7', DS7, ''),
    ('US', 'WashU', 'repository.library.washu.edu', 'custom', GEN, ''),
    ('US', 'George Mason (TIND)', 'gmu.tind.io', 'TIND', GEN, ''),
    ('US', 'UMass ScholarWorks', 'scholarworks.umass.edu', 'bepress', BEP, ''),
    ('US', 'Carnegie Mellon KiltHub', 'kilthub.cmu.edu', 'Figshare', FIG, ''),
    ('US', 'UNLV Digital Scholarship', 'digitalscholarship.unlv.edu', 'bepress', BEP, ''),
    ('US', 'UNT Digital Library', 'digital.library.unt.edu', 'custom', GEN, ''),
    ('US', 'Princeton DataSpace', 'dataspace.princeton.edu', 'DSpace', DS6, ''),
    ('US', 'Yale EliScholar', 'elischolar.library.yale.edu', 'bepress', BEP, 'yale'),
    ('US', 'Harvard DASH', 'dash.harvard.edu', 'DSpace 7', DS7, 'harvard'),
    ('US', 'Chicago Knowledge', 'knowledge.uchicago.edu', 'custom', GEN, 'uchicago'),
    ('US', 'Wisconsin MINDS', 'minds.wisconsin.edu', 'DSpace', DS6, 'wisconsinmadison'),
    ('US', 'NYU (none: ProQuest only)', 'archive.nyu.edu', 'DSpace', DS6, ''),
    ('US', 'Georgetown DigitalGeorgetown', 'repository.library.georgetown.edu', 'DSpace', DS6, ''),
    ('US', 'Emory ETD', 'etd.library.emory.edu', 'custom', GEN, ''),
    ('US', 'Indiana IUScholarWorks', 'scholarworks.iu.edu', 'DSpace 7', DS7, ''),
    ('US', 'Michigan State', 'd.lib.msu.edu', 'Islandora', GEN, ''),
    ('US', 'Ohio State / OhioLINK', 'etd.ohiolink.edu', 'custom', GEN, ''),
    ('US', 'Stanford SearchWorks/SDR', 'purl.stanford.edu', 'SDR', GEN, 'stanford'),
    ('US', 'Johns Hopkins JScholarship', 'jscholarship.library.jhu.edu', 'DSpace 7', DS7, 'johnshopkins'),
    ('US', 'Penn State ETDA', 'etda.libraries.psu.edu', 'custom', GEN, ''),
    ('US', 'Boston College', 'dlib.bc.edu', 'custom', GEN, ''),
    ('US', 'Rochester UR Research', 'urresearch.rochester.edu', 'custom', GEN, ''),
    ('US', 'Minnesota Conservancy', 'conservancy.umn.edu', 'DSpace 7', DS7, 'minnesota'),
    ('US', 'Washington ResearchWorks', 'digital.lib.washington.edu', 'DSpace 7', DS7, 'washington'),
    ('US', 'Maryland DRUM', 'drum.lib.umd.edu', 'DSpace 7', DS7, 'maryland'),
    ('US', 'Florida (UFDC)', 'ufdc.ufl.edu', 'SobekCM', GEN, 'florida'),
    ('US', 'Vanderbilt IR', 'ir.vanderbilt.edu', 'DSpace 7', DS7, 'vanderbilt'),
    ('US', 'Duke DukeSpace', 'dukespace.lib.duke.edu', 'DSpace 7', DS7, 'duke'),
]


def world_hosts():
    import collections as C
    held = C.Counter()
    with (ROOT / 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            held[r['institution']] += 1
    rows = []
    for cc, uni, host, sw, (fp, oai), heldkey in WORLD:
        c = U.classify(host, fp, oai)
        rows.append(dict(country=cc, university=uni, host=host, software=sw, robots_class=c['cls'], robots_rule=c['rule'][:300],
                         robots_url=c['robots_url'], robots_status=c['robots_status'], checked=c['checked'],
                         crawl_delay=c['crawl_delay'], oai_path=c['oai_path'], oai_allowed_star=c['oai_allowed_star'],
                         oai_allowed_ai=c['oai_allowed_ai'], ai_clients_named=c['ai_excluded'][:300],
                         purpose_comments=c['purpose_comments'][:400], contacts_in_robots=c['contacts'],
                         held_in_graph=held.get(heldkey, '') if heldkey else ''))
        print(f"{cc} {host:45s} {c['cls']:12s} {c['rule'][:80]}", flush=True)
    return rows


OVERRIDE = {
    'd.lib.msu.edu': ('browser', 'no robots.txt, but the site answered scripts with a bot challenge (2026-11-05)'),
    'repositorio.colmex.mx': ('unavailable', 'captcha on files (2026-11-04): stays out'),
    'ethos.bl.uk': ('unavailable', 'EThOS offline since the British Library cyber attack (Oct 2023)'),
    'theses.fr': ('open', 'catalogue only; ESR-restricted files stay out'),
    'ora.ox.ac.uk': ('open', "'*' may fetch /objects/<uuid>/files/<id>; /*?f* (download_file?file_format=…) is disallowed: use the files path"),
    'trove.nla.gov.au': ('open', 'catalogue: lists theses and links out to the university repository'),
    'arch.library.northwestern.edu': ('browser', '401/403 to scripts (2026-11-04)'),
}
VERDICT = {'open': '1 script (open)', 'ai-excluded': '2 user-run list', 'browser': '3 browser only',
           'unavailable': '4 not available', 'retry': 'retry (timed out, not refused)', 'redirect': 'old address (see target)'}


def all_hosts():
    rows = []
    ca = OUT / 'canada-hosts.csv'
    if ca.exists():
        for r in csv.DictReader(ca.open(newline='')):
            rows.append(dict(country='CA', university=r['university'], host=r['host'], software=r['software'],
                             robots_class=r['robots_class'], robots_rule=r['robots_rule'], checked=r['checked'],
                             crawl_delay=r['crawl_delay'], oai_allowed_star=r['oai_allowed_star'],
                             oai_allowed_ai=r['oai_allowed_ai'], purpose_comments=r['purpose_comments'],
                             history_selection=r['history_selection'], held='see canada-summary.csv',
                             links_known='see canada-summary.csv', sanctioned_bulk=r['sanctioned_bulk'], ask_route=r['ask_route']))
    for r in json.loads(Path('/mnt/e/user-run-downloads-2026-11-14/world-hosts.json').read_text()):
        cls, rule = r['robots_class'], r['robots_rule']
        if r['host'] in OVERRIDE:
            cls, note = OVERRIDE[r['host']]
            rule = note + ' | robots: ' + rule
        rows.append(dict(country=r['country'], university=r['university'], host=r['host'], software=r['software'],
                         robots_class=cls, robots_rule=rule, checked=r['checked'], crawl_delay=r['crawl_delay'],
                         oai_allowed_star=r['oai_allowed_star'], oai_allowed_ai=r['oai_allowed_ai'],
                         purpose_comments=r['purpose_comments'], history_selection='needs a metadata harvest (set/department not checked)',
                         held=r['held_in_graph'], links_known='', sanctioned_bulk='', ask_route=r['contacts_in_robots']))
    for r in csv.DictReader((AHA / 'wget/hosts.csv').open(newline='')):
        rows.append(dict(country='US', university='(AHA hybrid route host)', host=r['host'], software='', robots_class=r['class'],
                         robots_rule=r['note'] or 'see aha wget hosts.csv', checked='2026-11-14', crawl_delay=r['crawl_delay'],
                         oai_allowed_star='', oai_allowed_ai='', purpose_comments='', history_selection='AHA directory (History dept)',
                         held='', links_known=r['direct_links'], sanctioned_bulk='', ask_route=''))
    for r in csv.DictReader((DE / 'hosts.csv').open(newline='')):
        reason = r['reason']
        cls = {'A': 'open', 'resolver': 'resolver', 'redirect': 'redirect'}.get(r['class'])
        if r['class'] == 'C':
            cls = ('ai-excluded' if reason == 'named AI-client exclusion' else
                   'retry' if ('unreadable (error' in reason or '(503)' in reason) else
                   'redirect' if 'unreadable (30' in reason else 'browser')
        rows.append(dict(country='DE', university='', host=r['host'], software='', robots_class=cls,
                         robots_rule=(reason + ' | ' + r['rule_text'][:200]).strip(' |'), checked=r['checked'][:10],
                         crawl_delay=r['crawl_delay'], oai_allowed_star='', oai_allowed_ai='', purpose_comments='',
                         history_selection='DNB subject groups (theses.csv.gz confidence/screen)', held='',
                         links_known=r['links'], sanctioned_bulk='DNB free online theses set https://data.dnb.de/FreieOnlineHochschulschriften' if cls in ('browser', 'retry') else '',
                         ask_route=''))
    for r in rows:
        r['verdict'] = VERDICT.get(r['robots_class'], r['robots_class'])
    with (OUT / 'hosts.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print('hosts.csv', len(rows), collections.Counter((r['country'], r['robots_class']) for r in rows))
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    germany()
    rs = us_resolvers()
    with (OUT / 'us-resolver-links.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0]))
        w.writeheader()
        w.writerows(rs)
    print('us resolver links', len(rs), collections.Counter(r['target_host'] for r in rs).most_common(40))
    # re-class resolved targets; file links (resolved PDF links) on open / ai-excluded hosts become list rows
    known = {r['host']: r['class'] for r in csv.DictReader((AHA / 'wget/hosts.csv').open(newline=''))}
    known.update({'repositories.lib.utexas.edu': 'browser', 'www.ideals.illinois.edu': 'browser', 'deepblue.lib.umich.edu': 'browser',
                  'scholarshare.temple.edu': 'browser', 'rucore.libraries.rutgers.edu': 'browser'})
    already = set()
    for f in (AHA / 'wget').glob('*-urls.tsv'):
        already |= {l.split('\t')[0] for l in f.read_text().splitlines() if l}
    held_dir = Path('/mnt/e/historiography-dissertation-pdfs/aha-wget-2026-11-14')
    have = {p.name for p in held_dir.glob('*.pdf')} if held_dir.exists() else set()
    lists = collections.defaultdict(list)
    recl = collections.Counter()
    for r in rs:
        h = r['target_host']
        if not h:
            recl[('unresolved', r['kind'])] += 1
            continue
        if h not in known:
            c = U.classify(h, [urllib.parse.urlparse(r['resolved']).path or '/'], ['/oai/request'])
            known[h] = c['cls']
        cls = known[h]
        recl[(cls, r['kind'])] += 1
        is_file = re.search(r'(\.pdf$|/bitstream/|/bitstreams/|/download|/content$|viewcontent\.cgi)', r['resolved'], re.I)
        if is_file and cls in ('open', 'ai-excluded') and r['resolved'] not in already:
            name = f"aha{r['aha_id']}-{U.slug(r['dissertator'].split(',')[0], 30)}-{r['year']}.pdf"
            if name not in have:
                lists[cls].append((r['resolved'], name, h, '10'))
    for cls in ('open', 'ai-excluded'):
        items = lists.get(cls, [])
        with (OUT / f'us-{cls}-urls.tsv').open('w') as f:
            for it in dict.fromkeys(items):
                f.write('\t'.join(it) + '\n')
    print('us re-class', dict(recl), {k: len(v) for k, v in lists.items()})
    all_hosts()


if __name__ == '__main__':
    main()
