"""Parse JSTOR note lists (the `references` field) into citations.

JSTOR splits each article's notes into pieces in note order: sometimes one piece per citation, sometimes one
per whole note (with commentary), sometimes JATS XML. There is no italic, so titles are found from the
imprint '(Place: Publisher, Year)', quotation marks, comma imprints ', Paris, Fayard, 1986' and German
', Leipzig 1908'. Back-references (Ibid., idem, op. cit., short titles, author-date 'Hamilton 1972') are
resolved to an earlier full citation in the same item, so order matters.

Rule ids (one per citation): xml, ibid, idem, opcit, short, authordate, bib_inverted, us_book, frag_book,
article, chapter, comma_imprint, german_imprint, archival, diss_fallback, unparsed.

Reuses the dissertation parsers (scripts/extract_dissertation_notes.py and
scripts/extract_dissertation_bibliographies.py) as a base and fallback.
"""
import html, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import extract_dissertation_bibliographies as bib  # noqa: E402
import extract_dissertation_notes as N  # noqa: E402
from build_dissertation_citation_graph import fold, title_key  # noqa: E402

Y = r'(?:1[4-9]\d\d|20[0-2]\d)'
YEAR = re.compile(rf'(?<![\d/]){Y}(?![\d/])')

# ---------------------------------------------------------------- normalisation

TAG = re.compile(r'<[^>]{0,400}>')


def normalize(s):
    s = unicodedata.normalize('NFC', html.unescape(s))
    s = re.sub(r'<sup>(.*?)</sup>', r'\1', s)
    s = TAG.sub(' ', s)
    s = s.replace('­', '')
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\s+(?=[,;)\]])|(?<=[(\[])\s+', '', s)          # 'Werbner , ed.' / '( London'
    s = re.sub(r'\s+(?=[.:](?:\s|$))', '', s)
    # nested parentheses inside an imprint: '(Villeneuve-d’Ascq (Nord), 2002)' -> '(Villeneuve-d’Ascq [Nord], 2002)'
    s = re.sub(r'\(([^()]*)\(([^()]*)\)([^()]*)\)', r'(\1[\2]\3)', s)
    # OCR hyphenation at line ends: 'Dis- covery', 'Mc- Graw-Hill'; keep 'pre- and post-war'
    s = re.sub(r'(?<=[a-zà-ÿ])- (?=[a-zà-ÿ])(?!(?:and|or|und|et|y|e|oder|ou)\b)', '', s)
    s = re.sub(r'(?<=Mc)- (?=[A-Z])', '', s)
    # old-style figures read as letters: 'i983', 'I969' -> years
    s = re.sub(r'\b[iIl]([6-9]\d\d)\b', r'1\1', s)
    s = re.sub(r'(?<=[a-z])(?=(?:1[5-9]|20)\d\d\b)', ' ', s)   # 'October1868' -> 'October 1868'
    return s


# ---------------------------------------------------------------- JATS XML pieces

def parse_xml(raw):
    """JATS mixed-citation fragments (Renaissance Quarterly and others)."""
    surn = re.findall(r'<surname>(.*?)</surname>', raw)
    given = re.findall(r'<given-names>(.*?)</given-names>', raw)
    authors = [f'{s.strip()}, {g.strip()}' if g else s.strip() for s, g in zip(surn, given + [''] * len(surn))]
    def tag(t):
        m = re.search(rf'<{t}[^>]*>(.*?)</{t}>', raw, re.S)
        return normalize(m.group(1)) if m else None
    title = tag('article-title') or tag('chapter-title')
    source = tag('source')
    year = tag('year')
    kind = 'article' if tag('article-title') else 'chapter' if tag('chapter-title') else 'book'
    if not title:
        title, source = source, None
    if not title:  # a <comment> with plain text: parse the text
        return None
    m = YEAR.search(year or '')
    return dict(authors=authors, surnames=[a.split(',')[0] for a in authors], title=title, container=source,
                place=tag('publisher-loc'), publisher=tag('publisher-name'), year=int(m.group()) if m else None,
                volume=tag('volume'), pages=(tag('fpage') + ('-' + tag('lpage') if tag('lpage') else '')) if tag('fpage') else None,
                kind=kind, rule='xml')


# ---------------------------------------------------------------- name lists (natural order)

PARTICLE = r"(?:de|du|des|la|le|van|von|der|den|di|da|dos|del|della|y|ten|ter|St\.|d'|d’)"
TOK = rf"(?:[A-ZÀ-ÝĀ-Ž][\w'’\-–]*\.?|[A-ZÀ-Ý]\.(?:-?[A-ZÀ-Ý]\.)*|{PARTICLE})"
NAME = rf"(?:{TOK}(?:(?:\s+|(?<=\.)){TOK}){{0,5}}(?:,?\s+(?:Jr|Sr|II|III|IV)\.?)?)"
# a co-author after a comma is a full name (given name or initials + surname): 'Gail Bederman, Manliness and
# Civilization: A Cultural History ...' is one author and a title, not three authors (2026-11-06)
NAME2 = rf"(?:{TOK}(?:(?:\s+|(?<=\.)){TOK}){{1,5}}(?:,?\s+(?:Jr|Sr|II|III|IV)\.?)?)"
NAMES = rf"{NAME}(?:(?:,\s*|\s+)(?:and|et|&|und|u\.|y|e)\s+{NAME}|,\s*{NAME2}(?=(?:,\s*|\s+)(?:and|et|&|und|u\.|y|e)\s)){{0,6}}(?:,?\s+et\s+al\.?)?"
# 'F. de Potter, J. Broeckaert, Title': a comma list of initialled names (a title rarely starts 'J. Name,')
INIT_NAME = rf"[A-ZÀ-Ý]\.(?:\s?-?[A-ZÀ-Ý]\.)*\s+(?:{PARTICLE}\s+)?[A-ZÀ-ÝĀ-Ž][\w'’\-–]+"
INIT_LIST = re.compile(rf"^(?P<a>{INIT_NAME}(?:\s*,\s*{INIT_NAME}){{1,5}}(?:,?\s*(?:and|et|&|und|y|e)\s+{INIT_NAME})?)\s*,\s+")
EDS = r"(?:,?\s*\(?(?:eds?|éds?|dir|dirs|coords?|comps?|Hg|Hrsg|a cura di|trans|tr)\.?\)?)?"
# a list of names ends with a comma (or a quoted title follows); a colon ends only a single name (German 'Hans Müller:
# Titel'): 'Theda Skocpol, Protecting Soldiers and Mothers: The Political Origins ...' is one author and a title
_AUTHOR = re.compile(rf"^(?:(?P<a>{NAMES}){EDS}\s*(?:,\s+|\s(?=[“\"«]))|(?P<a1>{NAME}){EDS}\s*:\s+)")   # also 'Marion Johnson "News from Nowhere"'
class _AuthorMatch:
    """A match of _AUTHOR whose group('a') is the name list from either branch."""
    def __init__(self, m):
        self.m = m

    def group(self, g=0):
        return (self.m.group('a') or self.m.group('a1')) if g == 'a' else self.m.group(g)

    def start(self, *g):
        return self.m.start(*g)

    def end(self, *g):
        return self.m.end(*g)


class _AuthorRe:
    def match(self, s, pos=0):
        m = _AUTHOR.match(s, pos)
        return _AuthorMatch(m) if m else None


AUTHOR = _AuthorRe()
# 'Georges Duby, Michelle Perrot (éd.), Titre' / 'Friedrich Edelmayer, Maximilian Lanzinner, Peter Rauscher (éd.),': a comma list only with an editor mark
AUTHOR_EDS = re.compile(rf"^(?P<a>{NAME}(?:\s*,\s*{NAME}){{1,6}}(?:,?\s*(?:and|et|&|und|y|e)\s+{NAME})?)\s*,?\s*\(?(?:eds?|éds?|dir|dirs|coords?|Hg|Hrsg|a cura di)\.?\)?\s*[,:]\s+")
SPLIT = re.compile(r'\s*(?:,\s*(?:and|et|&|und|u\.|y|e)\s+|\s+(?:and|et|&|und|u\.|y|e)\s+|,\s*(?=[A-ZÀ-Ý]))')
STOPWORDS = {'the', 'a', 'an', 'in', 'on', 'see', 'for', 'of', 'and', 'le', 'la', 'les', 'il', 'el', 'der', 'die',
             'das', 'ibid', 'cf', 'voir', 'vgl', 'this', 'these', 'his', 'her', 'their', 'my', 'our', 'it', 'as'}
NOT_AUTHOR = re.compile(r'^(?:The|A(?![.\-])|An|In|On|See|For|Ibid|Cf|Voir|Vgl|This|These|His|Her|Their|My|Our|It|As|Le|La|Les|'
                        r'Il|El|Der|Die|Das|Report|Minutes|Proceedings|Annual|Journal|Letter|Papers|Correspondence|'
                        r'Archives?|Public|National|Library|British|Bibliothèque|Archivio|Archivo|Arch|Hansard|'
                        r'Parliamentary|House|Senate|Congress|Statutes|Census|Calendar|Rotuli|Acts|Records?|'
                        r'University|Department|Ministry|Ministère|Government|Royal|Commission|Bureau|Office|Board)\b')
JR = re.compile(r',?\s+(?:Jr|Sr|II|III|IV)\.?$')


def split_names(a):
    a = re.sub(r',?\s*\bet\s+al\b\.?', '', a)
    a = re.sub(EDS + r'$', '', a).strip(' ,.')
    parts, out = SPLIT.split(a), []
    for p in parts:
        p = p.strip(' ,.')
        if not p:
            continue
        if re.fullmatch(r'(?:Jr|Sr|II|III|IV)\.?', p) and out:
            out[-1] += ', ' + p
            continue
        out.append(p)
    # Spanish/Portuguese compound surnames: 'Diego Parada y Barreto' is one person ('y' + a single surname)
    m = re.fullmatch(r"(.+?\s[A-ZÀ-Ý][\w'’\-]+)\s+(?:y|e|i)\s+([A-ZÀ-Ý][\w'’\-]+)", a)
    if m and len(out) == 2 and ' ' not in out[1]:
        return [a]
    return out


def canonical(name):
    """'Surname, Given' and surname from a natural-order name."""
    jr = JR.search(name)
    base = JR.sub('', name).strip(' ,.') if jr else name.strip(' ,.')
    toks = base.split()
    if len(toks) == 1:
        return base, base
    # surname = last token plus any particles before it ('Jean de La Fontaine', 'Ludwig von Mises')
    i = len(toks) - 1
    while i > 1 and re.fullmatch(PARTICLE, toks[i - 1]):
        i -= 1
    sur, given = ' '.join(toks[i:]), ' '.join(toks[:i])
    if sur.isupper() and len(sur) > 2:  # French 'Fabienne DARGE'
        sur = sur.title()
    for k, t in enumerate(toks):   # 'Clément LENOBLE et ...' / 'LACOSTE-DUJARDIN C.' handled elsewhere
        if len(t) > 2 and t.isupper() and k < len(toks) - 1 and not re.fullmatch(r'[A-Z]\.', t):
            sur, given = ' '.join(toks[k:]).title(), ' '.join(toks[:k])
            break
    return (f'{sur}, {given}' if given else sur), sur


def authors_of(a):
    names = [n for n in split_names(a) if n]
    if not names or len(names) > 7:
        return [], []
    canon = [canonical(n) for n in names]
    return [c[0] for c in canon], [c[1] for c in canon]


def plausible_author(a):
    if not a or len(a) > 140 or NOT_AUTHOR.match(a) or a.strip(' ,.:').lower() in N.PLACES:
        return False
    words = re.findall(r"[^\W\d_][\w'’\-]*", a)
    if not words:
        return False
    if len(words) <= 2 and all(w.isupper() and len(w) <= 6 for w in words):
        return False   # 'PJ', 'NAI', 'TS G': archive and source sigla
    if len(words) == 1 and re.fullmatch(r'[A-Z][a-z]?[A-Z]\w*', words[0]):
        return False   # 'ASFi'
    low = [w for w in words if w[0].islower() and not re.fullmatch(PARTICLE, w) and w not in ('and', 'et', 'und', 'u', 'y', 'e', 'al')]
    if any(w in ('The', 'Le', 'La', 'Les', 'Die', 'Der', 'Das', 'El', 'Il', 'Of', 'History', 'Histoire', 'Geschichte') for w in words[1:]):
        return False
    return not low and not any(w.lower() in ('university', 'press', 'society', 'committee') for w in words)


# ---------------------------------------------------------------- lead text ('See, for example,')

LEAD = re.compile(r"^(?:(?:see|cf|voir|vgl|siehe|v\.|compare|on\s+[^,]{3,60},?\s+see|for\s+[^,]{3,80},?\s+see|"
                  r"also|and|et|und|y|e\.g\.|i\.e\.|especially|esp\.|notably|notamment|aussi|auch|for\s+example|for\s+instance|"
                  r"for\s+a\s+[^,]{3,60},?\s+see|quoted\s+in|cited\s+in|cité\s+(?:dans|par)|cit\.\s+in|reprinted\s+in|"
                  r"in|dans|quoted\s+from|from|sur\s+[^,]{3,60},?\s+voir|à\s+ce\s+sujet|in\s+general|more\s+generally|generally|"
                  r"the\s+(?:best|standard|classic)\s+(?:account|study|work|treatment)\s+(?:is|remains)|"
                  r"for\s+the\s+[^,]{3,80},?\s+see|see\s+also|see\s+especially|see\s+generally)[\s,.:;]+)+", re.I)


SENT_END = re.compile(r'[.:;]\s+(?=\S)')
ABBR = re.compile(r'(?:[A-ZÀ-Ý]|pp|p|vol|vols|no|nos|ed|eds|cf|St|Mr|Mrs|Dr|Jr|Sr|trans|chap|art|n|ch|fol|ff|esp|e\.g|i\.e|cit|op|loc|Bd|Hg|Hrsg|S|t|éd|dir|c|ca)', re.I)


def strip_lead(c):
    """Drop commentary before a citation. Keep the text after the last sentence end that precedes a
    'Name Name, ' + title/imprint, and leading signal words."""
    if BIB_PERIOD.match(c):
        return c
    am = AUTHOR_EDS.match(c) or INIT_LIST.match(c) or AUTHOR.match(c)
    if am and plausible_author(am.group('a')):
        return c   # a note that opens with its author: never cut inside the title ('Treason Was No Crime: Ludwig Beck, ...')
    best = 0
    ip, qm = IMPRINT_PAREN.search(c), re.search(r'[“"«„]', c)
    limit = min([x for x in (ip.start() if ip else None, qm.start() if qm else None) if x is not None], default=len(c))
    for m in SENT_END.finditer(c, 0, limit):
        word = re.search(r'(\S+)$', c[:m.start()])
        if word and ABBR.fullmatch(word.group(1)):
            continue
        nxt = c[m.end():]
        n2 = LEAD.sub('', nxt, count=1)
        am = AUTHOR_EDS.match(n2) or AUTHOR.match(n2)
        if am and plausible_author(am.group('a')) and re.search(r'[^\W\d_]{3,}', n2[am.end():][:40]):
            best = m.end()
    if not best:
        am = AUTHOR_EDS.match(c) or AUTHOR.match(c)
        if not (am and plausible_author(am.group('a'))):
            for m in re.finditer(r'(?:,|\bsee|\bvoir|\bvgl\.|\bcf\.|\bin|\bby|\bpar|\bde)\s+(?=[A-ZÀ-Ý])', c[:limit]):
                if re.search(r'\b(?:ed|eds|éd|trans|tr|hrsg|Hg|by|par|von|a cura di|introd?|with)\.?\s*,?\s*$', c[:m.end()], re.I):
                    continue
                n2 = c[m.end():]
                am = AUTHOR_EDS.match(n2) or AUTHOR.match(n2)
                if am and plausible_author(am.group('a')) and (n2[am.end():am.end() + 1] in '“"«„‘' or ip):
                    best = m.end()
                    break
    c = c[best:]
    return LEAD.sub('', c, count=1).strip()


# ---------------------------------------------------------------- patterns

IBID = re.compile(r'^\s*(?:(?:ibid(?:em)?|ebd|ebenda|ivi)\b\.?|ib\.|id\.(?=\s*,?\s*(?:p|pp|S|vol|t)\.?\s*\d|\s*$)|loc\.\s*cit\.?)', re.I)
IDEM = re.compile(r'^\s*(?:idem|eadem|id\.|the\s+same|his|her)\b[.,]?\s+(?=\S)', re.I)
OPCIT = re.compile(r'\b(?:op\.?\s*cit|art\.?\s*cit|ouvr?\.?\s*cit|cit\.\s*n\.|a\.\s*a\.\s*O|loc\.?\s*cit|cit\.)\b\.?'
                   r'|\((?:n\.|note|nn\.|Anm\.|wie Anm\.|cit\.\s*n\.|supra|above)\s*\d*[^()]{0,20}\)', re.I)
IMPRINT_PAREN = re.compile(rf"\((?P<imp>[^()]{{0,160}}?(?P<y>{Y})(?:[–\-/]\d{{2,4}})?[a-z]?(?:\s*\[[^\]]*\])?[^()]{{0,40}}?)\)")
QUOTED = re.compile(r'(?:^|(?<=[\s,(:]))(?P<q>[“"«‘\'„])\s*(?P<t>.{3,400}?)\s*(?P<c>[”"»’\'“])(?=[\s,.;:)\]]|$)')
VOL_DATE = re.compile(rf"^[\s,.:]*(?:in\s*:?\s*)?(?P<cont>[^\d(“”\"«»]{{2,160}}?)[\s,.]*(?:(?:vol\.|v\.|t\.|tome|Bd\.|Jg\.|a\.|anno|n[°o]\.?)\s*)?"
                      rf"(?P<vol>[IVXLCivxlc]{{1,8}}|\d{{1,4}}(?:[\-/.:]\d{{1,4}})?)?(?:\s*,?\s*(?:no\.|n[°o]|nr\.|Heft|fasc\.|H\.)\s*\d+)?"
                      rf"[\s,.]*\(?(?P<date>[^()\d]{{0,25}}{Y})\)?")
ARCHIVAL = re.compile(r'\b(?:MSS?\b|manuscript|Archives?\b|Archivo|Archivio|Archiv\b|Arch\.|Bibl\.|Bibliothèque|Biblioteca|'
                      r'Public Record Office|PRO\b|TNA\b|National Archives|Library of Congress|Papers\b|Correspondence|'
                      r'fols?\.|ff\.|carton|liasse|dossier|legajo|busta|filza|reg\.|Box\b|Folder\b|RG\s?\d|MG\s?\d|CO\s?\d|FO\s?\d|'
                      r'Hansard|Parl(?:iamentary)?\.? Papers|Accounts and Papers|Session Laws|Statutes|Congressional Record|'
                      r'Minutes\b|Proceedings of the|Report of the|Annual Report|Census|Calendar of|Rotuli|letter (?:of|from|to)|'
                      r'lettre (?:de|à)|Brief an|interview|entretien|A\.\s?N\.|A\.\s?D\.|Arch\. nat|Arch\. dép|B\.\s?N\.|BnF|'
                      r'personal communication|Library\b|f\.\s?\d+.{0,30}\b(?:op|d)\.\s?\d|\bfond\b|\bopis\b|\bdelo\b)', re.I)
PLACE_PUB_YEAR = re.compile(rf",\s*(?P<place>(?:[A-ZÀ-Ý][\w'’.\-]+(?:[ \-/](?:am|an|der|sur|en|de|im|bei|[A-ZÀ-Ý][\w'’.\-]+)){{0,3}}))"
                            rf"(?:,\s*(?P<pub>[^,;()]{{2,80}}?))?,\s*(?P<y>{Y})(?:[–\-]\d{{2,4}})?(?:\s*\[[^\]]*\])?\b")
GERMAN_IMP = re.compile(rf",\s*(?P<place>[A-ZÀ-Ý][\w'’\-]{{2,}}(?:[ /\-][A-ZÀ-Ý][\w'’.\-]+){{0,2}}(?:\s+(?:u\.\s?a\.|etc\.))?)\s+(?P<y>{Y})(?![\s\-–]*\d)(?:\s*[\[(][^\])]*[\])])?\b")
AUTHOR_DATE = re.compile(rf"^(?P<a>(?:[A-ZÀ-Ý][\w'’\-]+|de|van|von|den|der|du|le|la)(?:[\s/]+(?:and|et|&|und|[A-ZÀ-Ý][\w'’\-]+|de|van|von|den|der)){{0,5}}),?\s+\(?(?P<y>{Y})(?P<s>[a-z])?\)?(?:[,:;]\s*(?:p+\.\s*)?[\d\-–ivxl, ]*)?\.?;?$")
# author-date bibliography entries: the year follows the (inverted) name list directly
_GIV = r"[A-ZÀ-Ý][\w'’]*\.?(?:(?:[\s\-]+|(?<=\.))[A-ZÀ-Ý][\w'’]*\.?){0,3}"   # 'T. H.', 'Jean-Pascal', 'J.A.': no nested optional runs
_INV = rf"[A-ZÀ-Ý][\w'’\-]+(?:\s[A-ZÀ-Ý][\w'’\-]+)?,?\s+{_GIV}"
BIB_INVERTED = re.compile(rf"^(?P<a>{_INV}(?:\s*(?:,|;|&|and|et|y)\s*(?:{_INV}|{_GIV}\s[A-ZÀ-Ý][\w'’\-]+))*"
                          rf"(?:\s*\(?(?:eds?|éds?|dir|Hg|Hrsg)\.?\)?)?)[.,]?\s*(?:\((?P<y1>{Y})[a-z]?\)[.,:]?|(?P<y2>{Y})[a-z]?[.,:])\s+")
PLACES_X = N.PLACES | {'parigi', 'londra', 'londres', 'nueva york', 'lisboa', 'venezia', 'venice', 'firenze', 'genova', 'leipzig',
                       'bruxelles', 'den haag', 'the hague', 'la haye', 'wien', 'köln', 'cologne', 'zürich', 'zurich', 'basel', 'bâle'}
PUBLISHER_WORD = re.compile(r'\b(?:Instituto|Editorial|Ediciones|Editora|Edizioni|Éditions|Editions|Presses?|Verlag|Press|Publishing|'
                            r'Publishers|Libreria|Librería|Librairie|Imprenta|Tipografia|Universidad|Università|Université|Fondo|Consejo|Centro)\b', re.I)
LEGAL = re.compile(r'\bcase no\.|\bFederal Cases\b|\bv\.\s+[A-Z]|\bvs\.\s|\bU\.\s?S\.\s\d|\bStat\.\s|\bVict\.|\bGeo\.\s[IVX]|\b\d+\s+&\s+\d+\s+Will\.')
_MON = (r'(?:Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec|janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc|'
        r'enero|feb|marzo|abril|mayo|junio|julio|agosto|sept|oct|nov|dic|genn|febbr|apr|magg|giugno|luglio|ag|sett|ott|dic)[a-zéû]*\.?')
MONTH_DAY = re.compile(rf'\b{_MON}\s+\d{{1,2}},?\s+{Y}|\b\d{{1,2}}\s+{_MON}\s+{Y}', re.I)
MONTH_YEAR = re.compile(rf'^\s*(?:(?:spring|summer|fall|autumn|winter)|{_MON}(?:[\-–/]{_MON})?)[.,]?\s+{Y}\s*$', re.I)
BIB_PERIOD = re.compile(rf"^(?P<a>[^.]{{2,80}}?(?:\s[A-Z]\.)*)\.\s+(?P<t>[A-ZÀ-Ý0-9\'‘“\"].{{3,300}}?)\.\s+(?:[^.]{{0,120}}\.\s+)*?"
                        rf"(?P<pl>[A-ZÀ-Ý][^:.;]{{1,60}}):\s*(?P<pub>[^:;]{{2,100}}?),\s*(?P<y>{Y})\.?\s*$")
MLA_ARTICLE = re.compile(rf"^(?P<a>[A-ZÀ-Ý][\w'’\-]+(?:\s[A-ZÀ-Ý][\w'’\-]+)?,\s+[^.“\"]{{2,40}}?(?:,?\s+and\s+[^.“\"]{{3,40}}?)?)\.\s+[“\"](?P<t>.{{3,300}}?)[”\"]\s+"
                         rf"(?P<c>[^0-9“”\"]{{3,150}}?)\s+(?P<v>\d[\d.:]*)?(?:,?\s*no\.\s*\d+)?\s*\((?P<y>{Y})\)")
PAGES = re.compile(r'(?:\bp+\.?\s*|\bS\.\s*|:\s*|,\s*)(?P<pp>[\divxlcIVXLC]+(?:\s*[-–]\s*[\divxlc]+)?(?:\s*,\s*\d+(?:\s*[-–]\s*\d+)?)*)\s*\.?\s*$')


def years_in(s):
    return [int(m.group()) for m in YEAR.finditer(s)]


def split_imprint(imp):
    """'New York: Harper & Row, 1954' / 'Cambridge, 1981' / '2nd ed., Cambridge 1914' -> place, publisher, year."""
    imp = re.sub(r'^\s*(?:\d\w*\s+ed\.?|rev\.\s*ed\.|new\s+ed\.|repr\.?|reprint(?:ed)?|unpublished)[,;]?\s*', '', imp, flags=re.I)
    ys = years_in(imp)
    year = ys[0] if ys else None
    place = pub = None
    m = re.match(r'^\s*([^:;]{2,60}?)\s*:\s*([^;]{2,120}?),?\s*(?:c\.\s*)?' + Y, imp)
    if m:
        place, pub = m.group(1).strip(), m.group(2).strip(' ,')
    else:
        m = re.match(r'^\s*([A-ZÀ-Ý][^:;,\d]{1,60}?),?\s+(?:c\.\s*)?' + Y, imp)
        if m:
            place = m.group(1).strip(' ,')
    return place, pub, year


def parse_one(c):
    """One normalised citation string (lead already stripped) -> dict or None. Rule order: most specific first."""
    out = dict(authors=[], surnames=[], title=None, container=None, place=None, publisher=None, year=None,
               volume=None, pages=None, kind='other', rule='unparsed')
    if len(c) < 4:
        return None
    if re.search(r'personal communication|\binterview(?:ed)?\b|\bentretien\b|\bconversation with\b', c, re.I) or LEGAL.search(c[:150]):
        out.update(kind='primary', rule='archival')
        return out
    if re.search(r'https?://|www\.', c) and not IMPRINT_PAREN.search(c):
        out.update(kind='web', rule='web')
        return out
    if (pb := BIB_PERIOD.match(c)) and plausible_author(pb.group('a')) and len(pb.group('a').split()) <= 8:
        a = pb.group('a')
        if re.match(r"^[A-ZÀ-Ý][\w'’\-]+(?: [a-z]{1,3} [A-ZÀ-Ý][\w'’\-]+| [A-ZÀ-Ý][\w'’\-]+)?, [A-ZÀ-Ý]", a):   # 'Fenner, Dudley', 'Bertoloni Meli, Domenico'
            names = [x.strip() for x in re.split(r'\s*(?:;|\band\b|&)\s*', a) if x.strip()]
            out['authors'] = names; out['surnames'] = [n.split(',')[0].strip() for n in names]
        else:
            out['authors'], out['surnames'] = authors_of(a)
        out.update(title=pb.group('t').strip(' .'), place=pb.group('pl'), publisher=pb.group('pub'),
                   year=int(pb.group('y')), kind='book', rule='bib_period')
        return out
    if (ma := MLA_ARTICLE.match(c)) and plausible_author(ma.group('a')):
        a = ma.group('a')
        names = [x.strip() for x in re.split(r',?\s+and\s+', a) if x.strip()]
        out['authors'] = names; out['surnames'] = [n.split(',')[0].strip() if ',' in n else canonical(n)[1] for n in names]
        out.update(title=ma.group('t').strip(' .,'), container=ma.group('c').strip(' .,'), volume=ma.group('v'),
                   year=int(ma.group('y')), kind='article', rule='mla_article')
        return out
    am = AUTHOR_EDS.match(c) or INIT_LIST.match(c) or AUTHOR.match(c)
    a_ok = am and plausible_author(am.group('a'))
    rest = c[am.end():] if a_ok else c
    if a_ok:
        out['authors'], out['surnames'] = authors_of(am.group('a'))
        if re.search(r'\b(?:eds?|éds?|dir|coords?|Hg|Hrsg|a cura di)\b\.?\)?\s*[,:]\s*$', c[:am.end()]):
            out['editors'] = True
    q = QUOTED.match(rest) if rest[:1] in '“"«‘\'„' else None
    if q and q.group('q') in "'‘" and q.group('c') in "'’" and rest[q.end():q.end() + 1] not in ',.;:' :
        # straight or curly single quotes: an apostrophe can close early ("governments' religious"); prefer a close before , or .
        better = re.match(r"^['‘]\s*(?P<t>.{3,400}?)\s*['’](?=[,.;:]|\s*$)", rest)
        if better:
            q = better
    if q:  # quoted title: article or chapter
        out['title'] = q.group('t').strip(' ,.')
        after = re.sub(rf'^\s*[\[(]{Y}[\])]', '', rest[q.end():])
        ch = re.match(r'^[\s,.]*(?:in|dans|en|in:)\s+(?P<b>.+)$', after, re.I)
        if ch and not re.match(r'^\s*[«“"]', ch.group('b')) and (IMPRINT_PAREN.search(ch.group('b')) or PLACE_PUB_YEAR.search(ch.group('b'))
                                                                   or re.search(r'\b(?:eds?|éds?|dir|Hg|Hrsg|a cura di)\b\.?', ch.group('b'))):
            b = ch.group('b')
            ip = IMPRINT_PAREN.search(b)
            book = b[:ip.start()] if ip else b
            # 'in Thomas Head and Richard Landes, eds., The Peace of God' -> drop the editors; but keep
            # 'in Black Theater U.S.A., ed. James V. Hatch' (the title comes first, 'ed.' then a name)
            book = re.sub(rf'^{NAMES}\s*,?\s*\(?(?:eds?|éds?|dir|dirs|Hg|Hrsg|a cura di)\.?\)?\s*[,:]\s*', '', book)
            book = re.split(r',\s*(?:ed\.|eds\.|edited|trans\.|éd\.|dir\.|hrsg\.)', book)[0]
            out.update(container=book.strip(' ,.'), kind='chapter', rule='chapter')
            if ip:
                out['place'], out['publisher'], out['year'] = split_imprint(ip.group('imp'))
            elif (pm := PLACE_PUB_YEAR.search(b)):
                out.update(place=pm.group('place'), publisher=pm.group('pub'), year=int(pm.group('y')))
                out['container'] = re.split(r',\s*(?:ed\.|eds\.|éd\.|dir\.)', b[:pm.start()])[0].strip(' ,.')
        else:
            vm = VOL_DATE.match(after)
            if vm and vm.group('cont') and len(re.findall(r'[^\W\d_]{2,}', vm.group('cont'))) >= 1:
                cont = re.sub(r'^\s*(?:in|dans|en)\s*:?\s+', '', vm.group('cont'), flags=re.I)
                if ',' in vm.group('date') and not vm.group('vol'):   # the date grabbed the container's tail
                    cont = cont.rstrip() + ' ' + vm.group('date').rsplit(',', 1)[0].lstrip()
                cont = cont.strip(' ,.«»“”"')
                out.update(container=cont, volume=vm.group('vol'), year=int(re.search(Y, vm.group('date')).group()), kind='article', rule='article')
                if MONTH_DAY.search(after[:vm.end() + 12]):
                    out.update(kind='periodical', rule='periodical_article')
                    out['container'] = re.sub(rf',?\s*{_MON}$', '', cont, flags=re.I).strip(' ,.')
                pm = re.match(r'^[\s,.):]*(?:pp?\.\s*|S\.\s*)?(?P<pp>\d+(?:\s*[-–]\s*\d+)?)', after[vm.end():])
                if pm:
                    out['pages'] = pm.group('pp')
            else:
                ys = years_in(after)
                if ys and len(after) < 160:
                    out.update(year=ys[0], kind='article' if re.search(r'\d', after) else 'other', rule='article_loose',
                               container=re.split(r'[,(\d]', after.strip(' ,.'), 1)[0].strip(' ,.«»') or None)
                elif not after.strip(' .,'):
                    out.update(kind='short', rule='short_quoted')
                else:
                    out.update(rule='quoted_other', kind='other')
        if out['rule'] in ('short_quoted', 'article_loose', 'quoted_other') and not out['year'] and out['surnames']:
            out.update(kind='short', rule='short')
        return out
    ips = list(IMPRINT_PAREN.finditer(rest))
    # a bare date range inside the title ('Confréries … (1450–1830) (Villeneuve, 2002)') is not the imprint
    ips = [m for k, m in enumerate(ips) if not (re.fullmatch(rf'\s*c?\.?\s*{Y}\s*[-–]\s*\d{{2,4}}\s*', m.group('imp')) and k < len(ips) - 1)]
    ip = ips[0] if ips else None
    if ip and ip.start() > 2:  # Title (Place: Publisher, Year)
        title = rest[:ip.start()].strip(' ,.')
        title = re.split(r',\s*(?:\d+\w*\s+ed\.|rev\.\s*ed\.|ed\.\s|eds?\.\s|edited by|trans\.|translated by|tr\.|\d+\s+vols?\.)', title)[0]
        title = re.sub(r'\s*\((?:hereafter|cited as)[^)]*\)', '', title).strip(' ,.')
        if re.search(r'thesis|dissertation|thèse|tesi|tesis', ip.group('imp'), re.I):
            out['kind'] = 'thesis'
        out['place'], out['publisher'], out['year'] = split_imprint(ip.group('imp'))
        if out['year'] is None:
            out['year'] = int(ip.group('y'))
        out['title'] = title
        out['kind'] = out['kind'] if out['kind'] == 'thesis' else 'book'
        out['rule'] = 'us_book' if a_ok else 'frag_book'
        pm = PAGES.search(rest[ip.end():])
        if pm:
            out['pages'] = pm.group('pp')
        # journal volume at the end of the 'title': ', 2' / ' 63' / ', vol. 5' / ', XXIV' (Roman only without an author:
        # 'Decline and Fall, II (London, 1900)' is a multi-volume book); never a year range ('1600-1800') or 'Henry VIII'
        vol_tail = re.compile(r'(?:,\s*(?:vol\.\s*)?|\s(?:vol\.\s*)?)(?<![\d\-–])\d{1,3}(?:,?\s*(?:no\.|n[°o])\s*\d+)?\s*$'
                              + ('' if a_ok else r'|,\s*[IVXLC]{1,6}(?:,?\s*(?:no\.|n[°o])\s*\d+)?\s*$'), re.I)
        if not a_ok and (ARCHIVAL.search(title) or len(title) < 4 or LEGAL.search(title)):
            out.update(kind='primary', rule='archival')
        elif MONTH_DAY.search(ip.group('imp')) or MONTH_YEAR.match(ip.group('imp')):
            out.update(kind='periodical', rule='periodical_issue')   # a newspaper or magazine issue
        elif vol_tail.search(title) and not re.search(r'[“”"«»]', title) and not (a_ok and (out['publisher'] or re.search(r'\bvol\.\s*\d+\s*$', title, re.I))):
            # 'Labour/Le Travailleur, 2 (1977)' / 'E. Neuweiler, Vierteljahrsschr. nat. Ges. Zürich, 75 (1930)': a journal, no title
            out.update(kind='article', rule='frag_article', container=vol_tail.sub('', title).strip(' ,.'), title=None)
        elif not a_ok and title[:1].islower():
            out.update(kind='other', rule='frag_other')   # commentary before an imprint, not a title
        return out
    if a_ok:
        pm = PLACE_PUB_YEAR.search(rest)
        gm = GERMAN_IMP.search(rest)
        m, rule = (pm, 'comma_imprint') if pm and (not gm or pm.start() <= gm.start()) else (gm, 'german_imprint') if gm else (None, None)
        if m and m.start() > 2:
            title = rest[:m.start()].strip(' ,.')
            inside = re.search(r',\s*(?:in|dans|en|in:)\s*:?\s+[«“"]?(?P<c>[^«»“”"]{3,200}?)[»”"]?\s*$', title)
            out['title'] = title
            out['place'] = m.group('place')
            out['publisher'] = m.groupdict().get('pub')
            if out['publisher'] and PUBLISHER_WORD.search(out['place']) and not PUBLISHER_WORD.search(out['publisher']):
                out['place'], out['publisher'] = out['publisher'], out['place']   # Spanish 'Editorial, Madrid, 1969'
            out['year'] = int(m.group('y'))
            out['kind'] = 'book'
            out['rule'] = rule
            if inside:
                out['title'] = title[:inside.start()].strip(' ,.')
                out['container'] = inside.group('c').strip()
                out['kind'] = 'chapter'
            return out
        # Italian/French article: 'Titolo, in «Rivista», XXXI, 1989, pp.'
        im = re.search(r',\s*(?:(?:in|dans)\s*:?\s*)?[«“"](?P<c>[^»”"]{3,200})[»”"]', rest)
        if im:
            out.update(title=rest[:im.start()].strip(' ,.'), container=im.group('c').strip(), kind='article', rule='article')
            ys = years_in(rest[im.end():])
            out['year'] = ys[0] if ys else None
            return out
        # Short form: 'Turner, Rise of the New West, 77' / 'McBride, Chile: Land and Society , 177.' / 'Baikie, op. cit.'
        if OPCIT.search(rest[:40]) or not years_in(rest) or (len(rest) < 80 and re.search(r',\s*[\divxl\-–, ]+\.?$', rest)
                                                              and not PLACE_PUB_YEAR.search(rest) and not GERMAN_IMP.search(rest)):
            t = re.split(r'\s*(?:,|\(|\bop\.|\bcit\.|\bp+\.|\bvol\.|\bS\.)\s*(?=[\divxlc]|op|cit|n\.|$)', rest, 1)[0].strip(' ,.')
            if re.match(rf'^\s*{_MON}\s+\d{{1,2}}\b|^\s*\d{{1,2}}\s+{_MON}', rest, re.I) and years_in(rest + ' ' + c):
                out.update(authors=[], surnames=[], container=c[:am.end()].strip(' ,'), year=(years_in(rest) or [None])[-1],
                           kind='periodical', rule='periodical_issue')
                return out
            if t and re.fullmatch(r'[\divxlcIVXLC\s\-–,.:]+|[Pp]\.?\s*\d.*', t):
                t = None   # 'Ayrout, 20': pages, not a short title
            out.update(title=t if t and not OPCIT.match(t) else None, kind='short', rule='opcit' if OPCIT.search(rest[:40]) else 'short')
            return out
    return None


# ---------------------------------------------------------------- per item

DASH = re.compile(r'^\s*[—–_]{1,3}\s*[.,:]?\s+|^\s*-{2,3}\s*[.,:]?\s+')   # '—. 2000. Title' / '——, Title': same author as before


def merge_open_quotes(parts):
    """The dissertation splitter can cut inside a quoted title ('"Horses Vs. Tractors,"'): rejoin a part
    whose quotation marks are still open with the next one."""
    out = []
    for p in parts:
        if out and (out[-1].count('“') > out[-1].count('”') or out[-1].count('"') % 2 or out[-1].count('«') > out[-1].count('»')):
            out[-1] = out[-1] + ('' if out[-1].endswith(' ') else ' ') + p
        else:
            out.append(p)
    return out

def citations(pieces):
    """Yield one dict per citation for one item, with back-references resolved.
    Keys: note (piece index), cit (index in piece), rule, kind, authors, surnames, title, container, place,
    publisher, year, volume, pages, ref (index of the full citation this one refers back to, or None), conf."""
    out, works = [], []   # works: indices into out of full citations
    by_sur = {}
    last_full = None
    authordate_refs = []
    for ni, raw in enumerate(pieces):
        if not isinstance(raw, str) or not raw.strip():
            continue
        if '<' in raw and ('<surname>' in raw or 'person-group' in raw or '<source>' in raw):
            r = parse_xml(raw)
            if r is None:
                raw = normalize(raw)
            else:
                r.update(note=ni, cit=0, ref=None, conf=0.95)
                out.append(r); works.append(len(out) - 1); last_full = len(out) - 1
                for s in r['surnames'][:1]:
                    by_sur.setdefault(fold(s), []).append(len(out) - 1)
                continue
        text = normalize(raw)
        if BIB_PERIOD.match(text):
            parts = [text]
        else:
            parts = merge_open_quotes([''.join(t for t, _ in p) for p in N.split_citations([(text, False)])])
        for ci, part in enumerate(parts):
            part = part.strip(' ;')
            if len(part) < 3:
                continue
            row = dict(note=ni, cit=ci, ref=None)
            if IBID.match(part):
                row.update(rule='ibid', kind='backref', ref=last_full, conf=0.9 if last_full is not None else 0.2)
                out.append(row); continue
            mi = IDEM.match(part) or DASH.match(part)
            idem_auth = None
            if mi and last_full is not None:
                idem_auth = (out[last_full].get('authors'), out[last_full].get('surnames'))
                part = part[mi.end():]
                if idem_auth[0] and re.match(rf'^\(?{Y}\)?[a-z]?[.,:]?\s', part):   # '—. 2000. Title': rebuild the author-date entry
                    part = f'{idem_auth[0][0]}. {part}'
                    idem_auth = None
            # author-date short reference: 'Hamilton 1972', 'Henriksen, 1973, p. 97-8', 'Moore/Webb 1978'
            ad = AUTHOR_DATE.match(part)
            if ad and len(part) < 90:
                sur = re.split(r'[\s/]+(?:and|et|&|und)?\s*|/', ad.group('a'))
                row.update(rule='authordate', kind='backref', surnames=[s for s in sur if s and s[0].isupper()][:4],
                           year=int(ad.group('y')), suffix=ad.group('s'), conf=0.5)
                out.append(row); authordate_refs.append(len(out) - 1); continue
            # inverted bibliography entry: 'BRIGGS, T. H. (1920) The Junior High School. Boston: ...', 'GAY, Jean-Pascal. 2011. Morales'
            bm = BIB_INVERTED.match(part)
            if bm and len(re.findall(r'[^\W\d_]{3,}', part[bm.end():][:60])) < 2:
                bm = None   # 'Moryson, Itinerary (1598), p. 179': a short form, not a bibliography entry
            if bm and (bm.group('a').split(',')[0].isupper() or re.match(r"^[A-ZÀ-Ý][\w'’\-]+(?:\s[A-ZÀ-Ý][\w'’\-]+)?,\s", bm.group('a'))) \
                    and plausible_author(bm.group('a').split(',')[0]) \
                    and not re.match(r'^[^,]+,\s*(?:Die|Der|Das|The|La|Le|Les|El|Il|Lo|Un|Une|Ein|Eine|A|An)\s', bm.group('a')) \
                    and not re.match(rf"^[^,]+,\s*{_MON}\s", bm.group('a'), re.I) and bm.group('a').split(',')[0].lower() not in PLACES_X:
                r, _ = bib.parse(dict(text=part, spans=[(part, False)], page=None, section=[]), None)
                if r.get('title'):
                    r['title'] = re.sub(rf'^\(?{Y}[a-z]?\)?[.,:]?\s*', '', r['title'])
                    sur = [s.title() if s.isupper() else s for s in r.get('surnames') or []]
                    row.update(rule='bib_inverted', kind=r.get('kind'), authors=r.get('authors') or [], surnames=sur,
                               title=r['title'], container=r.get('container'), year=int(bm.group('y1') or bm.group('y2')), conf=0.75)
                    if row['kind'] in ('unstyled', 'book_or_serial'):
                        row['kind'] = 'book'
                    out.append(row); works.append(len(out) - 1); last_full = len(out) - 1
                    for s in sur[:1]:
                        by_sur.setdefault(fold(s), []).append(len(out) - 1)
                    continue
            am0 = AUTHOR_EDS.match(part) or INIT_LIST.match(part) or AUTHOR.match(part)
            if ARCHIVAL.search(part[:60]) and not (am0 and plausible_author(am0.group('a'))) and not re.match(r'^\s*[“"«‘]', part):
                row.update(rule='archival', kind='primary', conf=0.6, year=(years_in(part) or [None])[0])
                out.append(row); last_full = len(out) - 1; continue
            c = strip_lead(part)
            r = parse_one(c)
            if r is None or r['rule'] == 'unparsed':
                if ARCHIVAL.search(c):
                    row.update(rule='archival', kind='primary', conf=0.6, year=(years_in(c) or [None])[0])
                    out.append(row); last_full = len(out) - 1; continue
                d = N.parse_citation([(c, False)], None)
                if d and d.get('title') and d.get('surnames') and d.get('kind') not in ('other', 'web'):
                    row.update(rule='diss_fallback', kind={'unstyled': 'book', 'book_or_serial': 'book'}.get(d['kind'], d['kind']),
                               authors=d['authors'], surnames=d['surnames'], title=d['title'], container=d.get('container'),
                               year=d.get('year'), conf=0.45)
                    out.append(row); works.append(len(out) - 1); last_full = len(out) - 1
                    by_sur.setdefault(fold(d['surnames'][0]), []).append(len(out) - 1)
                    continue
                row.update(rule='unparsed', kind='other', conf=0.0)
                out.append(row); continue
            if idem_auth and not r['authors']:
                r['authors'], r['surnames'] = idem_auth[0] or [], idem_auth[1] or []
                r['rule'] = 'idem+' + r['rule']
            row.update(r)
            if r['kind'] == 'short' or r['rule'] == 'opcit':
                row['ref'] = resolve_short(out, works, by_sur, r)
                row['kind'] = 'backref'
                row['conf'] = 0.75 if row['ref'] is not None else 0.25
                out.append(row); continue
            if r['kind'] == 'web':
                row['conf'] = 0.5
                out.append(row); continue
            row['conf'] = 0.6 if row['kind'] == 'primary' else confidence(row)
            if not row.get('surnames') and row.get('title'):   # fragment: maybe the full form appeared earlier in the item
                prev = resolve_title(out, works, row['title'])
                if prev is not None:
                    row['ref'] = prev
            out.append(row)
            if row['kind'] == 'primary':
                last_full = len(out) - 1
            elif row['title'] and row['kind'] != 'web':
                works.append(len(out) - 1); last_full = len(out) - 1
                for s in (row.get('surnames') or [])[:1]:
                    by_sur.setdefault(fold(s), []).append(len(out) - 1)
    for i in authordate_refs:
        r = out[i]
        cands = [w for w in works if out[w]['year'] == r['year'] and out[w]['surnames']
                 and fold(out[w]['surnames'][0]) == fold(r['surnames'][0] if r['surnames'] else '')]
        if len(cands) == 1 or (cands and r.get('suffix') is None):
            r['ref'] = cands[0]; r['conf'] = 0.8 if len(cands) == 1 else 0.55
    return out


def resolve_short(out, works, by_sur, r):
    sur = fold(r['surnames'][0]) if r.get('surnames') else None
    cands = by_sur.get(sur, []) if sur else []
    if not cands:
        return None
    if r.get('title'):
        short = SHORT_TAIL.sub('', r['title']).strip(' ,.…')
        tk = title_key(short)
        words = set(re.findall(r'[^\W\d_]{4,}', fold(short)))
        hit = []
        for w in cands:
            t = out[w].get('title') or out[w].get('container')
            if not t:
                continue
            fk = title_key(t)
            if fk.startswith(tk[:max(4, min(len(tk), 25))]) or tk.startswith(fk[:25]) or \
                    (words and words <= set(re.findall(r'[^\W\d_]{4,}', fold(t)))):   # 'Ubutwa' in 'A Few Notes on Ubutwa: ...'
                hit.append(w)
        if hit:
            return hit[-1]
        if len(tk) >= 4:
            return None
    return cands[-1]


SHORT_TAIL = re.compile(r'(?:[\s,]*(?:op\.?\s*cit|ouvr?\.?\s*cit|art\.?\s*cit|cit)\b\.?.*$)|(?:,\s*(?:[IVXLC]{1,6}|Ili|Bd\.\s*\d+|vol\.\s*\d+|t\.\s*[IVXLC\d]+)\s*$)', re.I)


def resolve_title(out, works, title):
    tk = title_key(title)
    if len(tk) < 6:
        return None
    for w in reversed(works):
        t = out[w].get('title')
        if t and out[w].get('surnames') and title_key(t)[:30] == tk[:30]:
            return w
    return None


def confidence(r):
    c = {'xml': 0.95, 'mla_article': 0.85, 'periodical_article': 0.6, 'bib_period': 0.8, 'bib_inverted': 0.75, 'frag_article': 0.35, 'periodical_issue': 0.6,
         'archival': 0.6, 'us_book': 0.85, 'article': 0.85, 'chapter': 0.8, 'comma_imprint': 0.7, 'german_imprint': 0.65,
         'frag_book': 0.5, 'article_loose': 0.55, 'quoted_other': 0.3}.get(r['rule'].replace('idem+', ''), 0.4)
    if r['rule'].endswith('frag_article'):
        return 0.5 if r.get('surnames') and r.get('container') and r.get('year') else 0.3
    if not r.get('title') or len(r['title']) < 4:
        c -= 0.3
    if r.get('title') and len(r['title']) > 250:
        c -= 0.3
    if not r.get('year'):
        c -= 0.15
    return round(max(c, 0.0), 2)
