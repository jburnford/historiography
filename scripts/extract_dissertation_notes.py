#!/usr/bin/env python3
"""Reconstruct a dissertation's bibliography from its notes (footnotes or endnotes).

Many History theses cite only in notes: no closing bibliography, or one that lists archives
and leaves the secondary literature in the notes. This reads the notes and rebuilds the
bibliography as one entry per cited work, in the ``entries.jsonl`` shape of
``extract_dissertation_bibliographies.py``, plus how often the notes cite it.

1. **Find the notes.** Footnotes: the block at the foot of a page set in a smaller size than
   the body text, starting with a note number (a superscript span or a leading number).
   Endnotes: pages headed 'Notes' / 'Endnotes' (chapter ends or the back of the thesis).
   A note number is accepted only in sequence (the next number, a restart at 1, or a small
   jump), so years and table figures at the start of a line do not open notes.
2. **Cut citations.** A note is split at top-level semicolons. *Ibid.*, *idem*, *id.* and
   *op. cit.* forms do not add a work; they add a citation to the work they refer to
   (the previous citation, or the latest work by the named author).
3. **Parse.** Each citation goes through the bibliography parser (italic and quoted titles,
   containers, years, kinds). Notes name authors in natural order ('Arthur S. Morton'), so
   the author is re-read from the text before the title: commentary and 'See' / 'Voir' /
   'cited in' are dropped and only a name list is kept.
4. **One entry per work.** Citations are merged within the thesis by first-author surname
   and title key (short titles join the full title that begins the same way), keeping the
   fullest form, the number of citations and the first note page.

Output (derived bibliographic metadata only; the PDF text stays local):
``<out>/notes-extraction.jsonl`` and ``<out>/notes-entries.jsonl``. Entries carry
``from_notes: true``, ``citations`` and ``section: ['Notes']``. They are kept apart from the
bibliography files until the notes audit decides how they enter the graph.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import re
import signal
import statistics
import sys

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_dissertation_bibliographies as bib  # noqa: E402
from build_dissertation_citation_graph import fold, title_key  # noqa: E402
from dissertation_names import split_name  # noqa: E402

NOTES_HEADING = re.compile(r'^(?:[IVX\d]+\.?\s+)?(?:notes?|endnotes|notes\s+(?:to|for|of)\b.{0,40}|notes\s+de\s+fin|'
                           r'anmerkungen|notas|noter)\s*:?$', re.I)
NUMBERED = re.compile(r'^\s*(\d{1,4})(?:\s*[.)]\s*|\s+|(?=[A-ZÀ-Ý][a-zà-ÿ]))(?=\S)')  # also OCR-glued '4For'
IBID = re.compile(r'^\s*(?:ibid(?:em)?|ib\.|id(?:em)?\b\.?|eadem|ebd|ebenda)\b\.?', re.I)
OP_CIT = re.compile(r'\b(?:op\.?\s*cit|loc\.?\s*cit|art\.?\s*cit|ouvr\.?\s*cit|a\.\s*a\.\s*O)\b\.?', re.I)
LEAD = re.compile(r'^(?:see\s+(?:also|especially|for\s+example|e\.g\.)?|see|cf\.?|voir(?:\s+aussi|\s+notamment)?|vgl\.?(?:\s+(?:hierzu|dazu|auch|etwa|ferner|u\.\s?a\.|z\.\s?B\.))*|siehe|'
                  r'v\.|also|and|et|e\.g\.,?|for\s+example,?|quoted\s+in|cited\s+in|cité\s+(?:dans|par)|reproduced\s+in|'
                  r'reprinted\s+in|in|dans|à\s+ce\s+sujet,?|on\s+this,?\s+see)\s*:?\s+', re.I)
SIGNAL_WORD = re.compile(r'(?:see|voir|vgl|cf|similarly|thus|however|also|on|in|for|as|according|note|cited|quoted|histoire|history|'
                         r'hist[óo]ria|geschichte|storia|ibid|idem|the|le|la|les|der|die|das|el|il|this|these|cette|ce|une?|an?)', re.I)
NAME_TOKEN = r"(?:[A-ZÀ-ÝĀ-Ž][\w'’\-]*\.?|(?:de|du|des|la|le|van|von|der|den|di|da|dos|del|y|St\.)(?=\s))"
ONE_NAME = rf"{NAME_TOKEN}(?:\s*{NAME_TOKEN}){{0,5}}(?:,?\s+(?:Jr|Sr|II|III)\.?)?"
NAME_LIST = re.compile(rf"^({ONE_NAME})((?:\s*(?:,\s*(?:and|et|&|und|y)?|\s(?:and|et|&|und|y))\s+{ONE_NAME})*)"
                       r"(?:,?\s*\(?(?:eds?|éds?|dir|dirs|Hg|Hrsg|comps?|trans)\.?\)?)?$")
SPLIT_NAMES = re.compile(r'\s*(?:,\s*(?:and|et|&|und|y)\s+|\s+(?:and|et|&|und|y)\s+|,\s*)')
EDITOR = re.compile(r',?\s*\(?(?:eds?|éds?|dir|dirs|Hg|Hrsg|comps?|trans)\.?\)?\s*$', re.I)
PARTICLE = {'de', 'du', 'des', 'la', 'le', 'van', 'von', 'der', 'den', 'di', 'da', 'dos', 'del'}


def _letters(t):
    return ''.join(c for c in t if c.isalpha())


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout('notes extraction exceeded time limit')


def size_of(spans):
    """Text size of a line, ignoring a leading superscript note number."""
    sized = [(len(t.strip()), s) for t, *_, s in spans if t.strip()]
    if len(sized) > 1 and re.fullmatch(r'\d{1,4}', spans[0][0].strip() or 'x'):
        sized = sized[1:]
    total = sum(n for n, _ in sized)
    return sum(n * s for n, s in sized) / total if total else 0


def lead_number(line):
    """(number, text after it) when the line opens a note, else None."""
    spans = [s for s in line['spans'] if s[0].strip()]
    if not spans:
        return None
    first = spans[0][0].strip()
    if len(spans) > 1 and re.fullmatch(r'\d{1,4}\.?', first) and spans[0][3] < spans[1][3] * 0.9:
        return int(first.rstrip('.')), line['text'].strip()[len(first):].strip()
    m = NUMBERED.match(line['text'])
    return (int(m.group(1)), line['text'][m.end():]) if m else None


def in_sequence(n, last):
    return last is None and n <= 3 or last is not None and (last < n <= last + 3 or n == 1)


def body_size(doc):
    sizes = Counter()
    n = len(doc)
    for i in range(int(n * 0.15), n, max(1, n // 30)):
        for line in bib.lines_of(doc[i]):
            for t, _, _, s in line['spans']:
                sizes[round(s, 1)] += len(t)
    return sizes.most_common(1)[0][0] if sizes else 0


def footnote_lines(page, body):
    """Lines of the footnote block at the foot of a page (bottom-up run of small lines)."""
    h = page.rect.height
    lines = bib.lines_of(page)
    block = []
    for line in reversed(lines):
        size = size_of(line['spans'])
        if line['y0'] < h * 0.3 or size >= body * 0.95:
            break
        block.append(line)
    block.reverse()
    while block and lead_number(block[0]) is None:  # small-size body text (quotations, captions) above the notes
        block.pop(0)
    if block:
        return block
    # Scanned typescripts: OCR sizes are erratic, so take the block below the widest vertical
    # gap in the lower part of the page when it opens with a note number.
    low = [l for l in lines if l['y0'] > h * 0.4]
    gaps = [(b['y0'] - a['y1'], i + 1) for i, (a, b) in enumerate(zip(low, low[1:]))]
    if len(gaps) < 2:
        return []
    usual = statistics.median(g for g, _ in gaps)
    gap, at = max(gaps)
    if gap > max(6, usual * 1.8) and lead_number(low[at]) is not None:
        return low[at:]
    return []


def endnote_pages(doc):
    """Page ranges headed 'Notes': (start, end) pairs, each ending at the next page headed otherwise."""
    heads = {}
    for i in range(len(doc)):
        top = [t.strip() for t in doc[i].get_text().splitlines() if t.strip()][:4]
        if any(NOTES_HEADING.match(t) for t in top):
            heads[i] = 'notes'
        elif any(len(t) < 60 and (bib.STOP.match(t) or bib.START.match(t) or re.match(r'^(?:chapter|chapitre|kapitel|capítulo)\b', t, re.I))
                 for t in top[:2]):
            heads[i] = 'other'
    ranges, start = [], None
    for i in range(len(doc) + 1):
        kind = heads.get(i)
        if start is not None and kind == 'other':
            ranges.append((start, i))
            start = None
        if kind == 'notes' and start is None:
            start = i
    if start is not None:
        ranges.append((start, min(len(doc), start + 80)))
    return ranges


def segment(lines, notes, last):
    """Append notes cut from ``lines`` (number-opened, in sequence); returns the last number."""
    cur = notes[-1] if notes else None
    for line in lines:
        lead = lead_number(line)
        if lead and in_sequence(lead[0], last):
            last = lead[0]
            cur = dict(number=lead[0], page=line['page'], spans=[])
            notes.append(cur)
            spans = [s for s in line['spans'] if s[0].strip()]
            first = spans[0][0].strip()
            skip = len(first) if re.fullmatch(r'\d{1,4}\.?', first) else 0
            text = line['text'].strip()
            if skip == 0:
                m = NUMBERED.match(text)
                skip = m.end() if m else 0
            # rebuild the line's spans without the number
            out, pos = [], 0
            for t, ital, *_ in line['spans']:
                a = max(0, skip - pos) if pos < skip else 0
                if pos + len(t) > skip:
                    out.append((t[a:] if pos < skip else t, ital))
                pos += len(t)
            cur['spans'].extend(out)
            continue
        if cur is None:
            continue
        if cur['spans'] and cur['spans'][-1][0].endswith('-') and line['text'][:1].islower():
            t, i = cur['spans'][-1]
            cur['spans'][-1] = (t[:-1], i)
        elif cur['spans']:
            cur['spans'].append((' ', False))
        cur['spans'].extend((s[0], s[1]) for s in line['spans'])
    return last


def split_citations(spans):
    """Cut a note's spans at semicolons outside parentheses and quotes."""
    parts, cur, depth, quote = [], [], 0, False
    for text, ital in spans:
        buf = ''
        for ch in text:
            if ch in '([':
                depth += 1
            elif ch in ')]':
                depth = max(0, depth - 1)
            elif ch in '“”«»"':
                quote = not quote if ch == '"' else ch in '“«'
            if ch == ';' and depth == 0 and not quote:
                cur.append((buf, ital))
                parts.append(cur)
                cur, buf = [], ''
            else:
                buf += ch
        if buf:
            cur.append((buf, ital))
    parts.append(cur)
    out = []
    for part in parts:
        out += split_run_on(part)
    return [p for p in out if ''.join(t for t, _ in p).strip()]


ABBREV = re.compile(r'(?:pp?|vol|vols|no|nos|ed|eds|éd|dir|trad|trans|chap|art|cf|vgl|st|mr|mrs|dr|ms|mss|fol|ff?|t|ibid|id|cit|op|loc|etc|ca|c)', re.I)
SIGNALS = ('see also', 'see', 'voir aussi', 'voir', 'cf.', 'vgl.', 'also')
JOINERS = {'and', 'et', '&', 'und', 'y'}


def next_citation(seg):
    """True when ``seg`` (text between a sentence end and the next title) is a short name list ending
    in a comma: 'Freundlich, ', 'See also Alain Corbin, ', 'A. S. Morton and J. Smith, '. Plain token
    checks: the earlier regular expression backtracked exponentially on long notes."""
    seg = seg.strip()
    if not seg.endswith(',') or len(seg) > 90:
        return False
    seg = seg[:-1].strip()
    low = seg.lower()
    for sig in SIGNALS:
        if low.startswith(sig + ' '):
            seg = seg[len(sig):].strip()
            break
    toks = seg.replace(',', ' , ').split()
    if not 1 <= len(toks) <= 14:
        return False
    names = 1 + sum(t in (',',) or t.lower() in JOINERS for t in toks)
    return names <= 5 and all(t == ',' or t.lower() in JOINERS or t.lower() in PARTICLE or t[:1].isupper() for t in toks)


def split_run_on(spans):
    """Cut a citation where a sentence ends and a new one starts ('…, 1987, p. 3. Freundlich, *Le
    monde du jeu*, 1995'): the text after '. ' up to the next italic or quoted title is a name list
    ending in a comma."""
    raw = ''.join(t for t, _ in spans)
    starts = sorted({a for a, _ in bib.italic_runs(spans)} | {i for i, c in enumerate(raw) if c in '“«"'})
    cuts = []
    for m in re.finditer(r'\.\s+(?=[A-ZÀ-Ý])', raw):
        word = re.search(r'(\S+)$', raw[:m.start()])
        if not word or ABBREV.fullmatch(word.group(1)) or re.fullmatch(r'[A-ZÀ-Ý]', word.group(1)):
            continue  # 'p. 3', 'vol. II', an initial 'A. S.'
        nxt = next((t for t in starts if t > m.end()), None)
        if nxt is not None and nxt - m.end() <= 120 and next_citation(raw[m.end():nxt]):
            cuts.append(m.end())
    if not cuts:
        return [spans]
    out, cur, pos, k = [], [], 0, 0
    for t, ital in spans:
        while k < len(cuts) and pos <= cuts[k] < pos + len(t):
            cut = cuts[k] - pos
            cur.append((t[:cut], ital))
            out.append(cur)
            cur, t, pos, k = [], t[cut:], cuts[k], k + 1
        cur.append((t, ital))
        pos += len(t)
    out.append(cur)
    return out


def strip_lead(spans):
    """Drop commentary and 'See'/'Voir' before a citation: keep from the last sentence or colon break
    before the title (first italic or quote) and then leading signal words."""
    raw = ''.join(t for t, _ in spans)
    runs = bib.italic_runs(spans)
    q = next((i for i, c in enumerate(raw) if c in '“"«'), None)
    title_at = min([p for p in (runs[0][0] if runs else None, q) if p is not None], default=None)
    cut = 0
    if title_at is None:  # unstyled citations ('Vgl. hierzu: WEIBEZAHN, Ingrid: Missale'): signal words only
        title_at = len(raw)
    else:
        for m in re.finditer(r'(?<![A-ZÀ-Ý])[.:]\s+(?=[A-ZÀ-Ý])|:\s*', raw[:title_at]):
            if m.end() < title_at:
                cut = m.end()
    while (m := LEAD.match(raw[cut:title_at])):
        cut += m.end()
    if not cut:
        return spans
    out, pos = [], 0
    for t, ital in spans:
        if pos + len(t) > cut:
            out.append((t[max(0, cut - pos):], ital))
        pos += len(t)
    return out


def note_authors(author):
    """Natural-order author names from the text before a title, or [] when it is not a name list."""
    if not author:
        return []
    a = re.sub(r',?\s*\bet\s+al\b\.?', '', author).strip(' ,.')
    a = re.sub(r'^(?:by|par|von)\s+', '', a, flags=re.I)
    while (m := LEAD.match(a + ' ')):  # 'See Said', 'Voir Closset', 'Vgl. Meyer'
        a = (a + ' ')[m.end():].strip()
    if not a or SIGNAL_WORD.fullmatch(a.split()[0].strip('.,:')):
        return []
    if ',' in a and re.fullmatch(r"[A-ZÀ-Ý][\w'’\-]+(?:\s[A-ZÀ-Ý][\w'’\-]+)?,\s+[A-ZÀ-Ý][\w.'’\- ]{0,30}", a) and \
            not re.search(r",\s+[A-ZÀ-Ý][\w'’\-]+\s+[A-ZÀ-Ý][\w'’\-]{2,}$", a):
        return [a]  # an inverted 'Surname, Given' (some note styles)
    if len(a) > 100 or not NAME_LIST.match(a):
        return []
    names = [EDITOR.sub('', n).strip(' ,.') for n in SPLIT_NAMES.split(EDITOR.sub('', a))]
    names = [n for n in names if n and not re.fullmatch(r'(?:Jr|Sr|II|III)\.?', n)]
    return names if 0 < len(names) <= 6 else []


def canonical(name):
    """'Surname, Given' and the key surname of a note author ('Arthur S. Morton', 'BOURDIEU Pierre',
    'HALBWACHS F.', 'Morton, A. S.')."""
    name = re.sub(r',?\s+(?:Jr|Sr|II|III)\.?$', '', name).strip(' ,.')
    if ',' in name:
        return name, name.split(',')[0].strip()
    split = split_name(name, 'natural')
    if not split:
        return name, name
    return f'{split[0]}, {split[1]}', split[0]


PLACES = {'london', 'oxford', 'cambridge', 'paris', 'new york', 'baltimore', 'chicago', 'toronto', 'montreal', 'montréal', 'québec',
          'quebec', 'ottawa', 'berlin', 'leipzig', 'munich', 'münchen', 'princeton', 'boston', 'philadelphia', 'berkeley', 'new haven',
          'edinburgh', 'dublin', 'rome', 'roma', 'milan', 'milano', 'madrid', 'barcelona', 'lisbon', 'lisboa', 'amsterdam', 'leiden',
          'stockholm', 'vienna', 'wien', 'frankfurt', 'stuttgart', 'göttingen', 'heidelberg', 'lyon', 'bruxelles', 'brussels', 'genève',
          'geneva', 'washington', 'vancouver', 'winnipeg', 'halifax', 'kingston', 'sydney', 'melbourne', 'tokyo', 'beijing', 'mexico',
          'buenos aires', 'são paulo', 'rio de janeiro', 'ithaca', 'durham', 'stanford', 'bloomington', 'urbana', 'lincoln', 'norman',
          'madison', 'ann arbor', 'austin', 'athens', 'firenze', 'florence', 'torino', 'turin', 'bologna', 'napoli', 'naples'}
UNSTYLED = re.compile(r"^(?P<author>[^,;:()“”«»\"]{3,70}?),\s+(?P<title>[^,;()“”«»\"]{6,220}?)\s*(?=,|\(|\.\s|\s(?:pp?|vol|t|S)\.\s?\d|$)")
TITLE_TAIL = re.compile(r'[\s,.]*\b(?:op|loc|art|ouvr)\.?\s*ci[tf]\b\.?.*$', re.I)
TITLE_HEAD = re.compile(r'^\s*\(?(?:hrsg|hg|eds?|éds?|dir)\.?\)?\s*[:.]\s*', re.I)


def parse_citation(spans, page):
    text = ''.join(t for t, _ in spans)
    if len(text.strip()) < 8:
        return None
    r, _ = bib.parse(dict(text=text, spans=spans, page=page, section=['Notes']), None)
    author = r.get('author')
    if author and r.get('title'):
        # note style puts a comma (or colon) between author and title: 'Adam Thom « fait confiance »' is prose
        at = text.find(r['title'][:20])
        if at > 0 and not re.search(r'[,:.]\s*[“"«‘]?\s*$', text[:at]):
            author = None
    if r.get('title'):
        r['title'] = TITLE_HEAD.sub('', TITLE_TAIL.sub('', r['title'])).strip(' ,.;:')
        words = re.findall(r'[^\W\d_]{3,}', r['title'])
        if not words or r['title'][:1].isdigit() or len(r['title']) < 4:
            r['title'] = None  # author-date or page residue ('70 et Rischel 1999, 179'), not a title
    if author and re.fullmatch(r'[A-Z][a-z]{1,5}\.?', author.strip()) and r.get('title') and len(r['title']) <= 14:
        return None  # classical abbreviations: 'Cic. Off.', 'Suet. Iul.'
    if not bib.italic_runs(spans) and not any(c in text for c in '“«"') and \
            (r.get('kind') in ('other', 'unstyled', 'book_or_serial') or not note_authors(author)):
        # unstyled note form (typescripts, OCR): 'Robert Sellar, History of the County of Huntingdon, pp. 512-5'
        m = UNSTYLED.match(text.strip())
        lone = m and re.fullmatch(r'[A-Z]{2,6}', m.group('author').strip())
        if lone:
            r['kind'] = 'archival'  # 'PAM, Journal of Peter Garrioch': a repository acronym, not an author
        elif m and len(m.group('author').split()) >= 2 and note_authors(m.group('author').strip()) \
                and len(re.findall(r'[^\W\d_]{3,}', m.group('title'))) >= 2:
            rest = text[m.end('title'):]
            years = bib.pub_years(rest)
            r.update(author=m.group('author').strip(), title=m.group('title').strip(' .'), container=None,
                     year=int(years[0]) if years else r.get('year'), kind='unstyled')
            author = r['author']
    if author and author.strip(' ,.').lower() in PLACES:
        author = None  # a place of publication before a quoted title, not an author
    canon = [canonical(n) for n in note_authors(author)]
    authors, surnames = [c[0] for c in canon], [c[1] for c in canon]
    if surnames and len(_letters(surnames[0])) < 2:
        authors, surnames = [], []
    if surnames and all(re.fullmatch(r'[A-Z]{2,6}', s) for s in surnames) and len(surnames) > 1:
        r['kind'] = 'archival'  # repository and series acronyms ('PAM, DA, MGQC'), not authors
    r.update(authors=authors, surnames=surnames, section_side='unspecified')
    return r


def reconstruct(notes):
    """Citations from notes -> one entry per work with citation counts."""
    works, order, last_work, by_surname = {}, [], None, {}
    cites = 0
    for note in notes:
        for part in split_citations(note['spans']):
            raw = ''.join(t for t, _ in part).strip()
            ib = IBID.match(raw)
            if ib and not any(b - a > 15 for a, b in bib.italic_runs(part) if a >= ib.end()):
                if last_work:
                    works[last_work]['citations'] += 1
                    cites += 1
                continue
            if OP_CIT.search(raw) and not bib.italic_runs(part):
                m = re.match(r"^\s*(?:[A-ZÀ-Ý][\w.'’\-]*\s+){0,3}([A-ZÀ-Ý][\w'’\-]+)\s*,?\s*(?:op|loc|art|ouvr)", raw)
                key = by_surname.get(fold(m.group(1))) if m else None
                if key:
                    works[key]['citations'] += 1
                    last_work = key
                    cites += 1
                continue
            r = parse_citation(strip_lead(part), note['page'])
            if not r or not r.get('title') or not r.get('surnames') or r['kind'] in ('other', 'web'):
                continue
            sur, tk = fold(r['surnames'][0]), title_key(r['title'])
            if not sur or len(tk) < 3:
                continue
            if r['kind'] in ('article', 'chapter'):
                tk += '|a'
            key = (sur, tk)
            if key not in works:  # a short title joins a full one that begins the same way, and vice versa
                same = [k for k in works if k[0] == sur and k[1].endswith('|a') == tk.endswith('|a')
                        and (k[1].startswith(tk.removesuffix('|a')) or tk.startswith(k[1].removesuffix('|a')))
                        and min(len(k[1]), len(tk)) >= 4]
                if same:
                    key = same[0]
            cites += 1
            if key in works:
                w = works[key]
                w['citations'] += 1
                if (r['year'] and not w['year']) or len(r['raw']) > len(w['raw']) and (r['year'] or not w['year']):
                    keep = w['citations'], w['first_page']
                    w.update(r)
                    w['citations'], w['first_page'] = keep
                if len(tk) > len(key[1]) and tk.startswith(key[1].removesuffix('|a')):
                    w['title'] = r['title']
            else:
                works[key] = dict(r, citations=1, first_page=r['page'])
                order.append(key)
            last_work = key
            by_surname[sur] = key
    return [works[k] for k in order], cites


def _process(path):
    fitz.TOOLS.mupdf_display_errors(False)
    doc = fitz.open(path)
    pages = len(doc)
    text_chars = sum(len(doc[i].get_text()) for i in range(0, pages, max(1, pages // 12)))
    if text_chars < 2000:
        return dict(file=str(path), pages=pages, status='no_text_layer'), []
    body = body_size(doc)
    foot, last = [], None
    for i in range(pages):
        last = segment(footnote_lines(doc[i], body), foot, last)
    end = []
    for a, b in endnote_pages(doc):
        lines = [l for i in range(a, b) for l in bib.lines_of(doc[i])]
        lines = [l for l in lines if not NOTES_HEADING.match(l['text'].strip())]
        segment(lines, end, None)
    notes, form = (foot, 'footnotes') if len(foot) >= len(end) else (end, 'endnotes')
    works, cites = reconstruct(notes)
    status = 'parsed_notes' if len(works) >= 10 else 'few_note_works' if notes else 'no_notes'
    info = dict(file=str(path), pages=pages, status=status, notes_form=form, notes=len(notes), footnotes=len(foot), endnotes=len(end),
                citations=cites, works=len(works), body_size=body, kinds=dict(Counter(w['kind'] for w in works)))
    return info, works


def process(path, limit=600):
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(limit)
    try:
        return _process(Path(path))
    except Exception as exc:  # one malformed PDF must not stop the batch
        return dict(file=str(path), status='notes_error', error=f'{type(exc).__name__}: {exc}'), []
    finally:
        signal.alarm(0)


def run(job):
    d, path = job
    info, works = process(path)
    info.update(institution=d['institution'], id=d['id'], file=d['file'])
    return info, works


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--status', nargs='*', default=['no_bibliography_heading', 'few_entries', 'suspect_span'],
                        help='read the notes of PDFs whose bibliography extraction ended with these statuses')
    parser.add_argument('--files', type=Path, help='file listing PDF paths relative to --out (overrides --status)')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--suffix', default='', help="write notes-extraction<suffix>.jsonl / notes-entries<suffix>.jsonl")
    parser.add_argument('--rebuild', action='store_true', help='redo PDFs already in the notes log')
    parser.add_argument('--retry-status', nargs='*', default=[], help='redo PDFs whose last notes status is one of these')
    parser.add_argument('--dest', type=Path, help='directory for the two output files (default --out)')
    parser.add_argument('--pdf-root', type=Path, help='read the PDFs (paths relative to --out, e.g. pdf/laval/x.pdf) under this '
                                                       'directory instead, such as a temporary local copy (default --out)')
    args = parser.parse_args()
    out = args.out
    last = {}
    for line in (out / 'extraction.jsonl').open():
        try:
            x = json.loads(line)
        except json.JSONDecodeError:
            continue
        last[x['file']] = x
    if args.files:
        wanted = [l.strip() for l in args.files.open() if l.strip()]
        jobs = [dict(institution=last[f].get('institution'), id=last[f].get('id'), file=f) for f in wanted if f in last]
    else:
        jobs = [dict(institution=x.get('institution'), id=x.get('id'), file=f) for f, x in last.items()
                if x['status'] in args.status and f.endswith('.pdf')]
    dest = args.dest or out
    dest.mkdir(parents=True, exist_ok=True)
    log_path, ent_path = dest / f'notes-extraction{args.suffix}.jsonl', dest / f'notes-entries{args.suffix}.jsonl'
    done = set()
    if log_path.exists() and not args.rebuild:
        prior = {}
        for l in log_path.open():
            if l.strip():
                x = json.loads(l)
                prior[x['file']] = x['status']
        done = {f for f, st in prior.items() if st not in args.retry_status}
    jobs = [j for j in jobs if j['file'] not in done]
    root = args.pdf_root or out
    missing = [j['file'] for j in jobs if not (root / j['file']).exists()]
    if jobs and len(missing) > len(jobs) * 0.1:
        sys.exit(f'{len(missing)} of {len(jobs)} PDFs are not reachable (e.g. {missing[0]}); is the PDF drive mounted? Nothing written.')
    print(f'{len(jobs)} PDFs', flush=True)
    # A rebuild writes to temporary files renamed at the end, so an interrupted run keeps the old output.
    log_out = log_path.with_suffix('.jsonl.tmp') if args.rebuild else log_path
    ent_out = ent_path.with_suffix('.jsonl.tmp') if args.rebuild else ent_path
    mode = 'w' if args.rebuild else 'a'
    with ProcessPoolExecutor(args.workers) as pool, log_out.open(mode) as log, ent_out.open(mode) as ent:
        futures = [pool.submit(run, (j, root / j['file'])) for j in jobs]
        for k, f in enumerate(as_completed(futures)):
            info, works = f.result()
            for n, w in enumerate(works):
                w.update(dissertation=info['id'], institution=info['institution'], n=n, from_notes=True)
                ent.write(json.dumps(w, ensure_ascii=False) + '\n')
            log.write(json.dumps(info, ensure_ascii=False) + '\n')
            log.flush()
            ent.flush()
            print(k, info['institution'], info['status'], info.get('notes'), info.get('works'), flush=True)
    if args.rebuild:
        errors = sum('"notes_error"' in l for l in log_out.open())
        if errors > max(5, len(jobs) * 0.05):
            sys.exit(f'{errors} of {len(jobs)} PDFs failed (drive dropped?); kept the previous output, new run left in {log_out.name}')
        log_out.replace(log_path)
        ent_out.replace(ent_path)


if __name__ == '__main__':
    main()
