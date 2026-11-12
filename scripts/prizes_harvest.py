"""Prize lists in history -> one table of prize facts (2026-11-12). Harvest only; linking is scripts/prizes_link.py.

Why (owner, 2026-11-12): a prize is an importance signal that does not depend on output volume or on an ORCID
(Brittany Luby's *Dammed*: CHA best book and three other prizes, seven citing theses, no graph node). A prize is a
fact about a work or a person; winners are never called "historians" here.

Sources, in the owner's priority:
  cha        the CHA prize table the atlas built on 2026-10-12 (data/extension-2026/canadian-historiography-groups-
             request-2026-10-12/answers/cha-prize-works.csv, 543 rows) with the winner pages re-read from
             cha-shc.ca, so that multi-winner pages (the Clio Prizes list a whole year's regions on one page) give
             one row per winner and title, and the citation's publisher is kept;
  wikidata   QLever (https://qlever.dev/api/wikidata): every award received (P166, with point in time P585 and for
             work P1686) by a human whose occupation is historian or a subclass of it, or who is a `wd:` anchor on a
             person key; every award received by a written work whose author is such a person or whose award is a
             history prize; and the winners (P166 reverse, P1346) of award items that are history prizes (main
             subject or field of work history, or a history word in the label). QIDs carried; the winner's LC, ORCID,
             GND, VIAF, ISNI and IdRef ids and the work's LCCN, ISBN and DOI ride along for exact links;
  web        the awarding bodies' own public pages (parsers in prizes_web_us.py, prizes_web_uk_ca_intl.py and
             prizes_web_fr_de_br_mx.py, one function per body), politely
             (scripts/prizes_fetch.py: robots.txt, 1.2 s per host, refusals recorded and never worked around).

Output: build/prizes-2026-11-12/rows-<source>.jsonl (raw rows); `assemble` writes the tracked
data/graph/prizes/prizes.csv.gz and a harvest section in data/graph/prizes/report.json.

    python3 scripts/prizes_harvest.py cha
    python3 scripts/prizes_harvest.py wikidata
    python3 scripts/prizes_harvest.py web [--only web-us,web-uk-ca-intl,web-fr-de-br-mx]
    python3 scripts/prizes_harvest.py assemble
"""
import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from prizes_fetch import BUILD, fetch, text_of, log  # noqa: E402

OUTDIR = ROOT / 'data/graph/prizes'
CHA_CSV = ROOT / 'data/extension-2026/canadian-historiography-groups-request-2026-10-12/answers/cha-prize-works.csv'
QLEVER = 'https://qlever.dev/api/wikidata'
COLS = ['prize_id', 'prize', 'body', 'body_country', 'field', 'honours', 'year', 'winner', 'co_winners', 'work_title',
        'publisher', 'wd_prize', 'wd_person', 'wd_work', 'person_ids', 'work_ids', 'source_url', 'source_kind', 'note']


def fold(t):
    t = unicodedata.normalize('NFKD', t or '')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', ''.join(c for c in t if not unicodedata.combining(c)).lower())).strip()


def prize_id(body, prize):
    return 'prize:' + re.sub(r'[^a-z0-9]+', '-', fold(body)[:30] + ' ' + fold(prize)[:60]).strip('-')


def write_rows(name, rows):
    BUILD.mkdir(parents=True, exist_ok=True)
    with (BUILD / f'rows-{name}.jsonl').open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps({c: r.get(c, '') for c in COLS}, ensure_ascii=False) + '\n')
    print(name, len(rows), 'rows', flush=True)


# ---------------------------------------------------------------- CHA

CHA_HONOURS = [(r'(?i)article|neatby|bullen|journal prize|sutherland|chapter', 'article'),
               (r'(?i)bullen', 'dissertation'), (r'(?i)teaching|public history|oral history|jubilee|media and communication',
                                                    'other'),
               (r'(?i)undergraduate', 'other'), (r'(?i)book|livre|garneau|clio|corey|ferguson|forsey', 'book')]


def cha_honours(prize):
    if re.search(r'(?i)bullen', prize):
        return 'dissertation'             # the John Bullen Prize: best History PhD thesis by a Canadian
    if re.search(r'(?i)forsey prize$|eugene a\. forsey', prize) and 'Undergraduate' not in prize:
        return 'dissertation'             # the Eugene A. Forsey Prize (graduate thesis in labour history)
    for rx, h in CHA_HONOURS:
        if re.search(rx, prize):
            return h
    return 'other'


def split_names(s):
    s = re.sub(r'\s+', ' ', s or '').strip()
    parts = re.split(r'\s*(?:,|&|\band\b|\bet\b|/)\s*', s)
    out = []
    for p in parts:
        p = p.strip(' .')
        if not p:
            continue
        if out and (re.fullmatch(r'(?:Jr|Sr|II|III)\.?', p) or len(p.split()) == 1 and len(out[-1].split()) == 1):
            out[-1] = out[-1] + ', ' + p
            continue
        out.append(p)
    return out


PUB = (r'(?:Press|Presses|Books|Éditions|Editions|Septentrion|Boréal|Publishing|Publishers|Verlag|Fides|Hurtubise|'
       r'Seuil|Gallimard|Knopf|Routledge|Palgrave|Brill|Wiley|Norton|Penguin|Lorimer|Between the Lines|Fernwood|'
       r'University(?! of [A-Z][a-z]+\)$)|Universit[ée])')


def cha_citation(text, name, others=()):
    """The citation line of one winner on a CHA page -> (title, publisher, line). CHA lines read 'Name . Title',
    'Name , Title (University).', 'A and B , Title', 'Name. Title. Place: Publisher, Year.' (Clio regions) or
    'Name, “Article,” Journal 46 (2000).' The line must name the winner within its first 120 characters and must not
    be jury prose."""
    words = name.split()
    if not words:
        return '', '', ''
    fam = words[-1]
    for line in text.split('\n'):
        if len(line) > 700 or len(line) < len(name) + 4:
            continue
        pos = line.find(fam)
        if pos < 0 or pos > 120 or words[0][:2] not in line[:pos + 1]:
            continue
        if re.match(r'(?i)^(the |this |ce |cette |prof|dr\.? |le comit|the committee|in |her |his |a |an )', line):
            continue
        rest = line[pos + len(fam):]
        # skip the co-winners printed with this one ('Irving Abella and Harold Troper , ...'), by their printed names only
        others = sorted(others or (), key=len, reverse=True)
        while True:
            m0 = re.match(r'^\s*(?:,|and|&|et)\s+', rest)
            nxt = m0 and next((o for o in others if rest[m0.end():].startswith(o)), None)
            if not nxt:
                break
            rest = rest[m0.end() + len(nxt):]
        m = re.match(r'^\s*(?:\((?:eds?\.?|dir\.?)\))?\s*(?:,\s*(?:eds?\.?|editors?)\s*)?(\s[,.]\s|[,.]\s)', rest)
        if not m:
            continue
        rest = rest[m.end():].strip()
        if not rest or re.match(r'(?i)^(the committee|this |ce |cette |professor|prof\.|who |whose |for |pour )', rest):
            continue
        pub = ''
        mp = re.search(r'(?:[.,]\s+|\(\s*)(?:[A-Z][\w .’\'-]{1,30}:\s*)?([A-Z][^.,:()]{0,60}?' + PUB + r'[^.,:()]{0,40})', rest)
        if mp:
            pub = mp.group(1).strip()
        q = re.match(r'^[“"«‘]\s*(.+?)\s*[,.]?\s*[”"»’](?=\s|$|[,.;:])', rest)
        if q:
            title = q.group(1)
        else:
            title = re.split(r'\s\.\s|\s\.$|\s\(|\.\s+(?:[A-Z][\w .’\'-]{1,30}:\s)|,\s+(?:[A-Z][\w .’\'-]{1,30}:\s)|'
                             r'[.,]\s+(?=[A-Z][^.,:]{0,60}?' + PUB + r')|\.\s+(?:19|20)\d\d', rest)[0]
            title = re.sub(r'\s*[.,;]\s*$', '', title)
        title = title.strip(' “”"«»‘’.,')
        if len(title) < 4 or len(title) > 300:
            continue
        return title, pub, line
    return '', '', ''


def cha(args):
    rows_in = list(csv.DictReader(CHA_CSV.open(encoding='utf-8')))
    out = []
    for r in rows_in:
        url = r['url']
        names = split_names(r['winner'])
        page = fetch(url) if url and not args.no_fetch else None
        text = text_of(page) if page else ''
        y = r['year']
        honours = cha_honours(r['prize'])
        multi = len(names) > 1
        for nm in [x for x in names if len(x) > 3 and x[:1].isupper()] or ['']:
            title, pub, line = (cha_citation(text, nm, [x for x in names if x != nm]) if text and nm else ('', '', ''))
            if not title and not multi:
                title = r['title']
            note = 'title from the 2026-10-12 table' if title and title == r['title'] and not multi else ''
            co = [x for x in names if x != nm]
            # a page that lists several winners of one prize-year for different works (Clio regions, honourable
            # mentions) is several rows; co-winners of one work are marked co_winners only when the citation is shared
            out.append(dict(prize=r['prize'], body='Canadian Historical Association', body_country='CA',
                            field=r['field'], honours=honours, year=y, winner=nm,
                            co_winners='; '.join(x for x in co if line and x.split()[-1] in line[:200]) if multi else '',
                            work_title=title, publisher=pub, source_url=url, source_kind='awarding-body',
                            note=(note + ('; one of several winners listed on the page' if multi else '')).strip('; ')))
    for r in out:
        r['prize_id'] = prize_id(r['body'], r['prize'])
    write_rows('cha', out)


# ---------------------------------------------------------------- Wikidata (QLever)

PFX = ('PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> '
       'PREFIX p: <http://www.wikidata.org/prop/> PREFIX ps: <http://www.wikidata.org/prop/statement/> '
       'PREFIX pq: <http://www.wikidata.org/prop/qualifier/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ')


def sparql(q, name):
    path = BUILD / 'wikidata' / f'{name}.tsv'
    if path.exists():
        return parse_tsv(path.read_text(encoding='utf-8'))
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(QLEVER, data=urllib.parse.urlencode({'query': PFX + q}).encode(),
                                 headers={'Accept': 'text/tab-separated-values', 'User-Agent': 'historiography-kg-research/0.1'})
    for attempt in range(6):
        try:
            t = urllib.request.urlopen(req, timeout=900).read().decode('utf-8')
            break
        except Exception as e:      # 429: QLever's rate limit; wait (Retry-After when given) and ask again
            ra = getattr(e, 'headers', None) and e.headers.get('Retry-After')
            wait = int(ra) if ra and ra.isdigit() else 60 * (attempt + 1)
            print('qlever retry', name, e, 'wait', wait, flush=True)
            time.sleep(wait)
    else:
        raise SystemExit('QLever failed: ' + name)
    path.write_text(t, encoding='utf-8')
    log(url=QLEVER, query=name, rows=t.count('\n') - 1)
    time.sleep(5)
    return parse_tsv(t)


def val(x):
    x = x.strip()
    if x.startswith('<http://www.wikidata.org/entity/'):
        return x[32:-1]
    m = re.match(r'^"(.*)"(?:@[\w-]+|\^\^<[^>]+>)?$', x, re.S)
    if m:
        return m.group(1).replace('\\"', '"').replace('\\t', ' ').replace('\\n', ' ')
    return x


def parse_tsv(t):
    lines = t.rstrip('\n').split('\n')
    head = [h.lstrip('?') for h in lines[0].split('\t')]
    return [dict(zip(head, (val(v) for v in ln.split('\t')))) for ln in lines[1:] if ln]


HIST_WORDS = (r'(?i)\b(histor\w*|histoire|historia|historiograph\w*|geschicht\w*|histórico|história|storia|storico|'
              r'historique|historien\w*|historiker\w*|historisch\w*)\b')


def wikidata(args):
    hist = 'wd:Q201788'
    # 1. awards of people with occupation historian (or a subclass)
    a1 = sparql(f"""SELECT ?h ?a ?t ?w WHERE {{ ?h wdt:P106/wdt:P279* {hist} . ?h p:P166 ?st . ?st ps:P166 ?a .
                   OPTIONAL {{ ?st pq:P585 ?t }} OPTIONAL {{ ?st pq:P1686 ?w }} }}""", 'q1-historian-awards')
    # 2. awards of every person key's wd: anchor (people of other fields the graph holds)
    import duckdb
    db = duckdb.connect()
    db.execute("SET memory_limit='2GB'; SET threads=2")
    G = Path(args.graph)
    qids = sorted({a[3:] for (a,) in db.execute(f"""SELECT a FROM (SELECT unnest(anchors) a FROM '{G}/person.parquet')
                                                  WHERE a LIKE 'wd:Q%'""").fetchall()})
    a2 = []
    for i in range(0, len(qids), 4000):
        vs = ' '.join('wd:' + q for q in qids[i:i + 4000])
        a2 += sparql(f"""SELECT ?h ?a ?t ?w WHERE {{ VALUES ?h {{ {vs} }} ?h p:P166 ?st . ?st ps:P166 ?a .
                       OPTIONAL {{ ?st pq:P585 ?t }} OPTIONAL {{ ?st pq:P1686 ?w }} }}""", f'q2-keyed-awards-{i // 4000:02d}')
    # 3. history prizes: award items whose subject / field is history, or with a history word in their label
    a3 = sparql(f"""SELECT DISTINCT ?a WHERE {{ ?a wdt:P31/wdt:P279* wd:Q618779 .
                   {{ ?a wdt:P921 wd:Q309 }} UNION {{ ?a wdt:P101 wd:Q309 }} UNION {{ ?a wdt:P921/wdt:P279 wd:Q309 }}
                   UNION {{ ?a wdt:P101/wdt:P279 wd:Q309 }} }}""", 'q3a-history-prizes-by-subject')
    a3b = sparql(f"""SELECT DISTINCT ?a ?l WHERE {{ ?a wdt:P31/wdt:P279* wd:Q618779 . ?a rdfs:label ?l .
                    FILTER(regex(str(?l), "(?i)(histor|geschicht|storia|histórico|história)")) }}""", 'q3b-history-prizes-by-label')
    hp = {r['a'] for r in a3} | {r['a'] for r in a3b if re.search(HIST_WORDS, r['l']) and not re.search(
        r'(?i)natural history|naturhistor|art history award for', r['l'])}
    hp_list = sorted(hp)
    # winners of the history prizes (any kind of recipient) by P166 and by P1346
    a4, a5 = [], []
    for i in range(0, len(hp_list), 2000):
        vs = ' '.join('wd:' + q for q in hp_list[i:i + 2000])
        a4 += sparql(f"""SELECT ?h ?a ?t ?w WHERE {{ VALUES ?a {{ {vs} }} ?h p:P166 ?st . ?st ps:P166 ?a .
                       OPTIONAL {{ ?st pq:P585 ?t }} OPTIONAL {{ ?st pq:P1686 ?w }} }}""", f'q4-history-prize-recipients-{i // 2000:02d}')
        a5 += sparql(f"""SELECT ?h ?a ?t ?w WHERE {{ VALUES ?a {{ {vs} }} ?a p:P1346 ?st . ?st ps:P1346 ?h .
                       OPTIONAL {{ ?st pq:P585 ?t }} OPTIONAL {{ ?st pq:P1686 ?w }} }}""", f'q5-history-prize-winners-{i // 2000:02d}')
    # 6. awards received by written works whose author is a historian
    a6 = sparql(f"""SELECT ?h ?a ?t ?w WHERE {{ ?w wdt:P50 ?au . ?au wdt:P106/wdt:P279* {hist} . ?w p:P166 ?st .
                   ?st ps:P166 ?a . OPTIONAL {{ ?st pq:P585 ?t }} BIND(?au AS ?h) }}""", 'q6-works-of-historians-awards')
    stmts = []
    for src, rows in (('historian', a1), ('keyed', a2), ('history-prize', a4), ('history-prize-p1346', a5),
                      ('work-of-historian', a6)):
        for r in rows:
            stmts.append(dict(h=r.get('h', ''), a=r['a'], t=r.get('t', ''), w=r.get('w', ''), via=src))
    # recipients that are works (a written work receiving a history prize): they are the work, the author comes from P50
    recips = sorted({s['h'] for s in stmts if s['h'].startswith('Q')})
    works = sorted({s['w'] for s in stmts if s['w'].startswith('Q')})
    awards = sorted({s['a'] for s in stmts if s['a'].startswith('Q')})
    meta = {}

    def batch(ids, qtpl, name, size=3000):
        out = []
        for i in range(0, len(ids), size):
            vs = ' '.join('wd:' + q for q in ids[i:i + size])
            out += sparql(qtpl.replace('VALS', vs), f'{name}-{i // size:03d}')
        return out

    LAB = """OPTIONAL {{ ?x rdfs:label ?en FILTER(lang(?en)='en') }} OPTIONAL {{ ?x rdfs:label ?mul FILTER(lang(?mul)='mul') }}
             OPTIONAL {{ ?x rdfs:label ?fr FILTER(lang(?fr)='fr') }} OPTIONAL {{ ?x rdfs:label ?de FILTER(lang(?de)='de') }}
             OPTIONAL {{ ?x rdfs:label ?es FILTER(lang(?es)='es') }} OPTIONAL {{ ?x rdfs:label ?pt FILTER(lang(?pt)='pt') }}"""
    LAB = LAB.replace('{{', '{').replace('}}', '}')
    rx = batch(recips, f"""SELECT ?x ?en ?mul ?fr ?de ?es ?pt (SAMPLE(?c) AS ?cls) (SAMPLE(?lc) AS ?lcnaf)
        (SAMPLE(?or) AS ?orcid) (SAMPLE(?gn) AS ?gnd) (SAMPLE(?vi) AS ?viaf) (SAMPLE(?is) AS ?isni) (SAMPLE(?ir) AS ?idref)
        (SAMPLE(?b) AS ?born) (SAMPLE(?d) AS ?died) (SAMPLE(?hi) AS ?historian) WHERE {{ VALUES ?x {{ VALS }} {LAB}
        OPTIONAL {{ ?x wdt:P31 ?c }} OPTIONAL {{ ?x wdt:P244 ?lc }} OPTIONAL {{ ?x wdt:P496 ?or }} OPTIONAL {{ ?x wdt:P227 ?gn }}
        OPTIONAL {{ ?x wdt:P214 ?vi }} OPTIONAL {{ ?x wdt:P213 ?is }} OPTIONAL {{ ?x wdt:P269 ?ir }}
        OPTIONAL {{ ?x wdt:P569 ?b }} OPTIONAL {{ ?x wdt:P570 ?d }} OPTIONAL {{ ?x wdt:P106/wdt:P279* {hist} BIND(1 AS ?hi) }} }}
        GROUP BY ?x ?en ?mul ?fr ?de ?es ?pt""", 'm-recipients')
    for r in rx:
        meta[r['x']] = r
    # works: those named by for-work and recipients that are works
    wk_ids = sorted(set(works) | {q for q, r in meta.items() if not r.get('born') and not r.get('historian')})
    wx = batch(wk_ids, f"""SELECT ?x ?en ?mul ?fr ?de ?es ?pt (GROUP_CONCAT(DISTINCT ?au; separator='|') AS ?authors)
        (SAMPLE(?pd) AS ?pub) (SAMPLE(?lccn) AS ?lccn_) (SAMPLE(?i13) AS ?isbn13) (SAMPLE(?i10) AS ?isbn10) (SAMPLE(?doi) AS ?doi_)
        (SAMPLE(?pb) AS ?publisher) (SAMPLE(?c) AS ?cls) WHERE {{ VALUES ?x {{ VALS }} {LAB} OPTIONAL {{ ?x wdt:P50 ?au }}
        OPTIONAL {{ ?x wdt:P577 ?pd }} OPTIONAL {{ ?x wdt:P1144 ?lccn }} OPTIONAL {{ ?x wdt:P212 ?i13 }} OPTIONAL {{ ?x wdt:P957 ?i10 }}
        OPTIONAL {{ ?x wdt:P356 ?doi }} OPTIONAL {{ ?x wdt:P123 ?pbq . ?pbq rdfs:label ?pb FILTER(lang(?pb)='en') }}
        OPTIONAL {{ ?x wdt:P31 ?c }} }} GROUP BY ?x ?en ?mul ?fr ?de ?es ?pt""", 'm-works')
    wmeta = {r['x']: r for r in wx}
    # a recipient is a work when it has an author, a publication date or an ISBN and no birth date
    ax = batch(awards, f"""SELECT ?x ?en ?mul ?fr ?de ?es ?pt (SAMPLE(?cb) AS ?body) (SAMPLE(?cbl) AS ?body_label)
        (SAMPLE(?ctry) AS ?country) (SAMPLE(?cl) AS ?country_label) (GROUP_CONCAT(DISTINCT ?cls; separator='|') AS ?classes)
        (GROUP_CONCAT(DISTINCT ?clsl; separator='|') AS ?class_labels) (SAMPLE(?web) AS ?website) (SAMPLE(?subj) AS ?subject)
        WHERE {{ VALUES ?x {{ VALS }} {LAB} OPTIONAL {{ ?x wdt:P1027 ?cb OPTIONAL {{ ?cb rdfs:label ?cbl FILTER(lang(?cbl)='en') }} }}
        OPTIONAL {{ ?x wdt:P17 ?ctry OPTIONAL {{ ?ctry rdfs:label ?cl FILTER(lang(?cl)='en') }} }}
        OPTIONAL {{ ?x wdt:P31 ?cls OPTIONAL {{ ?cls rdfs:label ?clsl FILTER(lang(?clsl)='en') }} }}
        OPTIONAL {{ ?x wdt:P856 ?web }} OPTIONAL {{ ?x wdt:P921|wdt:P101 ?subj }} }} GROUP BY ?x ?en ?mul ?fr ?de ?es ?pt""",
               'm-awards', size=2000)
    ameta = {r['x']: r for r in ax}
    # the authors of works that are recipients
    au_ids = sorted({a for r in wmeta.values() for a in (r.get('authors') or '').split('|') if a.startswith('Q')} - set(meta))
    for r in batch(au_ids, f"""SELECT ?x ?en ?mul ?fr ?de ?es ?pt (SAMPLE(?lc) AS ?lcnaf) (SAMPLE(?or) AS ?orcid)
        (SAMPLE(?gn) AS ?gnd) (SAMPLE(?vi) AS ?viaf) (SAMPLE(?b) AS ?born) (SAMPLE(?d) AS ?died) WHERE {{ VALUES ?x {{ VALS }} {LAB}
        OPTIONAL {{ ?x wdt:P244 ?lc }} OPTIONAL {{ ?x wdt:P496 ?or }} OPTIONAL {{ ?x wdt:P227 ?gn }} OPTIONAL {{ ?x wdt:P214 ?vi }}
        OPTIONAL {{ ?x wdt:P569 ?b }} OPTIONAL {{ ?x wdt:P570 ?d }} }} GROUP BY ?x ?en ?mul ?fr ?de ?es ?pt""", 'm-authors'):
        meta[r['x']] = r

    def label(r):
        return next((r.get(k) for k in ('en', 'mul', 'fr', 'de', 'es', 'pt') if r and r.get(k)), '')

    def pids(r):
        if not r:
            return ''
        out = [f'{k}:{r[k]}' for k in ('lcnaf', 'orcid', 'gnd', 'viaf', 'isni', 'idref') if r.get(k)]
        if r.get('born'):
            out.append('born:' + r['born'][:4].lstrip('+'))
        if r.get('died'):
            out.append('died:' + r['died'][:4].lstrip('+'))
        return ' '.join(out)

    def wids(r):
        if not r:
            return ''
        out = []
        if r.get('lccn_'):
            out.append('lccn:' + r['lccn_'])
        for k in ('isbn13', 'isbn10'):
            if r.get(k):
                out.append('isbn:' + r[k].replace('-', ''))
        if r.get('doi_'):
            out.append('doi:' + r['doi_'].lower())
        if r.get('pub'):
            out.append('pub:' + r['pub'][:4].lstrip('+'))
        return ' '.join(out)

    rows, seen = [], set()
    for s in stmts:
        a, h, w = s['a'], s['h'], s['w']
        am = ameta.get(a, {})
        hm = wmeta.get(h, {})
        is_work = bool(hm) and not meta.get(h, {}).get('born') and bool(hm.get('authors') or hm.get('pub') or hm.get('isbn13')
                                                                       or hm.get('isbn10') or hm.get('lccn_'))
        person, work = (None, h) if is_work else (h, w or None)
        key = (a, person, work, s['t'][:4])
        if key in seen:
            continue
        seen.add(key)
        wm = wmeta.get(work, {}) if work else {}
        authors = [x for x in (wm.get('authors') or '').split('|') if x]
        if is_work and authors:
            person = authors[0]
        pm = meta.get(person, {}) if person else {}
        rows.append(dict(
            prize=label(am) or a, body=am.get('body_label', ''), body_country=am.get('country_label', ''),
            field='history' if a in hp else '', honours='', year=s['t'][:4].lstrip('+'),
            winner=label(pm), co_winners='; '.join(label(meta.get(x, {})) or x for x in authors[1:]) if is_work else '',
            work_title=label(wm), publisher=wm.get('publisher', ''), wd_prize=a, wd_person=person or '',
            wd_work=work or '', person_ids=pids(pm), work_ids=wids(wm),
            source_url=f'https://www.wikidata.org/wiki/{person or work}', source_kind='wikidata',
            note=';'.join(x for x in ('via ' + s['via'], 'award classes: ' + (am.get('class_labels') or '')[:200]) if x)))
    write_rows('wikidata', rows)
    (BUILD / 'wikidata' / 'history-prizes.json').write_text(json.dumps(hp_list))
    json.dump({q: dict(label=label(r), body=r.get('body_label', ''), country=r.get('country_label', ''),
                       classes=r.get('class_labels', ''), website=r.get('website', ''), history=q in hp)
               for q, r in ameta.items()}, (BUILD / 'wikidata' / 'awards.json').open('w'), ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('cha')
    a.add_argument('--no-fetch', action='store_true')
    a = sub.add_parser('wikidata')
    a.add_argument('--graph', default=str(ROOT / 'build/graph'))
    a = sub.add_parser('web')
    a.add_argument('--only', default='')
    sub.add_parser('assemble')
    args = ap.parse_args()
    if args.cmd == 'web':
        # one parser module per group of awarding bodies; each writes build/prizes-2026-11-12/rows-web-<group>.jsonl
        import importlib
        for mod, name in (('prizes_web_us', 'web-us'), ('prizes_web_uk_ca_intl', 'web-uk-ca-intl'),
                          ('prizes_web_fr_de_br_mx', 'web-fr-de-br-mx')):
            if args.only and name not in args.only.split(','):
                continue
            write_rows(name, importlib.import_module(mod).harvest())
    elif args.cmd == 'assemble':
        assemble(args)
    else:
        globals()[args.cmd](args)


COUNTRY = {'Canada': 'CA', 'United States': 'US', 'United States of America': 'US', 'United Kingdom': 'GB', 'France': 'FR',
           'Germany': 'DE', 'Brazil': 'BR', 'Mexico': 'MX', 'Italy': 'IT', 'Spain': 'ES', 'Netherlands': 'NL', 'Kingdom of the Netherlands': 'NL',
           'Norway': 'NO', 'Sweden': 'SE', 'Denmark': 'DK', 'Finland': 'FI', 'Poland': 'PL', 'Russia': 'RU', 'Soviet Union': 'SU',
           'Israel': 'IL', 'Switzerland': 'CH', 'Austria': 'AT', 'Belgium': 'BE', 'Ireland': 'IE', 'Australia': 'AU',
           'Portugal': 'PT', 'Argentina': 'AR', 'Japan': 'JP', 'China': 'CN', "People's Republic of China": 'CN', 'India': 'IN',
           'Czech Republic': 'CZ', 'Czechia': 'CZ', 'Hungary': 'HU', 'Romania': 'RO', 'Greece': 'GR', 'Turkey': 'TR',
           'Ukraine': 'UA', 'Serbia': 'RS', 'Croatia': 'HR', 'Slovenia': 'SI', 'Slovakia': 'SK', 'Bulgaria': 'BG',
           'Lithuania': 'LT', 'Latvia': 'LV', 'Estonia': 'EE', 'New Zealand': 'NZ', 'South Africa': 'ZA', 'Chile': 'CL',
           'Colombia': 'CO', 'Peru': 'PE', 'Cuba': 'CU', 'Vatican City': 'VA', 'Holy See': 'VA', 'Iceland': 'IS',
           'Luxembourg': 'LU', 'Georgia': 'GE', 'Armenia': 'AM', 'Belarus': 'BY', 'Kazakhstan': 'KZ', 'Iran': 'IR',
           'South Korea': 'KR', 'Egypt': 'EG', 'Germany (East)': 'DD', 'German Democratic Republic': 'DD', 'Yugoslavia': 'YU'}
HONOUR_RX = [  # Wikidata award classes and labels -> what the prize honours
    (r'(?i)honorary (doctor|degree)|doctor honoris|honoris causa|ehrendoktor|docteur honoris', 'other'),
    (r'(?i)\border\b|ordre|orden\b|knight|chevalier|commander|officer of|decoration|medal of honou?r|cross of|'
     r'grand cross|légion|legion of honour|state award|hero of|title of honou?r|honorary citizen|ehrenbürger', 'other'),
    (r'(?i)fellowship|stipend|scholarship|grant\b|guggenheim', 'other'),
    (r'(?i)dissertation|thesis|doctoral|these|tese|tesis', 'dissertation'),
    (r'(?i)article|essay prize|paper prize', 'article'),
    (r'(?i)book|literary award|literature award|livre|buch|libro|livro|non-?fiction|biography', 'book'),
]


def wd_honours(r, aw):
    if r.get('wd_work') and r['work_title']:
        return 'book' if not re.search(r'(?i)scholarly article|journal article', r.get('note', '')) else 'article'
    txt = ' '.join([r['prize'], (aw or {}).get('classes', '')])
    for rx, h in HONOUR_RX:
        if re.search(rx, txt):
            return h if h != 'book' else 'book'
    if re.search(r'(?i)prize|award|medal|prix|preis|premio|prêmio|nagroda|cena|palkinto', txt):
        return 'career'
    return 'other'


def row_id(r):
    k = '|'.join([r['source_kind'], r['prize_id'], r['year'], fold(r['winner']), fold(r['work_title'])[:80], r['wd_person'],
                  r['wd_work'], r['source_url']])
    return 'pr-' + hashlib.sha1(k.encode()).hexdigest()[:12]


def assemble(args):
    """rows-*.jsonl -> data/graph/prizes/prizes.csv.gz (one row per prize fact) and the harvest part of report.json."""
    rows = []
    awards = {}
    ap = BUILD / 'wikidata' / 'awards.json'
    if ap.exists():
        awards = json.loads(ap.read_text())
    for f in sorted(BUILD.glob('rows-*.jsonl')):
        for line in f.open(encoding='utf-8'):
            r = json.loads(line)
            r = {c: str(r.get(c) or '').strip() for c in COLS}
            if not r['winner'] and not r['work_title']:
                continue
            if r['source_kind'] == 'wikidata':
                aw = awards.get(r['wd_prize'], {})
                r['body_country'] = COUNTRY.get(r['body_country'], r['body_country'])
                r['honours'] = wd_honours(r, aw)
                if not r['prize_id']:
                    r['prize_id'] = 'prize:wd-' + r['wd_prize']
            if not r['prize_id']:
                r['prize_id'] = prize_id(r['body'], r['prize'])
            if r['year'] and not re.fullmatch(r'\d{4}', r['year']):
                r['note'] = (r['note'] + '; year as given: ' + r['year']).strip('; ')
                r['year'] = ''
            rows.append(r)
    seen, out = set(), []
    for r in rows:
        r['id'] = row_id(r)
        if r['id'] in seen:
            continue
        seen.add(r['id'])
        out.append(r)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    cols = ['id'] + COLS
    with gzip.open(OUTDIR / 'prizes.csv.gz', 'wt', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in sorted(out, key=lambda r: (r['source_kind'], r['prize_id'], r['year'], r['winner'])):
            w.writerow({c: r[c] for c in cols})
    rep_path = OUTDIR / 'report.json'
    rep = json.loads(rep_path.read_text()) if rep_path.exists() else {}
    by = Counter((r['source_kind'], r['body'] if r['source_kind'] != 'wikidata' else '(Wikidata)', r['body_country']) for r in out)
    rep['harvest'] = dict(
        date='2026-11-12', rows=len(out),
        by_source_kind=dict(Counter(r['source_kind'] for r in out)),
        by_honours=dict(Counter(r['honours'] for r in out)),
        by_country=dict(Counter(r['body_country'] or '?' for r in out).most_common()),
        awarding_body_rows_by_body={f'{b} ({c})': n for (k, b, c), n in sorted(by.items(), key=lambda kv: -kv[1]) if k != 'wikidata'},
        wikidata_history_prize_rows=sum(1 for r in out if r['source_kind'] == 'wikidata' and r['field'] == 'history'),
        rows_with_work_title=sum(1 for r in out if r['work_title']),
        fetch_log='build/prizes-2026-11-12/fetch-log.jsonl (not in git)')
    refusals = []
    if (BUILD / 'fetch-log.jsonl').exists():
        for line in (BUILD / 'fetch-log.jsonl').open(encoding='utf-8'):
            d = json.loads(line)
            if d.get('refused'):
                refusals.append((urllib.parse.urlparse(d['url']).netloc, d['refused']))
    rep['harvest']['refusals'] = sorted({f'{h}: {k}' for h, k in refusals})
    rep_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(rep['harvest'], indent=1, ensure_ascii=False)[:3000])


if __name__ == '__main__':
    main()
