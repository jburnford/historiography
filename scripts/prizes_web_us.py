"""Prize-winner lists of United States history bodies, read from the awarding bodies' own public pages (2026-11-12).

One row per (prize, year, winner person, work); rows go to build/prizes-2026-11-12/rows-web-us.jsonl for the prize
harvest (scripts/prizes_harvest.py) and the linker. Every page is fetched with scripts/prizes_fetch.py (robots.txt
obeyed, 1.2 s per host, raw page cached under build/prizes-2026-11-12/raw/, refusals logged and never worked around).

Bodies and pages read:
  Bancroft Prize (Columbia University Libraries)
      https://library.columbia.edu/about/awards/bancroft/previous_awards.html                         1948-
  Society for the History of Technology (SHOT)
      https://www.historyoftechnology.org/about-us/awards-prizes-and-grants/<prize>/   Edelstein (Dexter), Usher,
      Leonardo da Vinci Medal, Robinson, Trescott, Finn IEEE, Ferguson, Levinson, Hacker, Race and Histories of
      Technologies (page 3303-2). Dibner Award (museum exhibits, no persons) is skipped.
  American Society for Environmental History (ASEH)
      https://aseh.org/past-recipients     Marsh, Hamilton, Leopold-Hidy, Carson, Distinguished Scholar,
      Distinguished Career in Public Environmental History (fellowships, service and outreach awards skipped)
  Berkshire Conference of Women Historians
      https://berksconference.org/annual-prizes/book-prize-winners/  and  .../annual-prizes/article-prize/
  Western History Association (WHA)
      https://westernhistory.org/awards/<prize>  (book, article, dissertation prizes and the Award of Merit;
      fellowships, scholarships, student, teaching and public-history awards skipped)
  Conference on Latin American History (CLAH)
      https://clahistorians.org/prizes-and-awards/prizes-and-awards-descriptions/<prize>/
  African Studies Association (ASA)
      https://africanstudies.org/awards-prizes/{asa-best-book-prize (Herskovits), bethwell-a-ogot-book-prize,
      distinguished-africanist-award}/
  Toynbee Prize Foundation
      https://toynbeeprize.org/the-prize/

Refused on 2026-11-12 (HTTP 403 or robots.txt forbidden; recorded in fetch-log.jsonl, not worked around):
American Historical Association (historians.org), Organization of American Historians (oah.org), Pulitzer Prizes
(pulitzer.org), Library of Congress Kluge Prize (loc.gov), History of Science Society (hssonline.org), Association
for Asian Studies (asianstudies.org, robots.txt 403).

Honourable mentions are kept with note 'honorable mention'; finalists and runners-up are skipped. Printed
affiliations go to note as 'affiliation: ...'; an article's printed citation (journal, volume, pages) goes to note as
'venue: ...' (publisher stays '' for articles); a dissertation's university is an affiliation. Career awards
(medals, distinguished-scholar awards, the Toynbee Prize) have no work_title.

Known weaknesses: free-text lines are parsed by pattern (year header, 'Names, Title (Publisher, year)' or
'Names, “Title,” Venue'); odd lines are skipped rather than guessed. Typos on the pages are kept as printed
('T he Charisma Machine', 'M ilk and Honey'). The WHA Award of Merit page has a garbled year header '2022012'; its
three names are skipped, not guessed. The fetcher's challenge heuristic flagged some small aseh.org and
westernhistory.org pages (a login widget mentions captcha); within one process that host is then not asked again,
so a run with an empty raw cache may return fewer WHA/ASEH rows.

    python3 scripts/prizes_web_us.py      # writes build/prizes-2026-11-12/rows-web-us.jsonl, prints counts per body
"""
import html as H
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from prizes_fetch import fetch, text_of  # noqa: E402
from prizes_harvest import prize_id  # noqa: E402

OUT = ROOT / 'build/prizes-2026-11-12/rows-web-us.jsonl'
COLS = ['prize_id', 'prize', 'body', 'body_country', 'field', 'honours', 'year', 'winner', 'co_winners', 'work_title',
        'publisher', 'wd_prize', 'wd_person', 'wd_work', 'person_ids', 'work_ids', 'source_url', 'source_kind', 'note']

AFFIL = re.compile(r'(?i)universit|college|institut|school|museum|academy|library|polytechnic|\bUC[LS]?\b|UCLA|MIT\b|'
                   r'KTH|ETH|CNRS|centre|center|press|society|foundation|state|politécnic|nacional|hospital|senior editor')
PARTICLES = {'de', 'del', 'della', 'da', 'das', 'do', 'dos', 'van', 'von', 'der', 'den', 'la', 'le', 'y', 'e', 'di',
             'du', 'ten', 'ter', 'al', 'el', 'bin', 'ibn', 'st.', "d'"}
FUNCTION_WORDS = {'when', 'to', 'of', 'the', 'in', 'on', 'for', 'at', 'with', 'from', 'by', 'is', 'are', 'my', 'our',
                  'their', 'his', 'her', 'into', 'how', 'why', 'what', 'who', 'where', 'a', 'an', 'not', 'no', 'as',
                  'history', 'histories', 'war', 'world', 'american', 'america', 'new', 'empire', 'nation', 'story',
                  'life', 'lives', 'people', 'land', 'city', 'press', 'university', 'books', 'prize', 'award'}
SUFFIX = re.compile(r'^(jr\.?|sr\.?|ii|iii|iv|phd|s\.\s?j\.?)$', re.I)
SKIP_LINE = re.compile(r'(?i)^(no award|not awarded|not presented|prize not awarded|no prize|due to|the \d{4} .* (was )?not'
                       r'|none\b|no recipient)')
YEAR = re.compile(r'^(1[89]\d\d|20[0-3]\d)$')
STRONG_AFFIL = re.compile(r'(?i)universit|college|institut|school|museum|academy|library|polytechnic|\bpress\b|'
                          r'\bState\b|\bUCLA\b|\bMIT\b|\bKTH\b|\bETH\b|CNRS|centre|center|nacional|senior editor|'
                          r'department|dept\b|laborator|observatory|hospital|smithsonian|ministry')


def clean(s):
    s = H.unescape(s or '').replace('\xa0', ' ')
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s+([,.;:)])', r'\1', s)
    s = re.sub(r'([(])\s+', r'\1', s)
    return s.strip()


def is_name(tok):
    """A printed person name: 2-7 words, capitalised (particles allowed), no digits, no title words."""
    tok = tok.strip()
    if not tok or re.search(r'\d|[:?!“”"]', tok) or len(tok) > 60:
        return False
    words = tok.split()
    if not 2 <= len(words) <= 7:
        return False
    if words[0].lower() in ('the', 'a', 'an', 'for', 'in', 'on', 'of', 'two', 'co-winners'):
        return False
    if any(w.lower() in FUNCTION_WORDS for w in words):   # 'When Jesus Came', 'To Love'
        return False
    caps = 0
    for w in words:
        wl = w.lower()
        if wl in PARTICLES or SUFFIX.match(w.strip(',')):
            continue
        if not (w[0].isupper() or w[0] in "'’" or re.match(r"^(d|l|o)['’][A-Z]", w)):
            return False
        caps += 1
    return caps >= 2 or (caps >= 1 and len(words) >= 2 and words[0][0].isupper())


def split_names(s):
    """'A, B, and C' / 'A and B' / 'A & B' -> [A, B, C]; 'Allen and Barbara Isaacman' -> two full names."""
    s = clean(s).strip(' ,;:')
    s = re.sub(r'(?i)\b(eds?\.|editors?|edited by)\s*', '', s).strip(' ,')
    s = re.sub(r'(?:(?<=^)|(?<=,\s)|(?<=and\s))(Dr|Prof|Professor)\.?\s+', '', s)
    m = re.fullmatch(r"([A-Z][\w'’-]+),\s+([A-Z][\w.' -]+?)", s)   # inverted 'Walker, Brett L.'
    if m and len(m.group(2).split()) <= 3 and not SUFFIX.match(m.group(2).rstrip('.')) and \
            re.search(r'\b[A-Z]\.', m.group(2)):
        s = m.group(2) + ' ' + m.group(1)
    parts = [p.strip() for p in re.split(r'\s*,\s*and\s+|\s*,\s*&\s*|\s*,\s*|\s+and\s+|\s*&\s*', s) if p.strip()]
    out = []
    for p in parts:
        if SUFFIX.match(p.rstrip('.')) and out:
            out[-1] = out[-1] + ', ' + p
        else:
            out.append(p)
    # 'Paul and Laura Bohannan': a single first name followed by a full name with the shared surname
    for i in range(len(out) - 1):
        if len(out[i].split()) == 1 and len(out[i + 1].split()) >= 2 and \
                re.search(r'\b' + re.escape(out[i]) + r'\s+(and|&)\s', s):
            out[i] = out[i] + ' ' + out[i + 1].split()[-1]
    return out


def split_name_affil(s):
    """'Name (Aff)' / 'Name, Aff' / 'Name (Aff) and Name2 (Aff2)' -> (names, affiliations)."""
    s = clean(s).strip(' ,;:')
    s = re.sub(r'^(?i:for)\b:?\s*', '', s)
    affs = re.findall(r'\(([^()]*)\)', s)
    s = re.sub(r'\s*\([^()]*\)', '', s).strip(' ,')
    toks = [t.strip() for t in s.split(',')]
    names_part, more = [], []
    for t in toks:
        if names_part and (STRONG_AFFIL.search(t) or AFFIL.search(t) and not is_name(re.sub(r'^(and|&)\s+', '', t))):
            more.append(t)
        elif more:
            more.append(t)
        else:
            names_part.append(t)
    names = split_names(', '.join(names_part))
    if more:
        affs.append(', '.join(more))
    return names, [a for a in affs if a]


def take_paren_tail(s):
    """Split a trailing balanced '( ... )' off the string -> (head, inside) or (s, '')."""
    t = s.rstrip(' .;')
    if not t.endswith(')'):
        return s, ''
    depth = 0
    for i in range(len(t) - 1, -1, -1):
        if t[i] == ')':
            depth += 1
        elif t[i] == '(':
            depth -= 1
            if depth == 0:
                return t[:i].rstrip(' ,'), t[i + 1:-1].strip()
    return s, ''


def publisher_of(inside):
    p = inside
    p = re.split(r'(?i)\.\s*first published', p)[0]
    p = re.sub(r',?\s*(fall |spring )?(1[89]|20)\d\d\s*$', '', p.strip()).strip(' ,.')
    p = re.sub(r'\s+(1[89]|20)\d\d$', '', p).strip(' ,.')
    m = re.match(r"^[A-Z][A-Za-z .,'-]{1,40}?:\s*(.+)$", p)  # 'New Haven: Yale University Press'
    if m and not re.search(r'(?i)press|books|universit', p.split(':')[0]):
        p = m.group(1)
    return p.strip(' ,.')


def parse_book(entry):
    """'Names, Title (Publisher, year)' or 'Names for Title (Publisher)' -> (names, title, publisher, affs) or None."""
    e = clean(entry)
    e = re.sub(r'^(?i:two recipients|co-winners|winner)\s*:\s*', '', e)
    head, inside = take_paren_tail(e)
    pub = publisher_of(inside) if inside and (re.search(r'(?i)press|books|universit|publish|editions|knopf|norton|'
                                                         r'macmillan|harper|brill|routledge|heinemann|praeger|penguin|'
                                                         r'random house|basic|wiley|houghton|little, brown|scribner|'
                                                         r'viking|holt|ohio|currey|zed|verso|unwin|collins|\d{4}', inside)) else ''
    if not pub:
        head = e if not re.fullmatch(r'(1[89]|20)\d\d', inside or '') else head
    m = re.match(r'^(.+?)\s+for\s+(.+)$', head)
    if m and (',' not in m.group(1) or re.search(r'\s(and|&)\s', m.group(1))) and \
            all(is_name(n) for n in split_names(m.group(1))):
        names, title = split_names(m.group(1)), m.group(2)
        affs = []
    else:
        toks = [t.strip() for t in head.split(',')]
        names_tok, i = [], 0
        while i < len(toks):
            t = re.sub(r'^(and|&)\s+', '', toks[i])
            if SUFFIX.match(t.rstrip('.')) and names_tok:
                names_tok[-1] += ', ' + t
            elif ' and ' in t and all(is_name(x) or len(x.split()) == 1 for x in split_names(t)) and \
                    any(is_name(x) for x in split_names(t)):
                names_tok.append(t)
            elif is_name(t) and not (i + 1 == len(toks)) and (
                    not names_tok or re.search(r'\b[A-Z]\.', t) or re.match(r'^(and|&)\s', toks[i]) or
                    any(re.match(r'^(and|&)\s', x) and is_name(x[4:].strip()) for x in toks[i + 1:i + 3])):
                names_tok.append(t)
            elif re.fullmatch(r'(?i)eds?\.?', t) and names_tok:
                pass
            else:
                break
            i += 1
        while len(names_tok) > 1 and i < len(toks) and re.match(r'^[\d(a-z]', toks[i]) and not re.match(r'^(eds?\.|editors?)', toks[i]) and \
                not re.match(r'^(and|&)\s', names_tok[-1]):
            names_tok.pop()
            i -= 1
        if not names_tok or i >= len(toks):
            return None
        names = split_names(', '.join(names_tok))
        title = ', '.join(toks[i:])
        affs = []
    title = re.sub(r'^G:\s*', '', clean(title)).strip(' ,.')
    # 'Name, Editor and University of Oklahoma Press for Title' / 'Name, ed. Title'
    title = re.sub(r'^(?:eds?\.|editors?)(?:,?\s+and\s+.+?)?,?\s+for\s+|^(?:eds?\.|editors?)\s+', '', title, flags=re.I)
    title = title.strip('“”"')
    if not title or not names:
        return None
    return names, title, pub, affs


OPENQ = '“"‘'
CLOSEQ = {'“': '”', '"': '"', '‘': '’'}


def parse_article(entry):
    """'Names[ (Aff)][, Aff], “Title,” Venue' -> (names, title, venue, affs) or None."""
    e = clean(entry)
    if '|||' in e:   # 'Name, Affiliation' line followed by a title line
        who, rest = e.split('|||', 1)
        rest = re.sub(r'^(?i:for)\s*:?\s*', '', rest.strip())
        names, affs = split_name_affil(who)
        if rest[:1] in OPENQ:
            q = rest[0]
            rest = rest[1:]
        else:
            q = '“'
        j = rest.find(CLOSEQ[q]) if CLOSEQ[q] in rest else rest.find('”')
        title, venue = (rest[:j], rest[j + 1:]) if j > 0 else (rest, '')
        return names, title.strip(' ,.'), venue.strip(' ,.'), affs
    # the first opening quote that starts a title (after a comma, colon, space or start)
    m = re.search(r'(^|[\s,:])([“"])', e) or re.search(r'(,)([”’])(?=[A-Z‘])', e)
    sq = None
    if not m:
        sq = re.search(r"(^|,\s*)'(.+?)'\s", e)
        if not sq:
            return None
        who, title, venue = e[:sq.start()], sq.group(2), e[sq.end():]
    else:
        who = e[:m.start(2)]
        rest = e[m.end(2):]
        q = m.group(2)
        closers = ['”', '"', '“'] if q in '“”’' else ['"', '”', '“']
        js = [rest.find(c) for c in closers if rest.find(c) > 0]
        j = min(js) if js else -1
        mc = re.search(r'[,.?!]\s*[”"]', rest)   # the closing quote of a title usually follows its comma
        if mc and j >= 0 and mc.end() - 1 > j:
            j = mc.end() - 1
        title, venue = (rest[:j], rest[j + 1:]) if j > 0 else (rest, '')
    who = who.strip(' ,:')
    who = re.sub(r'(?i)\s+for( her| his| their)?( article)?$', '', who)
    names, affs = split_name_affil(who)
    if not names or not all(is_name(n) for n in names):
        return None
    title = clean(title).strip(' ,.')
    return names, title, clean(venue).strip(' ,.;'), affs


def row(body, prize, field, honours, year, winner, co=(), title='', publisher='', url='', note='', affs=()):
    notes = [note] if note else []
    for a in affs:
        a = clean(a)
        if a:
            notes.append('affiliation: ' + a)
    return {'prize_id': prize_id(body, prize), 'prize': prize, 'body': body, 'body_country': 'US', 'field': field,
            'honours': honours, 'year': str(year), 'winner': clean(winner).strip(' ,;'), 'co_winners': '; '.join(clean(c) for c in co), 'work_title': clean(title),
            'publisher': clean(publisher), 'wd_prize': '', 'wd_person': '', 'wd_work': '', 'person_ids': '',
            'work_ids': '', 'source_url': url, 'source_kind': 'awarding-body', 'note': '; '.join(notes)}


def rows_for(body, prize, field, honours, year, parsed, url, note=''):
    names, title, pub, affs = parsed
    out = []
    for i, n in enumerate(names):
        a = affs[i:i + 1] if len(affs) == len(names) else affs
        out.append(row(body, prize, field, honours, year, n, [x for x in names if x != n], title, pub, url, note, a))
    return out


def lines_of(url, main=True):
    h = fetch(url)
    if h is None:
        return None
    # inline tags carry no word break ('<span>P</span><span>eter Blodget</span>'): drop them before text_of
    h = re.sub(r'(?i)</?(span|font|em|strong|b|i|u|sup|sub)\b[^>]*>', '', h)
    return text_of(h, main=main).split('\n')


def generic_list(body, prize, field, honours, url, lines, start_pat, stop_pat=r'^(Copyright|BACKGROUND|©|Donations)',
                 kind=None):
    """Year-headed list: '2024' line (or '2024 | entry' / '2024 entry') then entries; status lines
    (Honorable Mention, Co-Winners, Finalists) switch the state until the next year."""
    kind = kind or honours
    out, year, state, started = [], '', 'win', False
    i = 0
    L = [clean(x) for x in lines]
    # 'entry (Spring 2015) 2014 | next entry': two year-entries run together on one line
    L = [y.strip() for x in L for y in re.sub(r'\s+((?:19|20)\d\d\s*\|\s)', r'\n\1', x).split('\n')]
    L = [y.strip() for x in L for y in re.split(r'\s*\|\s*and\s*\|\s*', x)]   # WHA: 'entry |and| entry'
    if kind == 'career':   # '1991 Carroll W. Pursell1990 Edwin Layton, Jr.' (two entries run together)
        L = [y for x in L for y in re.sub(r'(?<=[a-z.])((?:19|20)\d\d )', r'\n\1', x).split('\n')]
    while i < len(L):
        ln = L[i]
        i += 1
        if not started:
            if re.search(start_pat, ln):
                started = True
            continue
        if re.search(stop_pat, ln):
            break
        m = re.match(r'^((?:1[89]|20)\d\d)(?:\s*[|:–-]\s*|\s+)(.+)$', ln)
        if YEAR.match(ln):
            year, state = ln, 'win'
            continue
        if re.fullmatch(r'\d{5,}', ln):   # a garbled year header ('2022012'): skip its entries, do not guess
            year = ''
            continue
        if m and not re.match(r'^\d{4}\s*[-–]\s*\d', ln):
            year, state, ln = m.group(1), 'win', m.group(2).strip()
        if not year or not ln:
            continue
        low = ln.lower().rstrip(':')
        if re.match(r'^(honou?rable mentions?|honou?rable mention)\b', low):
            state = 'hm'
            ln = re.sub(r'(?i)^honou?rable mentions?\s*:?\s*', '', ln)
            if not ln:
                continue
        if re.match(r'^(finalists?|runners?-up)\b', low):
            state = 'skip'
            continue
        if re.match(r'^(co-?winners?|winners?|two recipients)\s*:?$', low) or low == 'and':
            if state != 'hm':
                state = 'win'
            continue
        if state == 'skip' or SKIP_LINE.match(ln):
            continue
        # joins: an opened quote not closed, or a name-and-affiliation line followed by its title line
        if kind in ('article', 'dissertation', 'other'):
            if ln.count('“') > ln.count('”') + ln.count('"') and i < len(L) and not YEAR.match(L[i]) and \
                    not re.match(r'^(?:19|20)\d\d\b', L[i]):
                ln = ln + ' ' + L[i]
                i += 1
            elif not any(q in ln for q in '“"”') and i < len(L) and not YEAR.match(L[i]) and \
                    ('”' in L[i] or re.match(r'(?i)^for\b', L[i])) and kind != 'career':
                ln = ln + ' ||| ' + L[i]
                i += 1
        elif kind == 'book':
            if '(' not in ln and i < len(L) and L[i].startswith('(') and not YEAR.match(L[i]):
                ln = ln + ' ' + L[i]
                i += 1
            elif ln.count('(') > ln.count(')') and i < len(L):
                ln = ln + ' ' + L[i]
                i += 1
            elif '(' not in ln and i < len(L) and re.search(r'\)\.?$', L[i]) and not YEAR.match(L[i]) and \
                    not re.match(r'^[A-Z][^,]{3,40},', L[i]):
                ln = ln + ' ' + L[i]
                i += 1
        note = 'honorable mention' if state == 'hm' else ''
        # two winning works on one line: '... (Press, 1995); and Name, Title (...)' -- split only when every
        # piece parses on its own (so 'Name (Affiliation) and Name2 (Affiliation)' stays one entry)
        pieces = [x for x in re.split(r'(?<=\))\s*[;,]?\s+and\s+(?=[A-Z])', ln) if x.strip()]
        got = []
        if len(pieces) > 1:
            for piece in pieces:
                r = parse_piece(body, prize, field, honours, year, piece, url, note, kind)
                if not r or not r[0]['work_title'] and kind != 'career':
                    got = None
                    break
                got += r
        if not got:
            got = parse_piece(body, prize, field, honours, year, ln, url, note, kind)
        out.extend(got)
    return out


def parse_piece(body, prize, field, honours, year, piece, url, note, kind):
    if kind == 'career':
        piece = re.sub(r'\s+["“][^"”]+["”]\s+', ' ', piece)   # nickname: Michael "Cowboy Mike" Searles
        piece = re.sub(r'(?i)^(co-?awards?|co-?winners?)\s*:\s*', '', piece)
        names, affs = split_name_affil(piece)
        names = [n for n in names if is_name(n)]
        return [row(body, prize, field, honours, year, n, [x for x in names if x != n], url=url, note=note,
                    affs=affs if len(names) == 1 else ()) for n in names]
    parsed = None
    as_article = False
    if kind in ('article', 'dissertation', 'other') or (kind == 'book' and re.match(r'^[^“(]{3,80},\s*“[^”]+,?”', piece)):
        parsed = parse_article(piece)
        as_article = bool(parsed)
        parsed = parsed or parse_book(piece)
    else:
        parsed = parse_book(piece)
        if not parsed:
            parsed = parse_article(piece)
            as_article = bool(parsed)
    if not parsed:
        return []
    names, title, pub, affs = parsed
    names = [n for n in names if is_name(n)]
    if not names or len(title) < 3:
        return []
    notes = [note] if note else []
    if as_article and pub:
        # an article's printed citation (journal, volume, pages) or a dissertation's university
        if kind == 'dissertation' and STRONG_AFFIL.search(pub) and len(pub) < 90:
            affs = list(affs) + [re.sub(r',?\s*(1[89]|20)\d\d$', '', pub)]
        else:
            notes.append('venue: ' + pub)
        pub = ''
    if title.startswith('“') and '”' not in title:
        title = title[1:].strip()
    if re.match(r'(?i)^\(?posthumous\)?,?\s+', title):
        title = re.sub(r'(?i)^\(?posthumous\)?,?\s+', '', title)
        notes.append('posthumous')
    if re.match(r'^[a-z]', title) and ':' not in title:   # a description, not a printed title ('the bibliography of ...')
        notes.append('work: ' + title)
        title = ''
    return rows_for(body, prize, field, honours, year, (names, title, pub, affs), url, '; '.join(notes))


# ---------------------------------------------------------------- bodies

def bancroft():
    url = 'https://library.columbia.edu/about/awards/bancroft/previous_awards.html'
    L = lines_of(url)
    if L is None:
        return []
    body, prize = 'Columbia University', 'Bancroft Prize'
    out, year, i = [], '', 0
    L = [clean(x) for x in L]
    started = False
    while i < len(L):
        ln = L[i]
        if YEAR.match(ln):
            year, started = ln, True
            i += 1
            continue
        if not started:
            i += 1
            continue
        if ln.startswith('Columbia University Libraries') or ln.startswith('535 West'):
            break
        if i + 1 < len(L) and re.match(r'(?i)^by\s', L[i + 1]):
            title = ln
            names = split_names(re.sub(r'(?i)^by\s+', '', L[i + 1]))
            pub = ''
            j = i + 2
            if j < len(L) and re.match(r'(?i)^published by\s', L[j]):
                pub = re.sub(r'(?i)^published by\s+(the\s+)?', '', L[j])
                pub = re.sub(r'\s*\((1[89]|20)\d\d\)\s*$', '', pub).strip()
                j += 1
            for n in names:
                out.append(row(body, prize, 'American history', 'book', year, n, [x for x in names if x != n],
                               title, pub, url))
            i = j
            continue
        i += 1
    return out


SHOT_BASE = 'https://www.historyoftechnology.org/about-us/awards-prizes-and-grants/'
SHOT_PRIZES = [  # slug, prize name, honours, kind, note
    ('sidney-edelstein-prize', 'Sidney Edelstein Prize', 'book', 'book', ''),
    ('abbot-payson-usher-prize', 'Abbott Payson Usher Prize', 'article', 'article', ''),
    ('the-leonardo-da-vinci-medal', 'Leonardo da Vinci Medal', 'career', 'career', ''),
    ('joan-cahalin-robinson-prize', 'Joan Cahalin Robinson Prize', 'other', 'article',
     'first paper presented at the SHOT annual meeting'),
    ('martha-trescott-prize', 'Martha Trescott Prize', 'article', 'article', ''),
    ('the-bernard-s-finn-ieee-history-prize', 'Bernard S. Finn IEEE History Prize', 'article', 'article', ''),
    ('the-ferguson-prize', 'Ferguson Prize', 'other', 'book', 'reference work, edition or bibliography'),
    ('the-levinson-prize', 'Levinson Prize', 'article', 'article', 'unpublished essay'),
    ('the-sally-hacker-prize', 'Sally Hacker Prize', 'book', 'book', ''),
    ('3303-2', 'SHOT-REDI Race and Histories of Technologies Prize', 'article', 'article', ''),
]


def shot():
    body, out = 'Society for the History of Technology', []
    for slug, prize, honours, kind, note in SHOT_PRIZES:
        url = SHOT_BASE + slug + '/'
        L = lines_of(url, main=False)
        if L is None:
            continue
        rows = generic_list(body, prize, 'history of technology', honours, url, L, r'^Recipients',
                            stop_pat=r'^(Copyright|\*Formerly|Special retrospective)', kind=kind)
        for r in rows:
            if note:
                r['note'] = '; '.join(x for x in (note, r['note']) if x)
        out += rows
    return out


def aseh():
    url = 'https://aseh.org/past-recipients'
    L = lines_of(url, main=False)
    if L is None:
        return []
    body, field = 'American Society for Environmental History', 'environmental history'
    sections = {  # header line -> (prize, honours, kind)
        'Distinguished Scholar Award': ('Distinguished Scholar Award', 'career', 'career'),
        'Distinguished Career in Public Environmental History Award':
            ('Distinguished Career in Public Environmental History Award', 'career', 'career'),
        'George Perkins Marsh Prize': ('George Perkins Marsh Prize', 'book', 'book'),
        'Alice Hamilton Prize': ('Alice Hamilton Prize', 'article', 'article'),
        'Leopold-Hidy Prize': ('Leopold-Hidy Prize', 'article', 'article'),
        'Rachel Carson Prize': ('Rachel Carson Prize', 'dissertation', 'dissertation'),
    }
    stops = {'Lisa Mighetto Distinguished Service Award', 'Public Outreach Project Award', 'Samuel Hays Fellowship',
             'Hal Rothman Dissertation Fellowship', 'J. Donald Hughes Graduate Research Fellowships',
             'Equity Graduate Student Fellowship', 'ASEH-Newberry Library Fellowships'}
    L = [clean(x) for x in L]
    try:
        start = L.index('Past Award Recipients')
    except ValueError:
        return []
    blocks, cur = [], None
    for ln in L[start + 1:]:
        if ln in sections or ln in stops:
            cur = [ln, []] if ln in sections else None
            if cur:
                blocks.append(cur)
            continue
        if ln.startswith('©') or ln.startswith('find us'):
            break
        if cur:
            # 'Year and Recipient' / '(best book)' captions; two entries run together on one line
            if re.match(r'^(Year( and)? Recipient|\()', ln):
                continue
            for part in re.split(r'(?<=[.)”"])\s+(?=(?:19|20)\d\d\s+[A-Z])', ln):
                cur[1].append(part)
    out = []
    for head, lines in blocks:
        prize, honours, kind = sections[head]
        lines = [re.sub(r'^(\d{4}) Recipi (?=[A-Z])', r'\1 ', x) for x in lines]
        rows = generic_list(body, prize, field, honours, url, ['START'] + lines, r'^START$', kind=kind)
        for r in rows:
            r['note'] = re.sub(r'\[award presented in (\d{4})\]', r'award presented in \1', r['note'])
            r['winner'] = re.sub(r'\s*\[award presented in \d{4}\]', '', r['winner'])
            if '[award presented in' in r['work_title']:
                r['work_title'] = ''
        out += rows
    return out


def aseh_marsh_fix(out):
    """Marsh lines read 'Name, Title . Publisher.' (no parentheses): split the publisher off the title."""
    for r in out:
        if r['prize'] == 'George Perkins Marsh Prize' and not r['publisher']:
            m = re.match(r'^(.*?\S)\s*[.,]\s+((?:New Haven:\s*)?[A-Z][^.]*(?:Press|Books|Norton|Company|Unwin|'
                         r'Collins|Inc)\.?)\s*$', r['work_title'])
            if m:
                r['work_title'], r['publisher'] = m.group(1), m.group(2).strip(' .')
                r['publisher'] = re.sub(r'^New Haven:\s*', '', r['publisher'])
            m = re.match(r'^(.*?)\s*\(\s*(.+?)\)\.?$', r['work_title'])
            if m and re.search(r'(?i)press', m.group(2)):
                r['work_title'], r['publisher'] = m.group(1), m.group(2)
        if r['prize'] in ('Alice Hamilton Prize', 'Leopold-Hidy Prize', 'Rachel Carson Prize'):
            r['publisher'] = ''
        if r['prize'] == 'Leopold-Hidy Prize':
            r['note'] = '; '.join(x for x in ('journal: Environmental History', r['note']) if x)
    return out


def berks():
    body = 'Berkshire Conference of Women Historians'
    out = []
    pages = [('https://berksconference.org/annual-prizes/book-prize-winners/', 'book'),
             ('https://berksconference.org/annual-prizes/article-prize/', 'article')]
    for url, honours in pages:
        h = fetch(url)
        if h is None:
            continue
        toks = re.findall(r'(?s)<div class="item year">\s*(\d{4})\s*</div>|<div\s+class="item content"\s+'
                          r'data-type="([^"]*)"|<h[2-4][^>]*>(.*?)</h[2-4]>|<p>(.*?)</p>', h)
        year, cat, state = '', '', 'win'
        for y, dt, hh, p in toks:
            if y:
                year, state = y, 'win'
                continue
            if dt:
                cat, state = clean(dt), 'win'
                continue
            if hh:
                t = clean(re.sub(r'<[^>]+>', '', hh))
                tl = t.lower()
                if 'honorable mention' in tl:
                    state = 'hm'
                elif re.search(r'finalist|runner', tl):
                    state = 'skip'
                elif re.search(r'co-winner', tl):
                    state = 'win'
                elif re.search(r'no award', tl):
                    state = 'skip'
                elif tl.startswith(('first book', 'history of women', 'any field')):
                    cat, state = t, 'win'
                continue
            if not year or state == 'skip' or '<strong' not in p:
                continue
            note = 'honorable mention' if state == 'hm' else ''
            if honours == 'book':
                sm = re.search(r'(?s)<strong\b[^>]*>(.*?)</strong\s*>', p)
                em = re.search(r'(?s)<em\b[^>]*>(.*?)</em\s*>', p)
                names = split_names(clean(re.sub(r'<[^>]+>', '', sm.group(1))).strip(' ,')) if sm else []
                title = clean(re.sub(r'<[^>]+>', '', em.group(1))) if em else ''
                tail = clean(re.sub(r'<[^>]+>', '', p[em.end():])) if em else ''
                _, inside = take_paren_tail(tail)
                pub = publisher_of(inside) if inside else ''
                if not names or not title:
                    continue
                gws = 'Non-Women' not in cat
                prize = 'Berkshire Conference First Book Prize' + (
                    ' (Women/Gender/Sexuality)' if gws else ' (Non-Women/Gender/Sexuality)')
                field = 'women and gender' if gws else 'history'
                out += rows_for(body, prize, field, 'book', year, (names, title, pub, []), url, note)
            else:
                parsed = parse_article(clean(re.sub(r'<[^>]+>', '', p)))
                if not parsed:
                    continue
                gws = 'women' in cat.lower()
                prize = 'Berkshire Conference Article Prize' + (
                    ' (History of Women, Gender, and/or Sexuality)' if gws else ' (Any Field of History)')
                field = 'women and gender' if gws else 'history'
                names, title, venue, affs = parsed
                out += rows_for(body, prize, field, 'article', year, (names, title, '', affs), url, note)
    return out


WHA_PRIZES = [  # slug, prize, honours, kind
    ('awards/caughey', 'Caughey Western History Prize', 'book', 'book'),
    ('awards/athearn', 'Robert G. Athearn Award', 'book', 'book'),
    ('awards/ewers', 'John C. Ewers Award', 'book', 'book'),
    ('awards/owens', 'Sally and Ken Owens Award', 'book', 'book'),
    ('awards/patersonkerr', 'Joan Paterson Kerr Award', 'book', 'book'),
    ('awards/rothman', 'Hal K. Rothman Book Prize', 'book', 'book'),
    ('awards/turrentine-jackson', 'W. Turrentine Jackson Prize', 'book', 'book'),
    ('awards/utley', 'Robert M. Utley Award', 'book', 'book'),
    ('awards/weber', 'David J. Weber Prize', 'book', 'book'),
    ('fixicoaward', 'Donald L. Fixico Award', 'book', 'book'),
    ('awards/smith', 'Dwight L. Smith (ABC-CLIO) Award', 'book', 'book'),
    ('awards/arrington-prucha', 'Arrington-Prucha Prize', 'article', 'article'),
    ('awards/billington', 'Ray Allen Billington Prize', 'article', 'article'),
    ('awards/bolton-cutter', 'Bolton-Cutter Award', 'article', 'article'),
    ('awards/fireman', 'Bert M. Fireman and Janet Fireman Award', 'article', 'article'),
    ('awards/gibson', 'Arrell M. Gibson Award', 'article', 'article'),
    ('awards/jensen-miller', 'Jensen-Miller Prize', 'article', 'article'),
    ('awards/malone', 'Michael P. Malone Award', 'article', 'article'),
    ('awards/winther', 'Oscar O. Winther Award', 'article', 'article'),
    ('VickiRuizAward', 'Vicki L. Ruiz Award', 'article', 'article'),
    ('awards/dissertation', 'Purrington/White Dissertation Prize', 'dissertation', 'dissertation'),
    ('awards/merit', 'Gordon Bakken Award of Merit', 'career', 'career'),
]


def wha():
    body, out = 'Western History Association', []
    for slug, prize, honours, kind in WHA_PRIZES:
        url = 'https://westernhistory.org/' + slug
        L = lines_of(url, main=False)
        if L is None:
            continue
        rows = []
        if prize == 'Caughey Western History Prize':
            # before 1993 the prize was for a "distinguished body of writing": career rows
            L2 = [clean(x) for x in L]
            try:
                cut = next(i for i, x in enumerate(L2) if x.startswith('Prior to 1993'))
            except StopIteration:
                cut = None
            if cut:
                rows = generic_list(body, prize, 'Western American history', honours, url, L2[:cut],
                                    r'^PAST RECIPIENTS', kind=kind)
                end = next((i for i in range(cut + 1, len(L2)) if not re.match(r'^\d{4}\s*\|', L2[i])), len(L2))
                old = generic_list(body, 'Western History Association Prize', 'Western American history', 'career',
                                   url, ['START'] + L2[cut + 1:end], r'^START$', kind='career')
                old = [r for r in old if r['year'] < '1993']
                for r in old:
                    r['note'] = 'distinguished body of writing (forerunner of the Caughey Prize)'
                rows += old
        else:
            rows = generic_list(body, prize, 'Western American history', honours, url, L, r'^PAST RECIPIENTS',
                                stop_pat=r'^(BACKGROUND|About Us$|Copyright|©)', kind=kind)
        out += rows
    return out


CLAH_BASE = 'https://clahistorians.org/prizes-and-awards/prizes-and-awards-descriptions/'
CLAH_PRIZES = [
    ('bolton-johnson-prize', 'Bolton-Johnson Prize', 'book', 'book'),
    ('susan-m-socolow-and-lyman-l-johnson-prize', 'Susan M. Socolow and Lyman L. Johnson Prize', 'book', 'book'),
    ('the-elinor-melville-prize-for-latin-american-environmental-history',
     'Elinor Melville Prize for Caribbean and Latin American Environmental History', 'book', 'book'),
    ('howard-f-cline-memorial-prize', 'Howard F. Cline Memorial Prize', 'book', 'book'),
    ('maria-elena-martinez-prize', 'María Elena Martínez Prize', 'book', 'book'),
    ('warren-dean-memorial-prize', 'Warren Dean Memorial Prize', 'book', 'book'),
    ('james-alexander-robertson-prize', 'James Alexander Robertson Prize', 'article', 'article'),
    ('paul-vanderwood-prize', 'Paul Vanderwood Prize', 'article', 'article'),
    ('tibesar-prize', 'Antonine Tibesar Prize', 'article', 'article'),
    ('distinguished-service-award', 'Distinguished Service Award', 'career', 'career'),
]


def clah():
    body, out = 'Conference on Latin American History', []
    for slug, prize, honours, kind in CLAH_PRIZES:
        url = CLAH_BASE + slug + '/'
        L = lines_of(url)
        if L is None:
            continue
        rows = generic_list(body, prize, 'Latin American history', honours, url, L, r'^View Previous Recipients',
                            stop_pat=r'^(Donations|Copyright|©|Quick Links)', kind=kind)
        for r in rows:
            if r['prize'] == 'Howard F. Cline Memorial Prize' and 'venue: ' in r['note']:
                r['honours'] = 'article'   # the Cline prize is for an article or a book
        out += rows
    return out


def asa():
    body, out = 'African Studies Association', []
    for slug, prize, honours, kind in [('asa-best-book-prize', 'ASA Best Book Prize (formerly Melville J. Herskovits '
                                        'Prize)', 'book', 'book'),
                                       ('bethwell-a-ogot-book-prize', 'Bethwell A. Ogot Book Prize', 'book', 'book'),
                                       ('distinguished-africanist-award', 'Distinguished Africanist Award', 'career',
                                        'career')]:
        url = 'https://africanstudies.org/awards-prizes/' + slug + '/'
        L = lines_of(url)
        if L is None:
            continue
        out += generic_list(body, prize, 'African studies', honours, url, L, r'(Prize|Award) (Winners|Recipients)',
                            stop_pat=r'^(Share|Related|Copyright|©|Past Winners$)', kind=kind)
    return out


def toynbee():
    url = 'https://toynbeeprize.org/the-prize/'
    L = lines_of(url)
    if L is None:
        return []
    L = [clean(x) for x in L]
    out = []
    try:
        s = L.index('Past Prize Winners')
    except ValueError:
        return []
    for i in range(s + 1, len(L) - 1):
        if YEAR.match(L[i + 1]) and not YEAR.match(L[i]):
            names = split_names(L[i])
            for n in names:
                out.append(row('Toynbee Prize Foundation', 'Toynbee Prize', 'global history', 'career', L[i + 1], n,
                               [x for x in names if x != n], url=url))
        if L[i].startswith('JOIN'):
            break
    return out


def dedupe(rows):
    seen, out = set(), []
    for r in rows:
        k = (r['prize_id'], r['year'], r['winner'], r['work_title'])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def harvest():
    rows = []
    for fn in (bancroft, shot, aseh, berks, wha, clah, asa, toynbee):
        try:
            got = fn()
        except Exception as e:  # one body must not stop the others
            print(fn.__name__, 'failed:', type(e).__name__, e, file=sys.stderr)
            got = []
        if fn is aseh:
            got = aseh_marsh_fix(got)
        rows += got
    rows = dedupe(rows)
    return [{c: r.get(c, '') for c in COLS} for r in rows]


if __name__ == '__main__':
    rows = harvest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    c = Counter(r['body'] for r in rows)
    for b, n in c.most_common():
        print(f'{n:5d}  {b}')
    print(f'{len(rows):5d}  total -> {OUT.relative_to(ROOT)}')
