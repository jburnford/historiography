"""History prize winners from awarding bodies' own public pages: United Kingdom, Canada (outside the CHA) and
international foundations (harvested 2026-11-12).

One row per (prize, year, winner, work), read only from pages fetched with the project's polite fetcher
(scripts/prizes_fetch.py: robots.txt obeyed, 1.2 s per host, raw pages cached under build/prizes-2026-11-12/raw/,
every fetch and refusal logged to build/prizes-2026-11-12/fetch-log.jsonl). Shortlists and finalists are skipped.

Bodies and URLs
  Wolfson History Prize (GB)          https://www.wolfsonhistoryprize.org.uk/past-winners/ and the year pages it links
                                      (/past-winners/YYYY-winners/, /past-winners/2024-shortlist/), 1972-2025
  Royal Historical Society (GB)       https://royalhistsoc.org/recipients-of-the-royal-historical-society-book-prizes-1977-2024/
                                      (Whitfield 1977-2024, Gladstone 1997-2024, First Book Prize 2025-2026) and
                                      https://royalhistsoc.org/prizes/royal-historical-society-early-career-article-prize/rhs-alexander-prize-past-winners/
                                      (Alexander Prize / Early Career Article Prize, 1898-2026)
  British Academy (GB)                https://www.thebritishacademy.ac.uk/prizes-medals/british-academy-medal/ (2013-2019)
                                      https://www.thebritishacademy.ac.uk/prizes-medals/leverhulme-medal-prize/ (2002-2021)
                                      both medals are for any humanities/social-science field: field says so
  Cundill History Prize (McGill, CA)  https://www.cundillprize.com/winners/YYYY (2008-2026; winner + "Recognition of
                                      Excellence" awards; affiliation from the first biography sentence when printed)
  Institut d'histoire de l'Amérique française (CA)
                                      https://ihaf.qc.ca/<prize page>/ for the Grand Prix (formerly Prix Lionel-Groulx),
                                      Prix de l'Assemblée nationale du Québec, Prix Michel-Brunet, Prix Louise-Dechêne
                                      (theses), Prix Paul-André-Linteau, Prix de la Revue d'histoire de l'Amérique française
  Manitoba Historical Society (CA)    https://www.mhs.ca/awards/margaret-mcwilliams-award-program/past-winners/
  Ontario Historical Society (CA)     https://www.ontariohistoricalsociety.ca/past-recipients (author awards only,
                                      2008-09 to 2023-24 cycles; year = first year of the cycle as the OHS names it)
  Holberg Prize (NO)                  https://holbergprize.org/prizes-and-laureates/holbergprize/holberg-prize-laureates/
  Balzan Prize (IT/CH)                https://www.balzan.org/en/prizewinners?quinquennio=YYYY (history-type subjects only)
  Dr A.H. Heineken Prize for History (NL)
                                      https://www.heinekenprizes.org/list-of-laureates/ (+ /page/N/)
  Dan David Prize (IL)                https://dandavidprize.org/our-winners/ (+ /page/N/, 2022-) and
                                      https://dandavidprize.org/previous-laureates/ (+ /page/N/, 2002-2021, "Past" dimension only)

Refused or skipped (recorded in the fetch log; never worked around): History Today / Longman-History Today awards
(robots.txt 403 + challenge), KNAW (robots 403; the Heineken site itself was used), Champlain Society (robots 403),
Governor General's Literary Awards ggbooks.ca (robots Disallow), Canada Council Killam/Molson pages (robots Disallow),
killamlaureates.ca (robots 403), BC Historical Federation bchistory.ca (robots 403), British Academy other medal pages
(HTTP 403 after two pages).

    python3 scripts/prizes_web_uk_ca_intl.py      # -> build/prizes-2026-11-12/rows-web-uk-ca-intl.jsonl + counts
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from prizes_fetch import fetch, text_of  # noqa: E402
from prizes_harvest import prize_id  # noqa: E402

OUT = ROOT / 'build/prizes-2026-11-12/rows-web-uk-ca-intl.jsonl'
COLS = ['prize_id', 'prize', 'body', 'body_country', 'field', 'honours', 'year', 'winner', 'co_winners', 'work_title',
        'publisher', 'wd_prize', 'wd_person', 'wd_work', 'person_ids', 'work_ids', 'source_url', 'source_kind', 'note']

HONORIFIC = re.compile(r'^(?:(?:Professor|Prof\.|Dr\.|Dr|Dame|Sir|Baroness|Lord|Justice|Mme|Rev\.|Rev|Mrs\.|Mrs|Mr\.|Miss|Major|Father|Fr\.)(?:\s+|(?<=\.)(?=[A-Z])))+')


def clean(s):
    s = (s or '').replace('\xa0', ' ').replace('​', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return re.sub(r'(?<=\w)\s+([,;])', r'\1', s)


def person(s):
    s = clean(s)
    s = re.sub(r'\s*\bFBA\b', '', s)
    s = HONORIFIC.sub('', s)
    return clean(s.strip(' ,;.'))


def split_names(s, sep=r'\s*,\s*|\s+(?:and|&|et)\s+'):
    out = [person(x) for x in re.split(sep, clean(s)) if clean(x)]
    return [x for x in out if x and x.lower() not in ('al.', 'al')]


def strip_quotes(t):
    t = clean(t)
    t = re.sub(r'^[‘\'“"]+', '', t)
    t = re.sub(r'[’′\'”"‘]+$', '', t)
    return clean(t)


def rows_for(base, names, **kw):
    """One row per name; co-winners carried."""
    out = []
    for n in names:
        r = dict(base)
        r.update(kw)
        r['winner'] = n
        r['co_winners'] = '; '.join(x for x in names if x != n)
        out.append(r)
    return out


def base(body, country, prize, field, honours, url, note=''):
    r = {c: '' for c in COLS}
    r.update(prize_id=prize_id(body, prize), prize=prize, body=body, body_country=country, field=field,
             honours=honours, source_url=url, source_kind='awarding-body', note=note)
    return r


def lines(html, main=True):
    return [clean(x) for x in text_of(html, main=main).split('\n') if clean(x)]


# ---------------------------------------------------------------- Wolfson History Prize

def wolfson():
    body, top = 'Wolfson Foundation', 'https://www.wolfsonhistoryprize.org.uk/past-winners/'
    h = fetch(top)
    if not h:
        return []
    urls = sorted(set(re.findall(r'href="(?:https://www\.wolfsonhistoryprize\.org\.uk)?(/past-winners/\d{4}-[a-z]+/)"', h)))
    out = []
    for path in urls:
        url = 'https://www.wolfsonhistoryprize.org.uk' + path
        x = fetch(url)
        if not x:
            continue
        t = lines(x)
        hi = next((i for i, l in enumerate(t) if re.fullmatch(r'\d{4} Winners?', l)), None)
        if hi is None:
            continue                      # e.g. 2026: shortlist only so far
        year = t[hi][:4]
        end = next((i for i in range(hi + 1, len(t)) if t[i].startswith('Judges') or t[i].endswith('Shortlist')), len(t))
        block = t[hi + 1:end]
        b = base(body, 'GB', 'Wolfson History Prize', 'history', 'book', url)
        if t[hi].endswith('Winner'):       # 2017-: one winner, title in parts, then author, then "Read more"
            stop = next((i for i, l in enumerate(block) if l.startswith('Read more')), len(block))
            parts = block[:stop]
            if len(parts) < 2:
                continue
            title = ''
            for p in parts[:-1]:
                p = strip_quotes(p)
                title = p if not title else (title + (' ' if title.endswith(':') else ': ') + p)
            out += rows_for(b, split_names(parts[-1], r'\s+(?:and|&)\s+'), year=year, work_title=title)
            continue
        i = 0
        while i < len(block):
            l = block[i]
            if l.startswith('For distinguished contribution'):
                if i + 1 < len(block):
                    out += rows_for(dict(b, honours='career', note='for distinguished contribution to the writing of history'),
                                    [person(block[i + 1])], year=year)
                i += 2
                continue
            if l[:1] in '‘\'“':
                parts = [l]
                while not re.search(r'[’′\'”]$', parts[-1]) and i + len(parts) < len(block):
                    parts.append(block[i + len(parts)])
                j = i + len(parts)
                title = ''
                for p in parts:
                    p = strip_quotes(p)
                    title = p if not title else title + ' ' + p
                author = block[j] if j < len(block) else ''
                pub = ''
                if j + 1 < len(block) and not block[j + 1].startswith(('Read more', 'For distinguished')) \
                        and block[j + 1][:1] not in '‘\'“':
                    pub = block[j + 1]
                    j += 1
                if author:
                    out += rows_for(b, split_names(author, r'\s+(?:and|&)\s+'), year=year, work_title=title, publisher=pub)
                i = j + 1
                continue
            i += 1
    return out


# ---------------------------------------------------------------- Royal Historical Society

def _pub_year(s):
    s = clean(s)
    return clean(re.sub(r'[,:]?\s*\d{4}\s*$', '', s))


def rhs_books():
    body = 'Royal Historical Society'
    url = 'https://royalhistsoc.org/recipients-of-the-royal-historical-society-book-prizes-1977-2024/'
    h = fetch(url)
    if not h:
        return []
    out, prize, year = [], None, None
    for l in lines(h):
        m = re.match(r'Winners of the RHS (.+?Prize)', l)
        if m:
            prize = 'RHS ' + m.group(1)
            continue
        if not prize:
            continue
        if re.fullmatch(r'\d{4}', l):
            year = l
            continue
        if l == 'and' or l.startswith('From this point') or not year:
            continue
        pub = ''
        m = re.search(r'\(([^()]*)\)\s*\.?$', l)
        rest = l
        if m:
            pub, rest = _pub_year(m.group(1)), clean(l[:m.start()])
        rest = rest.rstrip(' ,')
        if ', by ' in rest:
            title, name = rest.rsplit(', by ', 1)
        elif re.match(r'^[^:,]{3,60}? for ', rest):
            name, title = rest.split(' for ', 1)
        elif ',' in rest:
            name, title = rest.split(',', 1)
        else:
            continue
        title = clean(re.sub(r'\bT he\b', 'The', title)).rstrip(' ,')
        note = 'first book' if 'First Book' in prize else ''
        out += rows_for(base(body, 'GB', prize, 'history', 'book', url, note), [person(name)], year=year,
                        work_title=title, publisher=pub)
    return out


def rhs_articles():
    body = 'Royal Historical Society'
    url = ('https://royalhistsoc.org/prizes/royal-historical-society-early-career-article-prize/'
           'rhs-alexander-prize-past-winners/')
    h = fetch(url)
    if not h:
        return []
    prize = 'Alexander Prize (RHS Early Career Article Prize)'
    degree = re.compile(r'(?:\s*,?\s*\.?\b(?:BA|MA|PhD|DPhil|BLitt|Blitt|LLB|AM|MLitt|BSc|MSc|RMSA|FRHistS|NIA)\b\.?)+\s*$')
    out, year = [], None
    seen = Counter()
    for l in lines(h):
        m = re.match(r'^(\d{4})\s+(.*)$', l)
        if m:
            year, l = m.group(1), m.group(2)
        elif l == 'and' or l.startswith('From this point') or not year:
            continue
        if re.match(r'(?i)(– \d{4} )?no award', l) or not l:
            continue
        q = re.search(r'[‘“\']', l)
        if not q:
            continue
        name_part, rest = l[:q.start()], l[q.start():]
        name = person(degree.sub('', name_part.split(',')[0]))
        if not name:
            continue                       # 2024: second winner printed without a name
        rest = re.sub(r',([’‘]) ', r'\1, ', rest)
        close = {'‘': '’‘', '“': '”', "'": "'’"}[rest[0]]
        tm = re.match(r'[‘“\'](.+?)[' + close + r']\s*(?=,|\.|\s+in\s|\s*\(|$)', rest)
        title = re.sub(r'^”', '“', clean(tm.group(1))) if tm else strip_quotes(rest)
        venue = clean(rest[tm.end():]).strip(' ,.') if tm else ''
        venue = re.sub(r'^in\s+', '', venue)
        note = ('published: ' + venue) if venue and not venue.startswith('(Not published') else \
            ('not published in Transactions' if venue else '')
        seen[(year, title)] += 1
        out += rows_for(base(body, 'GB', prize, 'history', 'article', url, note), [name], year=year,
                        work_title=title.rstrip('.'))
    for r in out:
        if seen[(r['year'], r['work_title'])] > 1:
            r['note'] = clean(r['note'] + '; page prints the same title for two winners this year').strip('; ')
    return out


# ---------------------------------------------------------------- British Academy

def british_academy():
    body, out = 'British Academy', []
    field = 'humanities and social sciences (any field)'
    url = 'https://www.thebritishacademy.ac.uk/prizes-medals/leverhulme-medal-prize/'
    h = fetch(url)
    if h:
        t = lines(h, main=False)
        i = next((k for k, l in enumerate(t) if l.endswith('revious winners')), None)
        if i is not None:
            for l in t[i + 1:]:
                if l.startswith('History of the prize'):
                    break
                m = re.match(r'^(\d{4}) (.+)$', l)
                if not m or re.match(r'^\d{4} - \d{4}$', l):
                    continue
                year, rest = m.groups()
                if ' and ' in rest and ',' not in rest:
                    out += rows_for(base(body, 'GB', 'Leverhulme Medal and Prize', field, 'career', url),
                                    split_names(rest, r'\s+and\s+'), year=year)
                    continue
                name, _, aff = rest.partition(',')
                out += rows_for(base(body, 'GB', 'Leverhulme Medal and Prize', field, 'career', url,
                                     ('affiliation: ' + clean(aff)) if aff.strip() else ''), [person(name)], year=year)
    url = 'https://www.thebritishacademy.ac.uk/prizes-medals/british-academy-medal/'
    h = fetch(url)
    if h:
        t = lines(h, main=False)
        b = base(body, 'GB', 'British Academy Medal', field, 'book', url)
        i = next((k for k, l in enumerate(t) if l.endswith('revious winners')), None)
        year = None
        for k in range(i + 1 if i is not None else len(t), len(t)):
            l = t[k]
            if l.startswith('Sign up'):
                break
            m = re.match(r'^(\d{4}):\s+(.+)$', l)
            if m:                                      # "2019: Professor Naomi Oreskes" + a prose paragraph
                year, name = m.group(1), person(m.group(2))
                para = next((x for x in t[k + 1:k + 4] if 'awarded the British Academy Medal' in x), '')
                bm = re.search(r'for (?:her|his|their) books? (.+?)(?:, both|\.)', para)
                works = [clean(w) for w in re.split(r'\s+and\s+', re.sub(r'\s*\([^)]*\)', '', bm.group(1)))] if bm else ['']
                for w in works:
                    out += rows_for(b, [name], year=year, work_title=w)
                continue
            if re.fullmatch(r'\d{4}', l):
                year = l
                continue
            if not year or ' for ' not in l or re.fullmatch(r'\d{4} - \d{4}', l) or 'was awarded' in l \
                    or l[:1] in '"“-' or len(l) > 300:
                continue
            who, what = l.split(' for ', 1)
            names = split_names(who, r'\s+and\s+')
            aff = ''
            if len(names) == 1 and ',' in who:
                n, _, aff = who.partition(',')
                names = [person(n)]
            note = ('affiliation: ' + clean(aff)) if aff.strip() else ''
            if what.startswith('lifetime achievement'):
                out += rows_for(dict(b, honours='career', note=clean(note + '; for ' + what.rstrip('.')).strip('; ')),
                                names, year=year)
                continue
            what = re.sub(r'^(?:two-volume publication|the)\s+', '', what.rstrip('.'))
            for w in re.split(r'\)\s+and\s+', what):
                pm = re.search(r'\(([^()]*)\)?\s*$', w)
                pub = clean(pm.group(1).split(',')[0]) if pm else ''
                title = clean(w[:pm.start()]) if pm else clean(w)
                out += rows_for(dict(b, note=note), names, year=year, work_title=title, publisher=pub)
    return out


# ---------------------------------------------------------------- Cundill History Prize

AFF = re.compile(r"\bat (?:the )?((?:[A-Z][\w'’.-]*|of|at|and)(?:\s+(?:[A-Z][\w'’.-]*|of|at))*(?:, University of London)?)")


def _affiliation(bio):
    first = re.split(r'(?<=[a-z])\.\s', bio, maxsplit=1)[0]
    for m in AFF.finditer(first):
        a = clean(m.group(1))
        if re.search(r'University|College|Institute|School', a):
            return a
    return ''


def cundill():
    body, out = 'Cundill History Prize, McGill University', []
    for y in range(2008, 2027):
        url = f'https://www.cundillprize.com/winners/{y}'
        h = fetch(url)
        if not h:
            continue
        t = lines(h, main=False)

        def block(k):
            name = t[k + 1].rstrip(' -').strip()
            b = next((j for j in range(k + 2, min(len(t), k + 8)) if t[j] == 'Biography'), None)
            if b is None:
                return None
            title = ''
            for p in t[k + 2:b]:
                title = p if not title else title + (' ' if title.endswith(':') else ': ') + p
            return name, title, _affiliation(t[b + 1]) if b + 1 < len(t) else ''

        for k, l in enumerate(t):
            if l == f'{y} Winner':
                got = block(k)
                if got:
                    name, title, aff = got
                    out += rows_for(base(body, 'CA', 'Cundill History Prize', 'history', 'book', url,
                                         ('affiliation: ' + aff) if aff else ''), [person(name)], year=str(y),
                                    work_title=title)
            elif l.startswith('Recipient of the') and 'Recognition of Excellence' in l:
                f = max((j for j in range(k) if t[j] == 'Finalist'), default=None)
                got = block(f) if f is not None else None
                if got:
                    name, title, aff = got
                    out += rows_for(base(body, 'CA', 'Cundill History Prize Recognition of Excellence', 'history',
                                         'book', url, clean('finalist; ' + (('affiliation: ' + aff) if aff else '')).strip('; ')),
                                    [person(name)], year=str(y), work_title=title)
    return out


# ---------------------------------------------------------------- IHAF

IHAF = [('grand-prix-de-linstitut-dhistoire-de-lamerique-francaise',
         "Grand Prix de l'Institut d'histoire de l'Amérique française", 'history of French America', 'book',
         'formerly Prix Lionel-Groulx'),
        ('prix-de-lassemblee-nationale-du-quebec', "Prix de l'Assemblée nationale du Québec",
         'political history of French America', 'book', ''),
        ('prix-michel-brunet', 'Prix Michel-Brunet', 'history (early-career Quebec author)', 'book', ''),
        ('prix-louise-dechene', 'Prix Louise-Dechêne', 'history of French America', 'dissertation', ''),
        ('prix-paul-andre-linteau', 'Prix Paul-André-Linteau', 'history of Montreal', '', ''),
        ('prix-de-la-revue-dhistoire-de-lamerique-francaise', "Prix de la Revue d'histoire de l'Amérique française",
         'history of French America', 'article', '')]


def ihaf():
    body, out = "Institut d'histoire de l'Amérique française", []
    for slug, prize, field, honours, pnote in IHAF:
        url = f'https://ihaf.qc.ca/{slug}/'
        h = fetch(url)
        if not h:
            continue
        t = lines(h, main=False)
        for k, l in enumerate(t):
            if not re.fullmatch(r'(19|20)\d\d', l):
                continue
            stop = next((j for j in range(k + 1, min(len(t), k + 7)) if t[j].startswith('Fiche Laur')), None)
            if stop is None or stop - k < 3:
                continue
            names_line, title = t[k + 1], t[k + 2]
            venue = t[k + 3] if stop - k >= 4 else ''
            notes = [pnote] if pnote else []
            if re.search(r'(?i)ex aequo', names_line):
                notes.append('ex aequo')
                names_line = re.sub(r'(?i),?\s*ex aequo', '', names_line)
            if re.search(r'(?i)\((?:dir\.?|directeurs?|directrices?|eds?\.?|éd\.?)\)', names_line):
                notes.append('editors')
                names_line = re.sub(r'(?i)\s*\((?:dir\.?|directeurs?|directrices?|eds?\.?|éd\.?)\)', '', names_line)
            if re.search(r'\bet al\.?', names_line):
                notes.append('et al. on page')
            hon = honours or ('article' if re.search(r'(?i)revue|journal|vol\.|no \d', venue) else 'book')
            pub = ''
            if hon == 'book':
                pub = clean(re.sub(r',?\s*\d{4}\s*$', '', venue))
            elif venue:
                notes.append(('thesis: ' if hon == 'dissertation' else 'published: ') + venue)
            out += rows_for(base(body, 'CA', prize, field, hon, url, '; '.join(notes)),
                            split_names(names_line, r'\s*,\s*|\s+et\s+'), year=l, work_title=title, publisher=pub)
    return out


# ---------------------------------------------------------------- Manitoba Historical Society

def mhs():
    body = 'Manitoba Historical Society'
    url = 'https://www.mhs.ca/awards/margaret-mcwilliams-award-program/past-winners/'
    h = fetch(url)
    if not h:
        return []
    import html as H
    out = []
    panes = re.split(r'<span class="kt-blocks-accordion-title">', h)[1:]
    for p in panes:
        ym = re.match(r'\s*(\d{4})\s*</span>', p)
        if not ym:
            continue
        year = ym.group(1)
        tm = re.search(r'(?s)<table.*?</table>', p)
        if not tm:
            continue
        rows = re.findall(r'(?s)<tr>(.*?)</tr>', tm.group(0))
        cells = [[clean(H.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'(?i)<br\s*/?>', ' ', c))))
                  for c in re.findall(r'(?s)<t[dh][^>]*>(.*?)</t[dh]>', r)] for r in rows]
        if not cells:
            continue
        head = [c.lower() for c in cells[0]]
        if 'title' not in head or 'author' not in head:
            continue
        for c in cells[1:]:
            if len(c) != len(head):
                continue
            d = dict(zip(head, c))
            author, title, cat = d.get('author', ''), d.get('title', ''), d.get('category', '')
            if not author or not title or '?' in (author, title):
                continue
            notes = []
            hm = re.compile(r'(?i)\s*\(honou?rable mention\)')
            if hm.search(cat) or hm.search(title) or hm.search(author):
                notes.append('honourable mention')
                cat, title, author = hm.sub('', cat), hm.sub('', title), hm.sub('', author)
            if cat:
                notes.insert(0, 'category: ' + cat)
            honours, work = 'book', title
            if re.search(r'(?i)thesis', cat):
                honours = 'dissertation'
            elif re.search(r'(?i)essay', cat):
                honours = 'other'
            elif re.search(r'(?i)special project', cat):
                honours = 'other'
            elif re.search(r'(?i)individual contribution', cat):
                honours, work = 'other', ''
                notes.append('for: ' + title)
            if re.search(r'(?i)\(editors?\)|\beds?\.|edited by', author):
                notes.append('editor')
                author = re.sub(r'(?i)\s*\(editors?\)|\beds?\.\s*|edited by\s*', ' ', author)
            rm = re.search(r'\s*\(([^)]*)\)', author)
            if rm:
                notes.append('role: ' + rm.group(1))
                author = author[:rm.start()] + author[rm.end():]
            if re.search(r'(?i)as told to', author):
                notes.append('author as printed: ' + d['author'])
            if re.search(r'(?i)committee|church|society|museum|institute|association|club|group|\bRM of\b|women|branch|'
                         r'council|histor|horizons|school|parish|legion|board|district|department|municipality|library|archives|'
                         r'associates|class\b|students|grade|centre|center|project|regional|^Mr\.? (?:and|&) Mrs', author):
                names = [clean(author)]                       # an organisation: keep as printed, never split
                notes.append('organisation as printed')
            else:
                author = re.sub(r'\s+CD$', '', clean(author))
                names = split_names(re.sub(r'(?i)\s+as told to\s+', ', ', author), r'\s*,\s*|\s+(?:and|&)\s+')
            out += rows_for(base(body, 'CA', 'Margaret McWilliams Award', 'Manitoba history', honours, url,
                                 '; '.join(notes)), names, year=year, work_title=clean(work),
                            publisher=d.get('publisher', ''))
    return out


# ---------------------------------------------------------------- Ontario Historical Society

OHS_AWARDS = r'(Joseph Brant|Fred Landon|Alison Prentice|J\. ?J\. Talman|Donald Grant Creighton|Riddell|Huguenot Society of Canada)'


def ohs():
    body = 'Ontario Historical Society'
    url = 'https://www.ontariohistoricalsociety.ca/past-recipients'
    h = fetch(url)
    if not h:
        return []
    out, year, cycle = [], None, ''
    for l in lines(h):
        m = re.match(r'^(\d{4})-(\d{2}) Honours and Awards', l)
        if m:
            year, cycle = m.group(1), m.group(1) + '-' + m.group(2)
            continue
        m = re.match(r'^(?:The )?' + OHS_AWARDS + r' Award\s*(?:\(([^)]*)\))?\s*:\s*(.+)$', l)
        if not m or not year:
            continue
        award, qual, rest = m.groups()
        award = re.sub(r'J\. ?J\.', 'J.J.', award) + ' Award'
        notes = ['OHS awards cycle ' + cycle]
        if qual and re.search(r'(?i)honourable', qual):
            notes.append('honourable mention')
        elif qual:
            notes.append(qual.lower())
        honours = 'article' if award.startswith('Riddell') else 'book'
        field = {"Alison Prentice Award": "Ontario women's history", 'Riddell Award': 'Ontario history (article)'}.get(
            award, 'Ontario history')
        for part in re.split(r'\s*,\s+and\s+(?=(?:[A-Z][\w.\'’-]*\s+){2,4}for\s)', rest):
            pub = ''
            pm = re.search(r'\(([^()]*)\)\s*\.?$', part)
            if pm and honours == 'book' and not re.match(r'(?i)with ', pm.group(1)):
                pub = _pub_year(pm.group(1))
                part = clean(part[:pm.start()]).rstrip(' ,')
            nm = re.match(r'^([^,“"]+?)\s*,?\s+for\s+(.+)$', part)
            if nm and len(nm.group(1)) < 90:
                who, title = nm.groups()
            elif ',' in part:
                who, title = part.split(',', 1)
            else:
                continue
            title = clean(title).rstrip(' ,.')
            n = list(notes)
            if honours == 'article':
                am = re.match(r'^[“"](.+?)[,.]?[”"]\s*,?\s*(.*)$', title)
                if am:
                    title, venue = am.group(1).rstrip(','), re.sub(r'^(?:[Pp]ublished )?in\s+', '', am.group(2))
                    venue = re.sub(r'^Published in\s+', '', venue)
                    if venue:
                        n.append('published: ' + venue)
            elif not pub and re.search(r', [^,]*(Press|Publish|Society|Dundurn|House|Studio|Associates|Lorimer|Collins)[^,]*$',
                                       title):
                title, pub = title.rsplit(', ', 1)
            who = re.sub(r'\s*\(with ([^)]*)\)', r', \1', who)
            out += rows_for(base(body, 'CA', award, field, honours, url, '; '.join(n)),
                            split_names(who, r'\s*,\s*|\s+(?:and|&)\s+'), year=year, work_title=clean(title),
                            publisher=clean(pub))
    return out


# ---------------------------------------------------------------- Holberg Prize

def holberg():
    body = 'Holberg Prize'
    url = 'https://holbergprize.org/prizes-and-laureates/holbergprize/holberg-prize-laureates/'
    h = fetch(url)
    if not h:
        return []
    t = lines(h, main=False)
    out = []
    for k in range(1, len(t) - 1):
        if re.fullmatch(r'20\d\d', t[k]) and re.search(r'Holberg Prize', t[k + 1]) and t[k] in t[k + 1]:
            cit = t[k + 1]
            fm = re.search(r'\bfor (?:his|her|their) (.+?)\.?$', cit)
            note = ('for ' + fm.group(1)) if fm else ''
            field = 'history' if re.search(r'(?i)\bhistor', cit) else 'humanities and social sciences'
            out += rows_for(base(body, 'NO', 'Holberg Prize', field, 'career', url, note), [person(t[k - 1])],
                            year=t[k])
    return out


# ---------------------------------------------------------------- Balzan Prize

BALZAN_HIST = re.compile(r'(?i)histor|classic|medieval|middle ages|antiquit|ancient world|ancient near east|byzant|'
                         r'jewish studies|islamic|renaissance|archaeolog|prehistor|enlightenment|oriental studies|'
                         r'slavonic world|studies of antiquity|study of the ancient')


def balzan():
    body, out, seen = 'International Balzan Prize Foundation', [], set()
    for q in [''] + [str(y) for y in range(2021, 1955, -5)]:
        url = 'https://www.balzan.org/en/prizewinners' + ('?quinquennio=' + q if q else '')
        h = fetch(url)
        if not h:
            continue
        t = lines(h, main=False)
        for k, l in enumerate(t):
            m = re.match(r'^(\d{4}) Balzan Prize for (.+)$', l)
            if not m or not BALZAN_HIST.search(m.group(2)) or 'Humanity, Peace' in l:
                continue
            year, subject = m.groups()
            names_line = t[k - 1]
            key = (year, names_line, subject)
            if key in seen:
                continue
            seen.add(key)
            country = t[k - 3] if k >= 3 and not re.fullmatch(r'\d{4}', t[k - 3]) else ''
            note = ('country: ' + country) if country and len(country) < 40 else ''
            if '(ex aequo' in subject:
                note = clean(note + '; ex aequo').strip('; ')
                subject = clean(re.sub(r'\(ex aequo[^)]*\)', '', subject))
            out += rows_for(base(body, 'IT', 'Balzan Prize', subject, 'career', url, note),
                            split_names(names_line, r'\s+and\s+'), year=year)
    return out


# ---------------------------------------------------------------- Heineken Prize for History

def heineken():
    body, out = 'Royal Netherlands Academy of Arts and Sciences / Heineken Foundation', []
    for p in range(1, 15):
        url = 'https://www.heinekenprizes.org/list-of-laureates/' + (f'page/{p}/' if p > 1 else '')
        h = fetch(url)
        if not h:
            break
        t = lines(h, main=False)
        for k, l in enumerate(t):
            m = re.fullmatch(r'Dr A\.H\. Heineken Prize for History (\d{4})', l)
            if m:
                out += rows_for(base(body, 'NL', 'Dr A.H. Heineken Prize for History', 'history', 'career', url),
                                [person(t[k - 1])], year=m.group(1))
        if f'page/{p + 1}/' not in h:
            break
    return out


# ---------------------------------------------------------------- Dan David Prize

def dan_david():
    body, out = 'Dan David Prize', []
    for p in range(1, 10):
        url = 'https://dandavidprize.org/our-winners/' + (f'page/{p}/' if p > 1 else '')
        h = fetch(url)
        if not h:
            break
        t = lines(h, main=False)
        got = 0
        for k in range(1, len(t) - 2):
            if re.fullmatch(r'20\d\d', t[k]) and k + 2 < len(t) and t[k + 1] != 'Read More':
                rm = next((j for j in range(k + 1, min(len(t), k + 5)) if t[j] == 'Read More'), None)
                if rm is None or t[k - 1] in ('Year',) or re.fullmatch(r'20\d\d', t[k - 1]):
                    continue
                field = t[k + 1]
                aff = t[k + 2] if rm - k == 3 else ''
                out += rows_for(base(body, 'IL', 'Dan David Prize', field, 'career', url,
                                     ('affiliation: ' + aff) if aff else ''), [person(t[k - 1])], year=t[k])
                got += 1
        if not got or f'page/{p + 1}/' not in h:
            break
    for p in range(1, 15):
        url = 'https://dandavidprize.org/previous-laureates/' + (f'page/{p}/' if p > 1 else '')
        h = fetch(url)
        if not h:
            break
        t = lines(h, main=False)
        for k in range(1, len(t) - 1):
            if re.fullmatch(r'20\d\d', t[k]) and t[k + 1].startswith('Past:'):
                name = re.sub(r'\s*\(\d{4}\s*[-–]\s*\d{4}\)\s*$', '', t[k - 1])
                if ' ' not in name.strip():
                    continue                   # 2004 'Cities' laureates are cities, not people
                out += rows_for(base(body, 'IL', 'Dan David Prize', clean(t[k + 1][5:]), 'career', url,
                                     'Past time dimension (2001-2021 prize)'), [person(name)], year=t[k])
        if f'page/{p + 1}/' not in h:
            break
    return out


BODIES = [('Wolfson', wolfson), ('RHS books', rhs_books), ('RHS articles', rhs_articles),
          ('British Academy', british_academy), ('Cundill', cundill), ('IHAF', ihaf), ('Manitoba HS', mhs),
          ('Ontario HS', ohs), ('Holberg', holberg), ('Balzan', balzan), ('Heineken', heineken),
          ('Dan David', dan_david)]


def harvest():
    rows = []
    for name, fn in BODIES:
        try:
            got = fn()
        except Exception as e:  # one body failing must not stop the others
            print(name, 'FAILED', type(e).__name__, e, file=sys.stderr)
            got = []
        rows += [{c: clean(str(r.get(c, ''))) for c in COLS} for r in got if clean(r.get('winner', ''))]
    return rows


if __name__ == '__main__':
    rows = harvest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    c = Counter(r['body'] for r in rows)
    for b, n in c.most_common():
        ys = sorted(r['year'] for r in rows if r['body'] == b)
        print(f'{n:5d}  {b}  ({ys[0]}-{ys[-1]})')
    print(len(rows), 'rows ->', OUT.relative_to(ROOT))
