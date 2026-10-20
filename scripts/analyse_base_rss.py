#!/usr/bin/env python3
"""Analyse a BASE RSS harvest (scripts/harvest_base_rss.py): sources, duplicates, History-PhD
classification and overlap with the project's existing dissertation records.

Subcommands
    resolve-handles DIR [--per-prefix 1] [--top 60]
        Resolve a SAMPLE of Handle-System and DOI links (one per prefix, the most frequent
        prefixes only) through https://hdl.handle.net/api/handles/<handle> (DOIs:
        https://doi.org/api/handles/<doi>), to learn which repository
        host each prefix belongs to. One request per 1.5 s; results cached in
        DIR/handle-prefixes.json. No repository pages or PDFs are fetched.
    analyse DIR [--kind theses|books]
        Builds DIR/clusters.jsonl (one canonical record per duplicate cluster, all member
        links/ids kept), DIR/summary.json and the hand-check samples DIR/samples/*.csv.

Deduplication (BASE indexes the same work from several repositories/aggregators)
    Records are linked when they share a DOI, Handle or URN:NBN, or when they share a title key
    AND first-creator surname AND compatible year (+-1, using the harvest slice's year range).
    Title keys: casefolded, diacritics and punctuation stripped; the whole title, each
    ' ; '-separated part (HAL pairs a translated and an original title) and, as a secondary
    key, the main title before ':' (only when it keeps >= 4 words). Linking is transitive
    (union-find). The canonical member is chosen by source type: institutional repository of
    a university > national thesis portal > aggregator (CORE, Zenodo, OpenAIRE, ...), then the
    richer record.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import random
import re
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FR = ROOT / 'data/field-research'
UA = 'HistoriographyMetadataResearch/1.0 (handle prefix sample; no email)'

# ----------------------------------------------------------------- source registry
# key: host, or 'hdl:<prefix>' for Handle links, or 'doi:<prefix>' for DOI links.
# value: (repository, country, source_type) with source_type institutional|national|aggregator|publisher
SOURCES = {
    # national thesis portals / national repositories
    'theses.hal.science': ('HAL theses (TEL), France', 'France', 'national'),
    'tel.archives-ouvertes.fr': ('HAL theses (TEL), France', 'France', 'national'),
    'hal.science': ('HAL, France', 'France', 'national'),
    'shs.hal.science': ('HAL-SHS, France', 'France', 'national'),
    'halshs.archives-ouvertes.fr': ('HAL-SHS, France', 'France', 'national'),
    'hal.archives-ouvertes.fr': ('HAL, France', 'France', 'national'),
    'urn.kb.se': ('DiVA / Swedish URN:NBN (urn.kb.se)', 'Sweden', 'national'),
    'hdl:10442': ('National Archive of PhD Theses (EKT didaktorika), Greece', 'Greece', 'national'),
    'nbn-resolving.org': ('URN:NBN resolver (DNB; DE/AT/CH repositories)', 'Germany/Austria/Switzerland', 'national'),
    'nbn-resolving.de': ('URN:NBN resolver (DNB; DE/AT/CH repositories)', 'Germany/Austria/Switzerland', 'national'),
    'nardus.mpn.gov.rs': ('NaRDuS national dissertation repository, Serbia', 'Serbia', 'national'),
    'www.tesisenred.net': ('TDX Tesis Doctorals en Xarxa, Catalonia', 'Spain', 'national'),
    'hdl:10803': ('TDX Tesis Doctorals en Xarxa, Catalonia', 'Spain', 'national'),
    'theses.fr': ('theses.fr, France', 'France', 'national'),
    'dart-europe.org': ('DART-Europe', 'Europe', 'aggregator'),
    'ethos.bl.uk': ('EThOS, British Library', 'United Kingdom', 'national'),
    'hdl:10603': ('Shodhganga (INFLIBNET), India', 'India', 'national'),
    'shodhganga.inflibnet.ac.in': ('Shodhganga (INFLIBNET), India', 'India', 'national'),
    # aggregators
    'core.ac.uk': ('CORE', 'United Kingdom', 'aggregator'),
    'zenodo.org': ('Zenodo', 'International', 'aggregator'),
    'doi:10.5281': ('Zenodo', 'International', 'aggregator'),
    'explore.openaire.eu': ('OpenAIRE', 'Europe', 'aggregator'),
    'www.researchgate.net': ('ResearchGate', 'International', 'aggregator'),
    'figshare.com': ('figshare', 'International', 'aggregator'),
    'doi:10.6084': ('figshare', 'International', 'aggregator'),
    'oatd.org': ('OATD', 'International', 'aggregator'),
    'search.ndltd.org': ('NDLTD', 'International', 'aggregator'),
    'www.narcis.nl': ('NARCIS', 'Netherlands', 'aggregator'),
    'hdl:20.500.12613': ('Europeana / aggregator', 'Europe', 'aggregator'),
}
# Handle prefixes / hosts filled from the handle sample (handle-prefixes.json) or known.
KNOWN_INSTITUTIONAL = {
    'hdl:2262': ('TARA, Trinity College Dublin', 'Ireland'),
    'hdl:1959.4': ('UNSWorks, UNSW Sydney', 'Australia'),
    'doi:10.26190': ('UNSWorks, UNSW Sydney', 'Australia'),
    # prefixes whose handle servers answered 500 to the sample: identified from record content
    # (10366 records carry 'Universidad de Salamanca') or the well-known prefix assignment
    'hdl:10366': ('GREDOS, Universidad de Salamanca', 'Spain'),
    'hdl:11511': ('OpenMETU, Middle East Technical University (prefix, unverified)', 'Turkey'),
    'hdl:11858': ('SUB Goettingen eDiss/GoeScholar (prefix, unverified)', 'Germany'),
    'hdl:10902': ('UCrea, Universidad de Cantabria (prefix, unverified)', 'Spain'),
    'hdl:1822': ('RepositoriUM, Universidade do Minho (prefix, unverified)', 'Portugal'),
    'doi:10.3929': ('ETH Zurich Research Collection', 'Switzerland'),
    'hdl:20.500.11850': ('ETH Zurich Research Collection', 'Switzerland'),
    'orbilu.uni.lu': ('ORBilu, University of Luxembourg', 'Luxembourg'),
    'dspace.lu.lv': ('DSpace, University of Latvia', 'Latvia'),
    'scholarworks.montana.edu': ('ScholarWorks, Montana State University', 'United States'),
    'scholarship.richmond.edu': ('UR Scholarship Repository, University of Richmond', 'United States'),
    'www.zora.uzh.ch': ('ZORA, University of Zurich', 'Switzerland'),
    'hal.univ-lorraine.fr': ('HAL Université de Lorraine', 'France'),
}
HOST_NAMES = {
    'www.tdx.cat': ('TDX Tesis Doctorals en Xarxa, Catalonia', 'Spain', 'national'),
    'www.tara.tcd.ie': ('TARA, Trinity College Dublin', 'Ireland', 'institutional'),
    'difusion.ulb.ac.be': ('DI-fusion, Universite libre de Bruxelles', 'Belgium', 'institutional'),
    'cadmus.eui.eu': ('Cadmus, European University Institute', 'Italy', 'institutional'),
    'unsworks.unsw.edu.au': ('UNSWorks, UNSW Sydney', 'Australia', 'institutional'),
    'knowledge.uchicago.edu': ('Knowledge@UChicago, University of Chicago', 'United States', 'institutional'),
    'www.didaktorika.gr': ('National Archive of PhD Theses (EKT didaktorika), Greece', 'Greece', 'national'),
    'figshare.com': ('figshare (institutional figshare portals)', 'International', 'aggregator'),
    'hellanicus.lib.aegean.gr': ('Hellanicus, University of the Aegean', 'Greece', 'institutional'),
    'pandemos.panteion.gr': ('Pandemos, Panteion University', 'Greece', 'institutional'),
    'kuscholarworks.ku.edu': ('KU ScholarWorks, University of Kansas', 'United States', 'institutional'),
    'research-repository.st-andrews.ac.uk': ('St Andrews Research Repository', 'United Kingdom', 'institutional'),
    'www.research-collection.ethz.ch': ('ETH Zurich Research Collection', 'Switzerland', 'institutional'),
    'hammer.purdue.edu': ('Purdue University Research Repository / HAMMER', 'United States', 'institutional'),
    'vtechworks.lib.vt.edu': ('VTechWorks, Virginia Tech', 'United States', 'institutional'),
    'edit.elte.hu': ('EDIT, Eotvos Lorand University', 'Hungary', 'institutional'),
    'addi.ehu.eus': ('ADDI, University of the Basque Country', 'Spain', 'institutional'),
    'repositori.uji.es': ('Repositori UJI, Universitat Jaume I', 'Spain', 'institutional'),
    'diposit.ub.edu': ('Diposit Digital, Universitat de Barcelona', 'Spain', 'institutional'),
    'open.uct.ac.za': ('OpenUCT, University of Cape Town', 'South Africa', 'institutional'),
    'nva.sikt.no': ('NVA (Nasjonalt vitenarkiv), Norway', 'Norway', 'national'),
    'rex.libraries.wsu.edu': ('Research Exchange, Washington State University', 'United States', 'institutional'),
    'ora.ox.ac.uk': ('ORA, University of Oxford', 'United Kingdom', 'institutional'),
    'researchrepository.universityofgalway.ie': ('ARAN, University of Galway', 'Ireland', 'institutional'),
    'osf.io': ('OSF', 'International', 'aggregator'),
    'repositories.lib.utexas.edu': ('Texas ScholarWorks, UT Austin', 'United States', 'institutional'),
    'www.pedocs.de': ('peDOCS (education research)', 'Germany', 'disciplinary'),
    'www.ssoar.info': ('SSOAR, GESIS (social science open access repository)', 'Germany', 'disciplinary'),
    'utrecht-main-prod.atmire.com': ('Utrecht University Repository', 'Netherlands', 'institutional'),
}
HOST_COUNTRY = {'eu': 'Italy', 'eus': 'Spain', 'cat': 'Spain', 'edu': 'United States', 'gov': 'United States'}
TLD_COUNTRY = {'fr': 'France', 'de': 'Germany', 'se': 'Sweden', 'uk': 'United Kingdom', 'ie': 'Ireland',
               'au': 'Australia', 'nz': 'New Zealand', 'ca': 'Canada', 'nl': 'Netherlands', 'be': 'Belgium',
               'ch': 'Switzerland', 'at': 'Austria', 'it': 'Italy', 'es': 'Spain', 'pt': 'Portugal',
               'br': 'Brazil', 'gr': 'Greece', 'fi': 'Finland', 'no': 'Norway', 'dk': 'Denmark', 'pl': 'Poland',
               'cz': 'Czechia', 'sk': 'Slovakia', 'hu': 'Hungary', 'lv': 'Latvia', 'lt': 'Lithuania', 'ee': 'Estonia',
               'za': 'South Africa', 'rs': 'Serbia', 'hr': 'Croatia', 'si': 'Slovenia', 'ro': 'Romania', 'tr': 'Turkey',
               'ru': 'Russia', 'ua': 'Ukraine', 'mx': 'Mexico', 'ar': 'Argentina', 'cl': 'Chile', 'co': 'Colombia',
               'pe': 'Peru', 'jp': 'Japan', 'in': 'India', 'my': 'Malaysia', 'id': 'Indonesia', 'lu': 'Luxembourg',
               'is': 'Iceland', 'il': 'Israel', 'cn': 'China', 'tw': 'Taiwan', 'kr': 'South Korea', 'hk': 'Hong Kong',
               'sg': 'Singapore', 'ng': 'Nigeria', 'ke': 'Kenya', 'gh': 'Ghana', 'ec': 'Ecuador', 'uy': 'Uruguay',
               'cr': 'Costa Rica', 've': 'Venezuela', 'bg': 'Bulgaria', 'cy': 'Cyprus', 'mt': 'Malta'}


def folded(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', (text or '').casefold()) if not unicodedata.combining(c))


def norm(text):
    return re.sub(r'\s+', ' ', re.sub(r'[\W_]+', ' ', folded(text))).strip()


def strip_article(t):
    return re.sub(r'^(the|a|an|le|la|les|l|el|los|las|il|lo|gli|der|die|das|de|het|o|os|as) ', '', t)


def surname(name):
    name = folded(name or '').strip()
    if not name:
        return ''
    if ',' in name:
        sur = name.split(',', 1)[0]
    else:
        bits = name.split()
        sur = bits[-1] if bits else ''
    toks = [t for t in re.split(r'[\W\d_]+', sur) if t and t not in ('jr', 'sr', 'ii', 'iii', 'von', 'van', 'de', 'der', 'da', 'del', 'di', 'la', 'le')]
    return ''.join(toks)


def title_keys(title):
    """(primary keys, secondary keys) for a title."""
    title = re.sub(r'\s*\(\.\.\.\)\s*$', '', title or '')   # BASE truncation marker
    prim, sec = set(), set()
    whole = strip_article(norm(title))
    if len(whole) >= 12:
        prim.add(whole)
    for part in re.split(r'\s+;\s+|\s+=\s+|\s+/\s+', title):
        p = strip_article(norm(part))
        if len(p) >= 12:
            prim.add(p)
        main = strip_article(norm(re.split(r'\s*[:.?!]\s+', part, 1)[0]))
        if len(main.split()) >= 4 and main != p:
            sec.add(main)
    return prim, sec


def truncated(title):
    return bool(re.search(r'\(\.\.\.\)\s*$', title or ''))


ID_PATTERNS = [
    ('doi', re.compile(r'\b(10\.\d{4,9}/[^\s"<>]+)', re.I)),
    ('hdl', re.compile(r'hdl\.handle\.net/(\d[\w.]*/[^\s"<>?#]+)', re.I)),
    ('urn', re.compile(r'\b(urn:nbn:[a-z0-9:.\-]+)', re.I)),
]


def identifiers(rec):
    out = set()
    for field in (rec.get('link', ''), rec.get('guid', '')):
        for kind, rx in ID_PATTERNS:
            for m in rx.findall(field or ''):
                out.add(f'{kind}:{m.rstrip(".,;)").lower()}')
    return out


def source_key(link):
    sp = urlsplit(link or '')
    host = sp.netloc.lower()
    path = sp.path.lstrip('/')
    if host in ('hdl.handle.net', 'handle.net', 'hdl.net'):
        return 'hdl:' + path.split('/')[0]
    if host in ('doi.org', 'dx.doi.org', 'www.doi.org'):
        return 'doi:' + path.split('/')[0]
    return host


def load_handle_map(d):
    p = d / 'handle-prefixes.json'
    return json.loads(p.read_text()) if p.exists() else {}


def describe_source(key, hmap):
    if key in SOURCES:
        return SOURCES[key]
    if key in KNOWN_INSTITUTIONAL:
        name, country = KNOWN_INSTITUTIONAL[key]
        return name, country, 'institutional'
    host = key
    if key.startswith(('hdl:', 'doi:')) and key in hmap and hmap[key].get('host') not in (None, 'hdl.handle.net'):
        host = hmap[key]['host']
        if host in SOURCES:
            return SOURCES[host]
        if host in KNOWN_INSTITUTIONAL:
            return KNOWN_INSTITUTIONAL[host][0], KNOWN_INSTITUTIONAL[host][1], 'institutional'
    if host in HOST_NAMES:
        return HOST_NAMES[host]
    if host.endswith(('.hal.science', '.archives-ouvertes.fr')) and not host.startswith('hal.univ-'):
        return f'HAL, France ({host})', 'France', 'national'
    if key.startswith('doi:') and host == key:
        return key, 'unknown', 'publisher'
    if key.startswith('hdl:') and host == key:
        return key, 'unknown', 'institutional'
    tld = host.rsplit('.', 1)[-1]
    country = TLD_COUNTRY.get(tld) or HOST_COUNTRY.get(tld, 'unknown')
    kind = 'aggregator' if any(a in host for a in ('core.ac.uk', 'zenodo', 'openaire', 'researchgate', 'figshare')) else 'institutional'
    return host, country, kind


# ----------------------------------------------------------------- language
_LANG_READY = False


def detect_lang(text):
    global _LANG_READY
    try:
        from langdetect import DetectorFactory, detect_langs
    except ImportError:
        return None
    if not _LANG_READY:
        DetectorFactory.seed = 0
        _LANG_READY = True
    text = re.sub(r'\s+', ' ', text or '').strip()
    if len(text) < 8:
        return None
    try:
        best = detect_langs(text)[0]
    except Exception:
        return None
    return best.lang if best.prob >= 0.6 else None


def record_language(rec):
    """Language of the work, guessed from metadata: if a title has parts in several languages
    (a translated English title beside the original), the non-English part wins."""
    parts = [p for p in re.split(r'\s+;\s+|\s+=\s+', re.sub(r'\s*\(\.\.\.\)\s*$', '', rec['title'])) if len(p) > 15]
    langs = [detect_lang(p) for p in parts] if parts else []
    langs = [l for l in langs if l]
    non_en = [l for l in langs if l != 'en']
    if non_en:
        return Counter(non_en).most_common(1)[0][0]
    if langs:
        return langs[0]
    return detect_lang(rec['title'] + ' ' + rec.get('description', '')[:300]) or 'und'


# ----------------------------------------------------------------- History-PhD classifier
STRONG_HIST = re.compile(
    r'^\[shs\.hist\]|^(history|historia|histoire|geschichte|storia|historie|geschiedenis|historiography|'
    r'historiografia|istoria|ιστορια|история|istorija|dejiny|historia y geografia|history and archaeology|'
    r'ιστορια και αρχαιολογια|histoire et civilisations|sciences historiques|historical studies|'
    r'geschichtswissenschaft|geschichtswissenschaften|history department|department of history|'
    r'doctorat en histoire|phd in history|histoire moderne et contemporaine|histoire contemporaine|'
    r'histoire moderne|histoire medievale|histoire ancienne|alte geschichte|neuere geschichte|'
    r'zeitgeschichte|mittelalterliche geschichte|historia contemporanea|historia moderna|historia medieval|'
    r'storia contemporanea|storia moderna|storia medievale|historia antigua|ancient history|medieval history|'
    r'modern history|contemporary history)$|info:eu-repo/classification/ddc/9[0-9][0-9]|^ddc:9[0-9][0-9]|'
    r'^9[0-9][0-9]\b|^(dejepis|historiografi|historia e geografia|historiska studier|historia ja|'
    r'tortenelemtudomany\w*|bolcseszettudomanyok tortenelemtudomany\w*|istorijske znanosti|'
    r'historical sciences|history and philosophy of science)$|anzsrc[- ]for 43(03|02)|fos history and archaeology|'
    r'tortenelemtudomany|^history (and|&) (archaeology|classics|philosophy|politics|international relations)$')
SUBFIELD_HIST = re.compile(
    r'\b(economic|social|urban|cultural|political|military|intellectual|church|legal|maritime|labou?r|'
    r'women s|gender|colonial|imperial|global|world|environmental|agrarian|agricultural|business|'
    r'diplomatic|religious|local|regional|oral|public|family|medical)\s+history\b|history of (ideas|science|'
    r'medicine|technology|education|religion|art)|ekonomisk historia|ide och lardomshistoria|idehistoria|'
    r'lardomshistoria|wirtschaftsgeschichte|sozialgeschichte|kirchengeschichte|kulturgeschichte|'
    r'histoire (economique|sociale|culturelle|politique|religieuse|des sciences)|historia (economica|social|'
    r'cultural|politica)|storia (economica|sociale)|economische geschiedenis|historisk|\bgeschichte\b|'
    r'historical geography|histoire et archeologie|^\w+ (history|historia|histoire|geschichte|vesture|istorija)$|'
    r'^(history|historia|histoire|geschichte) (of|de|des|der|du|del) \w+|\bhistoria\b|\bhistoire\b|\bhistory\b|'
    r'\b(vesture|istorija|istoriya|tortenet\w*|dejiny|historie)\b|\bhistory \d+(th|st|nd|rd) century\b')
NEG = re.compile(
    r'natural history|life history|life histories|history matching|thermal history|evolutionary history|'
    r'demographic history|population history genetic|phylogen|geolog|sediment|tectonic|petroleum|reservoir|'
    r'load history|stress history|case history|clinical history|medical records|patient|paleoclimat|'
    r'glacial|holocene|pleistocene|quaternary|stratigraph|ecolog|genetic|genomic|fossil|biogeograph|'
    r'thermochronolog|exhumation|history effect|time history|loading history|burial history')
OTHER_DISC = re.compile(
    r'^\[(shs\.(art|litt|langue|archeo|phil|droit|edu|socio|eco|scipo|geo|relig|musiq|anthro|psy|gestion|'
    r'info|demo|stat|archi|envir|class)|sdv|sdu|spi|phys|chim|math|info|sde|stat)[.\]]|'
    r'^(literature|linguistics|archaeology|archeology|architecture|art history|musicology|music|theology|'
    r'philosophy|law|sociology|economics|political science|education|anthropology|psychology|geography|'
    r'religious studies|classics|classical studies|literary studies|english|german|french|spanish|'
    r'comparative literature|kunstgeschichte|histoire de l art|archeologie|litterature|linguistique|'
    r'theologie|droit|sociologie|economie|science politique|kunstwissenschaft|literaturwissenschaft|'
    r'archaologie|musikwissenschaft|theologie|philosophie|religionswissenschaft)$|'
    r'info:eu-repo/classification/ddc/[0-8][0-9][0-9]|^ddc:[0-8][0-9][0-9]')
OTHER_HIST = re.compile(
    r'\b(art|music|musical|architectural|architecture|literary|film|cinema|theatre|theater|design|dance)\s+'
    r'(history|histories)\b|histoire de l art|kunstgeschichte|musikgeschichte|storia dell arte|historia del arte|'
    r'history of (art|music|architecture|literature|cinema|film|design)|muzik tarihi|literaturgeschichte|'
    r'fos arts arts history of arts')
TITLE_HIST = re.compile(
    r'\b(1[0-9]\d\d|20[0-2]\d)\s*[-–]\s*(1[0-9]\d\d|20[0-2]\d|\d\d)\b|\b(century|centuries|siecle|siecles|'
    r'jahrhundert|jahrhunderts|siglo|secolo|sekel|eeuw|ancien regime|medieval|early modern|colonial|'
    r'antiquity|empire|imperial|revolution|interwar|wartime|histor\w*|geschicht\w*|storia|storic\w*|'
    r'archiv\w*)\b')
DESC_HIST = re.compile(r'\b(archival|archives|primary sources|historiograph\w*|historians?|archiv\w*|'
                       r'quellen|sources primaires|fuentes)\b')


def classify(rec):
    cats = [norm(c) for c in rec.get('categories', [])]
    raw_cats = [folded(c) for c in rec.get('categories', [])]
    title = norm(rec.get('title', ''))
    desc = norm(rec.get('description', ''))[:1500]
    score, why = 0, []
    lcsh_hist = any(re.search(r'--\s*history(?!\s+and\s+criticism)\b', c) for c in raw_cats)
    hist_crit = any('history and criticism' in c for c in raw_cats)
    if any(STRONG_HIST.search(c) for c in cats + raw_cats):
        score += 3; why.append('history-discipline category')
    elif any(SUBFIELD_HIST.search(c) for c in cats if not OTHER_HIST.search(c)) or lcsh_hist:
        score += 2; why.append('history-subfield category' if not lcsh_hist else 'LCSH "-- History" heading')
    if hist_crit or any(OTHER_HIST.search(c) for c in cats):
        score -= 1; why.append('art/music/literary/architectural history')
    if TITLE_HIST.search(title):
        score += 1; why.append('historical title')
    if DESC_HIST.search(desc):
        score += 1; why.append('archival/historiographical abstract')
    neg_text = ' '.join(cats) + ' ' + title + ' ' + desc[:600]
    if NEG.search(neg_text):
        score -= 3; why.append('natural/clinical science "history" sense')
    other = [c for c in raw_cats + cats if OTHER_DISC.search(c)]
    if other and not any(c.startswith('[shs.hist]') for c in raw_cats):
        score -= 1; why.append('other-discipline category')
    label = 'history' if score >= 3 else 'possible' if score >= 1 else 'other'
    return label, score, why


# ----------------------------------------------------------------- holdings
def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.startswith('['):
        try:
            import ast
            return ast.literal_eval(v)
        except Exception:
            return [v]
    return [v]


def load_holdings():
    rows = []
    paths = sorted(FR.glob('canadian-dissertations-2026-10-1*/metadata/records.jsonl')) + \
        [FR / 'canadian-dissertations-2026-10-11/laval-public/records.jsonl',
         FR / 'canadian-dissertations-2026-10-11d/records.jsonl',
         FR / 'canadian-dissertations-2026-10-12-ubc/records.jsonl']
    for p in paths:
        if p.exists():
            for line in p.open():
                r = json.loads(line)
                rows.append(('canadian', r.get('title'), as_list(r.get('authors')), as_list(r.get('handles')) + [r.get('item_url') or '']))
    for p in sorted(FR.glob('us-dissertations*/records.jsonl')):
        tier = 'us-tier2' if 'tier2' in p.parent.name else 'us-tier1'
        for line in p.open():
            r = json.loads(line)
            rows.append((tier, r.get('title'), as_list(r.get('authors')), as_list(r.get('handles')) + [r.get('item_url') or '']))
    aha = FR / 'aha-dissertations-2026-10-13/records.csv'
    with aha.open() as fh:
        for r in csv.DictReader(fh):
            rows.append(('aha', r['title'], [r['dissertator']], []))
    index, ids = defaultdict(set), defaultdict(set)
    counts = Counter()
    for src, title, authors, links in rows:
        counts[src] += 1
        sur = surname(authors[0]) if authors else ''
        prim, sec = title_keys(title or '')
        for k in prim | sec:
            index[(k, sur)].add(src)
            index[(' '.join(k.split()[:8]), sur)].add(src)
        for l in links:
            for kind, rx in ID_PATTERNS:
                for m in rx.findall(l or ''):
                    ids[f'{kind}:{m.rstrip(".,;)").lower()}'].add(src)
    return index, ids, counts


# ----------------------------------------------------------------- clustering
class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)


def years_compatible(a, b):
    if a['year_lo'] is None or b['year_lo'] is None:
        return True
    alo, ahi = a['year_lo'], a['year_hi']
    blo, bhi = b['year_lo'], b['year_hi']
    return alo - 1 <= bhi and blo - 1 <= ahi


def cluster(recs):
    uf = UF(len(recs))
    by_id, by_key = defaultdict(list), defaultdict(list)
    link_reason = Counter()
    for i, r in enumerate(recs):
        for x in r['_ids']:
            by_id[x].append(i)
        sur = r['_surname']
        if sur:
            for k in r['_prim']:
                by_key[('p', k, sur)].append(i)
            for k in r['_sec']:
                by_key[('s', k, sur)].append(i)
            if r['_truncated']:
                for k in r['_prim']:
                    by_key[('t', ' '.join(k.split()[:8]), sur)].append(i)
    for x, members in by_id.items():
        for j in members[1:]:
            if uf.find(j) != uf.find(members[0]):
                link_reason['identifier'] += 1
            uf.union(members[0], j)
    for key, members in by_key.items():
        if len(members) < 2:
            continue
        for a_i in range(len(members)):
            for b_i in range(a_i + 1, len(members)):
                a, b = members[a_i], members[b_i]
                if uf.find(a) != uf.find(b) and years_compatible(recs[a], recs[b]):
                    link_reason[{'p': 'title+surname+year', 's': 'main-title+surname+year', 't': 'truncated-title+surname+year'}[key[0]]] += 1
                    uf.union(a, b)
    # truncated BASE titles: also link a truncated title's 8-word prefix to full titles
    pref = defaultdict(list)
    for i, r in enumerate(recs):
        if r['_surname']:
            for k in r['_prim']:
                pref[(' '.join(k.split()[:8]), r['_surname'])].append(i)
    for key, members in pref.items():
        if len(members) < 2 or len(key[0].split()) < 6:
            continue
        trunc = [m for m in members if recs[m]['_truncated']]
        for t in trunc:
            for m in members:
                if m != t and uf.find(m) != uf.find(t) and years_compatible(recs[m], recs[t]):
                    link_reason['truncated-title+surname+year'] += 1
                    uf.union(m, t)
    groups = defaultdict(list)
    for i in range(len(recs)):
        groups[uf.find(i)].append(i)
    return list(groups.values()), link_reason


TYPE_RANK = {'institutional': 3, 'national': 2, 'disciplinary': 2, 'publisher': 2, 'aggregator': 1}


def canonical(members, recs):
    def key(i):
        r = recs[i]
        return (TYPE_RANK.get(r['_source_type'], 2), len(r.get('description', '')) > 0,
                not r['_truncated'], len(r.get('categories', [])), -i)
    return max(members, key=key)


# ----------------------------------------------------------------- commands
def cmd_resolve(args):
    d = Path(args.dir)
    cache_p = d / 'handle-prefixes.json'
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    recs = [json.loads(l) for l in (d / 'records.jsonl').open()]
    by_prefix = defaultdict(list)
    for r in recs:
        k = source_key(r['link'])
        if k.startswith(('hdl:', 'doi:')):
            by_prefix[k].append(r['link'])
    todo = [p for p, _ in sorted(by_prefix.items(), key=lambda kv: -len(kv[1]))[:args.top] if p not in cache]
    for p in todo:
        link = by_prefix[p][0]
        handle = urlsplit(link).path.lstrip('/')
        resolver = 'doi.org' if p.startswith('doi:') else 'hdl.handle.net'
        url = f'https://{resolver}/api/handles/{handle}'
        entry = {'sample_handle': handle, 'records': len(by_prefix[p])}
        try:
            with urlopen(Request(url, headers={'User-Agent': UA}), timeout=30) as resp:
                data = json.loads(resp.read().decode())
            urls = [v['data']['value'] for v in data.get('values', []) if v.get('type') == 'URL']
            entry['url'] = urls[0] if urls else None
            entry['host'] = urlsplit(urls[0]).netloc.lower() if urls else None
        except (HTTPError, URLError, TimeoutError, ValueError) as e:
            entry['error'] = repr(e)[:200]
        cache[p] = entry
        print(p, entry.get('host'), entry.get('records'), flush=True)
        cache_p.write_text(json.dumps(cache, indent=1, sort_keys=True))
        time.sleep(1.5)
    cache_p.write_text(json.dumps(cache, indent=1, sort_keys=True))


def slice_index(d):
    """guid -> narrowest (year_lo, year_hi) and BASE language facet value, from every harvest
    pass (state*.json + raw/<pass>/<slice>/pNNNN.xml). A record first met in a coarse slice
    (e.g. 2005-2007) usually reappears in a single-year slice of a finer pass."""
    best, langs = {}, {}
    for state_p in sorted(d.glob('state*.json')):
        pass_name = state_p.stem[len('state-'):] if state_p.stem.startswith('state-') else None
        raw = d / 'raw' / pass_name if pass_name else d / 'raw'
        slices = json.loads(state_p.read_text())['slices']
        for sid, sl in slices.items():
            if sl.get('year_lo') is None and sl.get('lang_pos') is None:
                continue
            lo = sl['year_lo'] if sl['year_lo'] not in (None, 0) else -10**6
            hi = sl['year_hi'] if sl['year_hi'] not in (None, 9999) else 10**6
            for f in sorted((raw / sid).glob('p*.xml')) if (raw / sid).is_dir() else []:
                for g in re.findall(r'<guid>([^<]*)</guid>', f.read_text()):
                    g = g.strip()
                    if sl.get('year_lo') is not None and (g not in best or hi - lo < best[g][1] - best[g][0]):
                        best[g] = (lo, hi)
                    if sl.get('lang_pos'):
                        langs[g] = sl['lang_pos']
    return best, langs


def cmd_analyse(args):
    d = Path(args.dir)
    hmap = load_handle_map(d)
    recs = [json.loads(l) for l in (d / 'records.jsonl').open()]
    best, facet_langs = slice_index(d)
    for r in recs:
        g = r['guid']
        if g in best:
            lo, hi = best[g]
            r['year_lo'] = None if lo == -10**6 else lo
            r['year_hi'] = None if hi == 10**6 else hi
            r['year'] = lo if lo == hi else None
        r['base_lang'] = facet_langs.get(g)
        r['_source'] = source_key(r['link'])
        name, country, stype = describe_source(r['_source'], hmap)
        r['_repository'], r['_country'], r['_source_type'] = name, country, stype
        r['_ids'] = identifiers(r)
        r['_surname'] = surname(r['creators'][0]) if r.get('creators') else ''
        r['_prim'], r['_sec'] = title_keys(r['title'])
        r['_truncated'] = truncated(r['title'])
    groups, reasons = cluster(recs)
    index, hold_ids, hold_counts = load_holdings()
    out_rows = []
    for members in groups:
        c = canonical(members, recs)
        cr = recs[c]
        label, score, why = classify(cr)
        # a cluster is History if any member's metadata says so
        for m in members:
            l2, s2, w2 = classify(recs[m])
            if s2 > score:
                label, score, why = l2, s2, w2
        matched = set()
        for m in members:
            r = recs[m]
            for k in r['_prim'] | r['_sec']:
                matched |= index.get((k, r['_surname']), set())
                matched |= index.get((' '.join(k.split()[:8]), r['_surname']), set())
            for x in r['_ids']:
                matched |= hold_ids.get(x, set())
        lang = record_language(cr) if args.lang else None
        out_rows.append({
            'cluster_id': cr['guid'], 'title': cr['title'], 'creators': cr['creators'],
            'description': cr.get('description', ''), 'categories': cr['categories'],
            'year': cr['year'], 'year_lo': cr['year_lo'], 'year_hi': cr['year_hi'], 'facet': cr.get('facet'),
            'repository': cr['_repository'], 'country': cr['_country'], 'source_type': cr['_source_type'],
            'source_key': cr['_source'], 'link': cr['link'], 'language': lang,
            'base_lang_facet': next((recs[m]['base_lang'] for m in members if recs[m].get('base_lang')), None),
            'history_label': label, 'history_score': score, 'history_basis': why,
            'held_in': sorted(matched), 'n_members': len(members),
            'members': [{'guid': recs[m]['guid'], 'link': recs[m]['link'], 'repository': recs[m]['_repository'],
                         'source_type': recs[m]['_source_type'], 'ids': sorted(recs[m]['_ids']),
                         'title': recs[m]['title'] if m != c else None} for m in members],
        })
    with (d / 'clusters.jsonl').open('w') as fh:
        for row in out_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + '\n')

    # ---- summary
    S = {'raw_records': len(recs), 'clusters': len(out_rows),
         'records_in_multi_member_clusters': sum(r['n_members'] for r in out_rows if r['n_members'] > 1),
         'multi_member_clusters': sum(1 for r in out_rows if r['n_members'] > 1),
         'link_reasons': dict(reasons), 'holdings_loaded': dict(hold_counts)}
    S['duplication_rate'] = round(1 - S['clusters'] / max(1, S['raw_records']), 4)
    # by source: share of records that are non-canonical duplicates
    canon_guids = {r['cluster_id'] for r in out_rows}
    multi = {m['guid'] for r in out_rows if r['n_members'] > 1 for m in r['members']}
    src = defaultdict(lambda: Counter())
    for r in recs:
        s = src[r['_repository']]
        s['records'] += 1
        s['in_multi'] += r['guid'] in multi
        s['dropped_as_duplicate'] += r['guid'] not in canon_guids
        s['type:' + r['_source_type']] = 1
    S['by_source_raw'] = sorted(({'repository': k, 'records': v['records'], 'in_multi_member_cluster': v['in_multi'],
                                  'dropped_as_duplicate': v['dropped_as_duplicate'],
                                  'dup_rate': round(v['dropped_as_duplicate'] / v['records'], 3),
                                  'source_type': next((t[5:] for t in v if t.startswith('type:')), None)}
                                 for k, v in src.items()), key=lambda x: -x['records'])
    C = lambda f: Counter(f(r) for r in out_rows)
    S['clusters_by_repository'] = C(lambda r: r['repository']).most_common()
    S['clusters_by_country'] = C(lambda r: r['country']).most_common()
    S['clusters_by_source_type'] = C(lambda r: r['source_type']).most_common()
    S['clusters_by_year_slice'] = sorted(C(lambda r: (str(r['year']) if r['year'] else f"{r['year_lo'] or 'min'}-{r['year_hi'] or 'max'}")).items())
    if args.lang:
        S['clusters_by_language'] = C(lambda r: r['language']).most_common()
    S['clusters_by_base_lang_facet'] = C(lambda r: r['base_lang_facet'] or '(not in a language slice)').most_common()
    S['clusters_by_decade'] = sorted(C(lambda r: (f"{r['year'] // 10 * 10}s" if r['year'] else
                                                 f"range {r['year_lo'] or 'min'}-{r['year_hi'] or 'max'}")).items())
    if any(r['facet'] for r in out_rows):
        S['clusters_by_facet'] = C(lambda r: r['facet']).most_common()
    S['history_label'] = C(lambda r: r['history_label']).most_common()
    S['held_in'] = C(lambda r: '+'.join(r['held_in']) or 'not held').most_common()
    newhist = [r for r in out_rows if r['history_label'] == 'history' and not r['held_in']]
    newposs = [r for r in out_rows if r['history_label'] == 'possible' and not r['held_in']]
    S['new_history_clusters'] = len(newhist)
    S['new_possible_clusters'] = len(newposs)
    S['new_history_by_repository'] = Counter(r['repository'] for r in newhist).most_common(40)
    S['new_history_by_country'] = Counter(r['country'] for r in newhist).most_common()
    S['new_history_by_language'] = Counter(r['language'] for r in newhist).most_common() if args.lang else None
    S['new_history_by_host'] = Counter(urlsplit(r['link']).netloc for r in newhist).most_common(25)
    (d / 'summary.json').write_text(json.dumps(S, indent=1, ensure_ascii=False))

    # ---- samples for hand checks
    rnd = random.Random(20261019)
    sd = d / 'samples'
    if sd.exists() and not args.resample:
        print('samples/ exists (hand-check judgements kept); use --resample to redraw', file=sys.stderr)
        sd = None
    if sd is None:
        print(json.dumps({k: S[k] for k in ('raw_records', 'clusters', 'duplication_rate', 'history_label',
                                            'new_history_clusters')}, ensure_ascii=False))
        return
    sd.mkdir(exist_ok=True)
    multi_rows = [r for r in out_rows if r['n_members'] > 1]
    with (sd / 'dedupe-sample-20.csv').open('w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['cluster_id', 'n_members', 'canonical_title', 'creators', 'member_titles', 'member_repositories', 'judgement'])
        for r in rnd.sample(multi_rows, min(20, len(multi_rows))):
            w.writerow([r['cluster_id'], r['n_members'], r['title'], '; '.join(r['creators']),
                        ' || '.join(m['title'] or '(canonical)' for m in r['members']),
                        ' || '.join(m['repository'] for m in r['members']), ''])
    pos = [r for r in out_rows if r['history_label'] == 'history']
    with (sd / 'classifier-sample-50.csv').open('w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['cluster_id', 'repository', 'title', 'categories', 'description', 'basis', 'judgement'])
        for r in rnd.sample(pos, min(50, len(pos))):
            w.writerow([r['cluster_id'], r['repository'], r['title'], ' | '.join(r['categories'][:15]),
                        r['description'][:400], '; '.join(r['history_basis']), ''])
    for lab, n in (('possible', 30), ('other', 30)):
        rows = [r for r in out_rows if r['history_label'] == lab]
        with (sd / f'classifier-sample-{lab}-{n}.csv').open('w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['cluster_id', 'repository', 'title', 'categories', 'description', 'basis', 'judgement'])
            for r in rnd.sample(rows, min(n, len(rows))):
                w.writerow([r['cluster_id'], r['repository'], r['title'], ' | '.join(r['categories'][:15]),
                            r['description'][:300], '; '.join(r['history_basis']), ''])
    print(json.dumps({k: S[k] for k in ('raw_records', 'clusters', 'duplication_rate', 'multi_member_clusters',
                                        'history_label', 'held_in', 'new_history_clusters', 'new_possible_clusters')},
                     ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('resolve-handles'); a.add_argument('dir'); a.add_argument('--top', type=int, default=60)
    b = sub.add_parser('analyse'); b.add_argument('dir'); b.add_argument('--no-lang', dest='lang', action='store_false')
    b.add_argument('--resample', action='store_true', help='redraw samples/*.csv (overwrites hand-check judgements)')
    args = ap.parse_args()
    {'resolve-handles': cmd_resolve, 'analyse': cmd_analyse}[args.cmd](args)


if __name__ == '__main__':
    main()
