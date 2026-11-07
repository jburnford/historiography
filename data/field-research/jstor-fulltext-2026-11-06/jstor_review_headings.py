"""Reviewed-book headings from JSTOR book-review text, by rules (deliverable 3, 2026-11-06).

A review's text begins with the heading of the book (or books) it reviews: author or editors, title, imprint,
pagination, price. 117,047 of the 317,561 reviews in the request have no title in JSTOR's metadata, so the metadata
route (scripts/key_jstor_reviews.py) cannot place them; the heading can.

The heading is found by its end, not its start: pages are shared with the neighbouring reviews, so the text before
a heading is the tail of the previous review. An anchor is a pagination mark ('Pp. 251.', '248 pp.', 'xvi + 266 p.',
'S. 312') with an imprint year near it and, within 400 characters before it, the family name of one of the metadata
names that is not the reviewer (the reviewer comes from review-signatures-rules.jsonl.gz). Two heading shapes:
  by      - 'Title. By Author[, and Author]. [Edited / Translated by ...] Place: Publisher, Year. Pp. ...'
            (AHR, JAH, JEH, HAHR, Church History, JMH ...); the title runs back to the previous sentence end, cut
            after a signature (institution phrase, all-capitals name) of the previous review
  name    - 'Author[, Author], eds, Title (Place: Publisher, Year. Pp. ...)' or 'AUTHOR. Title. Place, Year. Pp.'
            (EcHR, Isis, EHR, German and French journals); the title runs from after the names to the imprint
Collective reviews give several headings. A review without a found heading gives a row with `books: []`.

Output (E:, not committed; parsed fields only, no review text):
  /mnt/e/jstor-fulltext-2026-11-06/review-headings-rules.jsonl.gz
  iid, meta_title (metadata title or ''), books: [{authors, editors (bool), title, place, publisher, year, pages,
  shape, conf}], reviewer (creator)
Summary counts on stdout. With --sample FILE (lines of the reviews shard) it reads that file instead.

    python3 jstor_review_headings.py [--sample FILE] [--out PATH]
"""
import argparse, gzip, json, os, re, sqlite3, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from jstor_notes import normalize  # noqa: E402
from jstor_review_signatures import INST_PHRASE, creators, fold, fold1  # noqa: E402

SRC = '/mnt/e/jstor-fulltext-2026-11-06/reviews.jsonl.gz'
SIG = '/mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz'
DB = 'file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro'
OUT = '/mnt/e/jstor-fulltext-2026-11-06/review-headings-rules.jsonl.gz'

YEAR = r"(?:1[5-9]\d\d|20[0-2]\d)"
ROMAN = r"(?:[ivxlcdm]+|[IVXLCDM]+|[IVXLC][ivxlc]+)"
NUM = r"(?:[\dIl]?\d[\d,IlO]*|" + ROMAN + r")"   # OCR: 'I32', '4I6'
# pagination closing a heading: 'Pp. xv, 132', 'Pp. xvi + 486', '248 pp.', 'xvi + 266 p.', 'S. 312', '312 S.', 'XIV 266 p.'
PAGES = re.compile(
    rf"\b(?:Pp\.?|pp\.|PP[.\-]|Pages|S\.|Seiten|Págs?\.|págs?\.)\s*{NUM}(?:\s*(?:,|\+|-)\s*{NUM}){{0,3}}|"
    rf"\b{NUM}(?:\s*(?:,|\+|-)\s*{NUM}){{0,3}}\s*(?:pp\.?|PP[.\-]|p\.|pages|S\.|Seiten|págs?\.)(?=[\s,;.)\-]|$)")
PROSE = re.compile(r"[.)]\s+[A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[a-zà-ÿ]{2,}){3}")
SENT = re.compile(r"[.?!][”\"’')\]]?\s+(?=[\"“‘'(\[]?[A-ZÀ-Ý0-9])")
ABBR = re.compile(r"(?:\b(?:[A-ZÀ-Ý]|St|Mr|Mrs|Dr|Jr|Sr|Ste|Mt|Ft|Co|Vol|No|Ed|Eds|Rev|vs|U\.S|ca|c)\.)$")
BY = re.compile(r"(?:^|[.,;:]\s+)(?:(?:Edited|Translated|Compiled|Introduced|Selected|Written|Ed\.|Trans\.)\s+(?:and\s+\w+\s+)?)?"
                r"(?:[Bb]y|[Pp]ar|[Vv]on|[Pp]or|[Dd]i|[Dd]a|(?:[Ee]ds?|[Tt]rans|[Hh]rsg|[Hh]g|éds?)\.)\s+", re.U)
ROLE = re.compile(r"\b(?:Edited|Translated|Compiled|Introduction|Introduced|Foreword|Preface|Selected|Annotated|Illustrated)\b"
                  r"|\b(?:ed|eds|trans|tr|comp|hrsg|hg|éd|éds|dir)\.?(?=[\s,)])", re.I)
EDS = re.compile(r"\b(?:eds?|editors?|Hrsg|Hg|éds?|dir|comps?|coord)\b\.?", re.I)
_PLACE = r"(?!By\b|Edited\b|Translated\b)[A-ZÀ-Ý][\w'’\-]*(?:\s+(?:[A-ZÀ-Ý&][\w'’\-]*\.?|on|upon|am|an|de|del|la|sur|-sur-))" \
         r"{0,3}(?:,\s*[A-Z][\w.]{1,15}(?:\s[A-Z][\w.]+)?)?"
# a year that opens a date range belongs to a title ('From Strangers to Citizens: ..., 1550-1750')
IMPRINT = re.compile(rf"(?P<place>{_PLACE})\s*:\s*(?P<pub>[^:;()]{{2,90}}?),?\s*(?P<year>{YEAR})\b(?!\s?[-–]\s?\d)")
IMPRINT2 = re.compile(rf"(?P<place>{_PLACE})[.,]\s+(?P<pub>[A-ZÀ-Ý][^:;()]{{2,80}}?)[.,]\s+(?P<year>{YEAR})\b(?!\s?[-–]\s?\d)")
CAPS_NAME = re.compile(r"(?:\b[A-ZÀ-Ý][A-ZÀ-Ý'’.\-]+(?:\s+|$)){2,}")


PART = re.compile(r"^(?:vols?|volumes?|parts?|tomes?|t|bd|band|books?|no|nos|series|ser)\b\.?\s*(?:\d|[ivxlcIVXLC]+\b)|^\d", re.I)


def last_sentence_start(seg):
    """Offset in seg where a title before ' By ...' starts: after the last sentence end that is not an abbreviation
    ('St.', 'J.'), walking back while the piece after it cannot open a title (a volume or part designation, a
    lowercase word, one or two words: 'Foreign Relations ..., 1951. Vol. VII: Korea. Parts 1 & 2')."""
    starts = [0] + [m.end() for m in SENT.finditer(seg) if not ABBR.search(seg[:m.start() + 1])]
    i = len(starts) - 1
    while i > 0:
        piece = seg[starts[i]:].strip()
        if PART.match(piece) or piece[:1].islower() or len(piece.split()) <= 2:
            i -= 1
        else:
            break
    return starts[i]


CORE_INST = re.compile(r"(?:(?:[A-ZÀ-Ý][\w'’\-]*|of|the|at|and|&)\s+){0,5}(?:University|Universit[éàyä]\w*|Universidad|Universidade|College|"
                       r"Institute|Institut|School|Academy|Museum|Library|Seminary)\b(?:\s+(?:of|at|in)(?:\s+the)?(?:\s+[A-ZÀ-Ý][\w'’\-]*){1,3})?"
                       r"(?:,\s*[A-ZÀ-Ý][\w'’\-]*(?:\s+[A-ZÀ-Ý][\w'’\-]*)?)?")
FUNC = {'AND', 'THE', 'OF', 'IN', 'A', 'AN', 'FOR', 'ON', 'TO', 'AT', 'ET', 'LA', 'LE', 'LES', 'DES', 'DU', 'UND', 'DER', 'DIE', 'DAS', 'EL', 'Y'}
RUNNING_HEAD = re.compile(r"(?:\b[A-ZÀ-Ý][A-ZÀ-Ý'’.,\-]*\s+){1,8}\d{1,4}\s+(?=[A-ZÀ-Ý])|\b\d{1,4}\s+(?:[A-ZÀ-Ý][A-ZÀ-Ý'’.,\-]*\s+){1,8}(?=[A-ZÀ-Ý][a-zà-ÿ])")


def cut_previous_signature(seg):
    """Drop what precedes the title in a segment: a running head ('COLONIAL AND INDEPENDENCE PERIODS 571'), the
    previous review's signature (an institution, 'University of Wisconsin', or an all-capitals name, 'EMILY K. ABEL').
    A capitals run that holds 'AND', 'THE', 'OF' is a title in capitals ('FREUD AND THE AMERICANS:'), not a name."""
    cut = 0
    for m in RUNNING_HEAD.finditer(seg):
        if m.end() < len(seg) - 8:
            cut = max(cut, m.end())
    for m in CORE_INST.finditer(seg):
        before = seg[:m.start()].rstrip()
        if m.end() < len(seg) - 8 and not before.endswith(':') and seg[m.end():].lstrip()[:1].isupper():
            cut = max(cut, m.end())
    for m in CAPS_NAME.finditer(seg):
        toks = re.findall(r"[A-ZÀ-Ý'’.\-]+", m.group())
        rest = seg[m.end():]
        if (m.end() < len(seg) - 8 and rest[:1].isupper() and not rest.isupper() and not FUNC & set(toks)
                and not re.match(r"[A-ZÀ-Ý'’\-]+[:,]", rest) and len(toks) <= 5):
            cut = max(cut, m.end())
    return seg[cut:].lstrip(' ,;.')


def imprint(seg):
    ms = list(IMPRINT.finditer(seg)) or list(IMPRINT2.finditer(seg))
    m = ms[-1] if ms else None   # the imprint nearest the pagination
    if m:
        place, start = m.group('place'), m.start()
        cut = [x.end() for x in re.finditer(r"(?<=[A-Za-zÀ-ÿ]{2})(?<!\bSt)(?<!\bMt)(?<!\bFt)\.\s+(?=[A-ZÀ-Ý])", place)]
        if cut:   # 'RICHARD E. WENTZ. Washington, D.C' / 'Eighteenth-Century England. New Haven, Conn'
            start += cut[-1]; place = place[cut[-1]:]
        return place.strip(' ,.'), m.group('pub').strip(' ,.'), int(m.group('year')), start
    ys = list(re.finditer(rf"\b{YEAR}\b", seg))
    return None, None, (int(ys[-1].group()) if ys else None), None


def name_hits(text, ftext, names, lo, hi):
    """Occurrences of the names' family names in text[lo:hi] -> [(start, end, name)]."""
    out = []
    for n in names:
        fam = fold(n.split()[-1]) if n.split() else ''
        if len(fam) < 2:
            continue
        for m in re.finditer(r'(?<![a-z])' + re.escape(fam) + r'(?![a-z])', ftext[lo:hi]):
            out.append((lo + m.start(), lo + m.end(), n))
    return sorted(out)


def name_span_left(text, s, name):
    """Extend a family-name hit left over the person's given names and initials."""
    given = [fold(g).strip('.') for g in re.split(r'[\s\-]+', name)[:-1] if g.strip('.')]
    for _ in range(6):
        lm = re.search(r"([\w'’.\-]+)\s*$", text[max(0, s - 40):s])
        if not lm:
            break
        parts = [x for x in re.split(r'[.\-]', fold(lm.group(1))) if x]
        if parts and all(x in {'de', 'van', 'von', 'der', 'du', 'da', 'di', 'la', 'le', 'y', 'del'} or
                         any(g == x or (len(x) == 1 and g[:1] == x) for g in given) for x in parts):
            s -= len(lm.group(0))
        else:
            break
    return s


def hit_names_of(hits, upto):
    return {h[2] for h in hits if h[0] <= upto}


STATES = (r"Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|"
          r"Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|"
          r"Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|"
          r"Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|"
          r"Wyoming|D\.\s?C\.|Ontario|Quebec|British Columbia|Alberta|Manitoba|Saskatchewan|Nova Scotia|New Brunswick|"
          r"Ala\.|Ariz\.|Ark\.|Calif\.|Colo\.|Conn\.|Del\.|Fla\.|Ga\.|Ill\.|Ind\.|Kans\.|Ky\.|La\.|Md\.|Mass\.|Mich\.|"
          r"Minn\.|Miss\.|Mo\.|Mont\.|Nebr\.|Nev\.|N\.\s?[HJMYCD]\.|Okla\.|Ore\.|Pa\.|R\.\s?I\.|S\.\s?[CD]\.|Tenn\.|Tex\.|"
          r"Vt\.|Va\.|Wash\.|W\.\s?Va\.|Wis\.|Wyo\.|Ont\.|Que\.|B\.\s?C\.")
# the town of the previous review's signature before a title ('Provo, Utah Mesmerism and ...', 'Oxford, Ohio Pius IX.')
SIG_TOWN = re.compile(rf"^[A-ZÀ-Ý][\w.'’\-]*(?:\s+[A-ZÀ-Ý][\w.'’\-]*){{0,2}},\s+(?:{STATES})\s+(?=[A-ZÀ-Ý\"“'‘])")
HEAD_WORDS = re.compile(r"^(?:.{0,60}?\b(?:Book Reviews?|Reviews of Books|BOOK REVIEWS?|REVIEWS OF BOOKS|Comptes[- ]rendus\w*|COMPTES[- ]RENDUS\w*)\b\s*(?:[/|*]\s*)?(?:[\dIl]{1,4}\b\s*)?)")
DOI_HEAD = re.compile(r"^.*\b(?:doi|DOI)\s*:?\s*\S+\s+|^.*\bPrinted in [A-Z][\w ]+?(?:Kingdom|States|America)\s+")


def clean_title(t):
    t = re.sub(r"\s+", " ", t).strip(" ,;:.-–—")
    t = DOI_HEAD.sub("", t)
    t = HEAD_WORDS.sub("", t)
    t = SIG_TOWN.sub("", t)
    t = re.split(r"\.\s+(?=(?:Trans|Translated|Edited|Ed\.|With|Introduction|Foreword|Preface|Herausgegeben|Hrsg)\b)", t)[0]
    t = re.sub(r",?\s*(?:herausgegeben von|hrsg\.? von|edited by|ed\. by|translated by|trans\. by|par|von|by)\s*$", "", t, flags=re.I)
    t = re.sub(r"^(?:(?:eds?|eels|editors?|ed\. and trans|trans|tr|hrsg|hg|éds?|dir|comps?)\.?,?\s+(?:(?:and|&)\s+(?:trans|tr)\.?\s+)?)+", "", t, flags=re.I)
    t = re.sub(r"^(?:BOOK REVIEWS?|REVIEWS?|Book Reviews?|Reviews?|GENERAL|COMPTES RENDUS)\s+", "", t)
    return t


OCR_NUM = re.compile(r"\b(?=[\dIilOo]{4}\b)(?=(?:[^\d\s]*\d){2})[\dIilOo]{4}\b")


def fix_numbers(text):
    """'I95I' -> '1951', 'i87I' -> '1871', 'I9I0' -> '1910': four-character runs of digits and digit look-alikes with
    two real digits or more."""
    return OCR_NUM.sub(lambda m: m.group().translate(str.maketrans('IilOo', '11100')), text)


def headings(text, names, reviewer, journal=''):
    """-> list of book dicts found in text."""
    text = fix_numbers(text)
    if journal:   # the journal's name as a running head before a title ('Western Historical Quarterly If You Poison Us')
        text = re.sub(r"(?i)" + re.escape(journal) + r"\s+(?=[A-ZÀ-Ý])", " ", text)
    ftext = fold1(text)
    authors = [n for n in names if n != reviewer] or names
    books, used = [], -1
    for pm in PAGES.finditer(text):
        e = pm.end()
        if pm.start() <= used:
            continue
        lo = max(used + 1, pm.start() - 450)
        hits = name_hits(text, ftext, authors, lo, pm.start())
        if not hits:
            continue
        window = text[lo:pm.start()]
        place, pub, year, ipos = imprint(window)
        if pub is None:
            # the imprint after the pagination: 'Pp. xlii, 409. Royal Historical Society (Camden series). 1957.',
            # Isis 'XIV 266 p., 164 figs. GRIFFIN & Co., London, 1932.'; up to where the review's prose begins
            tail = text[e:e + 220]
            pr = PROSE.search(tail)
            p2, b2, y2, _ = imprint(tail[:pr.start()] if pr else tail)
            if b2:
                place, pub, year = p2, b2, y2
            elif y2:
                year = y2
        istart = lo + ipos if ipos is not None else pm.start()
        # shape 'by': '<title>. By <names>. <imprint>'
        by = None
        for bm in BY.finditer(text, lo, istart):
            if any(bm.end() <= h[0] <= bm.end() + 40 for h in hits):
                by = bm
                break
        if by:
            names_seg = text[by.end():istart]
            seg = text[lo:by.start() + (1 if text[by.start()] in '.,;:' else 0)]
            # after the previous review's signature or a running head the title may hold full stops
            # ('De abditis ... causis. The Hidden Causes of Disease'); otherwise it starts after the last sentence end
            after = cut_previous_signature(seg)
            if after != seg.lstrip(' ,;.') and len(after.split()) <= 45 and len(SENT.findall(after)) <= 3:
                title = clean_title(after)
            else:
                title = clean_title(cut_previous_signature(seg[last_sentence_start(seg):]))
            role = ROLE.search(text, by.end(), istart)
            nend = role.start() if role else istart
            hit_names = sorted({h[2] for h in hits if by.end() <= h[0] < nend})
            shape, eds = 'by', bool(re.match(r"\s*(?:Edited|[Ee]ds?\.|[Hh]rsg|[Hh]g\.|éd)", text[by.start():by.end()].lstrip('.,;: ')))
        else:
            # shape 'name': names first, then the title up to the imprint
            first = [h for h in hits if h[0] < istart]
            if not first:
                continue
            h0 = first[0]
            s = name_span_left(text, h0[0], h0[2])
            # all the names in a run of names ('A, B, and C, eds,')
            run_end = h0[1]
            for h in first[1:]:
                if h[0] - run_end < 40 and re.fullmatch(r"[\w\s.,'’\-&]*", text[run_end:h[0]]):
                    run_end = h[1]
            given = {fold(g).strip('.') for n in hit_names_of(first, run_end) for g in n.split()[:-1]}
            for k in (3, 2, 1):   # 'REININGHAUS, WILFRIED.' / 'Smith, J. A.': the longest run of the person's given names
                inv = re.match(rf",\s*((?:[A-ZÀ-Ý][\w'’\-]*\.?\s*){{{k}}})", text[run_end:])
                toks = [fold(x).strip('.') for x in inv.group(1).split()] if inv else []
                if toks and all(any(g == x or (len(x) == 1 and g[:1] == x) for g in given) for x in toks):
                    run_end += len(inv.group(0).rstrip())
                    break
            em = re.match(r"(?i:(?:,?\s*(?:Jr|Sr)\.?)?[\s.,]*(?:\(?(?:eds?|Hrsg|Hg|éds?|dir|comps?)\.?\)\s*[.,:;\-–—]*|(?:eds?|Hrsg|Hg|éds?|dir|comps?)\.?\s*[.,:;\-–—]+)?\s*[.,:;\-–—]*\s*)", text[run_end:])
            if not em:
                continue
            eds = bool(EDS.search(em.group()))
            tstart = run_end + em.end()
            tend = istart
            par = text.rfind('(', tstart, istart + 1)
            if par > tstart:
                tend = min(tend, par)
            if re.match(r"\s*['’]s\b|\s*[a-zà-ÿ]", text[run_end:run_end + 4]):
                continue   # a possessive or a sentence ('Johns's entire enterprise'), not a heading
            im = re.search(rf"\.\s+{_PLACE}\s*:", text[tstart:tend])
            if im:   # 'Title. London: British Academic Press; distributed by ...' (an imprint the regex missed)
                tend = tstart + im.start() + 1
            title = clean_title(text[tstart:tend])
            title = re.split(r"\.\s+(?=(?:\d|" + ROMAN + r"\b|[A-Z][a-z]+\s+(?:and|ed|by)\b))", title)[0]
            hit_names = sorted({h[2] for h in first if h[0] <= run_end})
            shape = 'name'
            if s < pm.start() - 450:
                continue
        if not title or len(title) < 4 or len(title) > 300:
            continue
        conf = 0.9 if (pub and year and len(title.split()) >= 2) else 0.7 if (pub or year) else 0.5
        if len(title.split()) > 40:
            conf = 0.4
        books.append(dict(authors=hit_names, editors=eds, title=title, place=place, publisher=pub, year=year,
                          pages=pm.group().strip(), shape=shape, conf=conf))
        used = e
    return books


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--sample')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()
    c = sqlite3.connect(DB, uri=True)
    meta = {i.split(':')[-1]: (t or '', cr or '', j or '') for i, t, cr, j in
            c.execute("select item_id, title, creators_string, journal_title from records where genre='book_review_as_deposited'")}
    reviewer = {}
    for line in gzip.open(SIG, 'rt', encoding='utf-8'):
        r = json.loads(line)
        reviewer[r['iid']] = r['creator']
    src = open(args.sample, encoding='utf-8') if args.sample else gzip.open(SRC, 'rt', encoding='utf-8')
    tmp = args.out + '.tmp'
    C = Counter(); t0 = time.time()
    op = gzip.open if args.out.endswith('.gz') else open
    with src as f, op(tmp, 'wt', encoding='utf-8') as o:
        for line in f:
            iid = line[9:45]
            r = json.loads(line)
            t, cr, journal = meta.get(iid, ('', '', ''))
            names = creators(cr)
            text = normalize(' '.join(p for p in r.get('full_text') or [] if isinstance(p, str)))
            books = headings(text, names, reviewer.get(iid), journal) if names else []
            mt = re.sub(r'^\s*book reviews?\s*:\s*', '', t.strip(), flags=re.I)
            C['reviews'] += 1; C['untitled'] += not mt
            C['with_heading'] += bool(books); C['untitled_with_heading'] += bool(books) and not mt
            C['books'] += len(books); C['collective'] += len(books) > 1
            o.write(json.dumps(dict(iid=iid, meta_title=mt, reviewer=reviewer.get(iid), books=books), ensure_ascii=False) + '\n')
            if C['reviews'] % 50000 == 0:
                print(dict(C), round(time.time() - t0), flush=True)
    os.replace(tmp, args.out)
    print(json.dumps(dict(C), indent=1), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
