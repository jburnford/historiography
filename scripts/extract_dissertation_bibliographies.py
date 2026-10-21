#!/usr/bin/env python3
"""Extract and parse the bibliographies of downloaded History doctorates.

For each PDF in ``<out>/pdf`` this locates the closing bibliography (the first
bibliography-type heading in the back part of the document, ending at an index,
appendix or vita), splits it into entries using hanging indents, vertical gaps and
entry-start patterns, keeps the subheading path (e.g. Primary Sources > Archives)
and parses each entry with the PDF's own italics: author before the title, quoted
article or chapter titles, italic book titles and containers, and year.

Theses that arrive as plain text (``.txt``: UBC Open Collections full text) take a text-only
path: no italics or geometry, so entries are cut at author starts and headings found inline.

Output is derived bibliographic metadata only (``entries.jsonl`` and
``extraction.jsonl``); the PDF and text bodies stay local. Parsing is heuristic. The
audit sample in ``build_dissertation_citation_graph.py`` measures precision.
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import math
from pathlib import Path
import re
import signal
import statistics
import unicodedata

import fitz

START = re.compile(r'^(?:[IVX\d]+\.?\s+)?(?:select(?:ed|ive)?\s+|annotated\s+)?(?:bibliography|works\s+cited|references|list\s+of\s+references|'
                   r'works\s+consulted|sources\s+(?:and|&)\s+bibliography|bibliography\s+(?:and|&)\s+sources|'
                   r'sources\s+consulted|list\s+of\s+sources|bibliographie|sources\s+et\s+bibliographie|'
                   r'(?:primary|archival|manuscript|unpublished\s+primary)\s+sources|sources\s+primaires|sources|'
                   r'références|références\s+bibliographiques|ouvrages\s+cités|liste\s+des\s+sources|'
                   r'sources\s+et\s+(?:études|ouvrages)|sources\s+(?:manuscrites|imprimées|archivistiques))\s*:?$', re.I)
WEAK = re.compile(r'^(?:sources|references|références|(?:primary|archival)\s+sources|sources\s+primaires)$', re.I)
STOP = re.compile(r'^(?:appendi(?:x|ces)|annexes?|index|curriculum\s+vitae|vita|glossary|biographical\s+sketch)\b', re.I)
ENTRY_START = re.compile(r'^(?:[—–_\-]{2,}|[A-ZÀ-ÝĀ-Ž][\w\'’ÀÁÂÄÇÈÉÊËÎÏÔÖÙÚÛÜà-ÿ\-]+(?: [A-Z][\w\'’\-]+)?,\s|'
                         r'[A-ZÀ-Ý][A-Za-zÀ-ÿ\'’\-]+(?: [A-Za-zÀ-ÿ\'’\-]+){0,4}\.\s)')
PRIMARY = re.compile(r'primar|archiv|manuscript|government|official|newspaper|periodical|interview|oral|fonds|'
                     r'unpublished|printed sources|published sources|contemporary|sources primaires|imprim|'
                     r'collections?|papers|records|documents|reports|correspondence|statutes|debates|legislation', re.I)
SECONDARY = re.compile(r'secondary|books|articles|monograph|chapters|theses|dissertations|scholarship|'
                       r'études|ouvrages|sources secondaires|historiograph|literature|studies', re.I)
YEAR = re.compile(r'(?<![\d/])(1[4-9]\d\d|20[0-2]\d)(?![\d/])')
# Bibliography headings in further languages (BASE theses, added 2026-10-20). Kept apart from the
# English and French patterns above, so those match exactly as before; every use below is an
# extra alternative ("or"), and none of these words occurs as an English or French heading.
START_ML = re.compile(
    r'^(?:[IVX\d]+\.?\s+)?(?:'
    # German
    r'literaturverzeichnis|quellen-?\s*und\s*literaturverzeichnis|literatur-?\s*und\s*quellenverzeichnis|'
    r'quellen\s+und\s+literatur|literatur\s+und\s+quellen|verzeichnis\s+der\s+quellen\s+und\s+literatur|'
    r'quellenverzeichnis|literatur|quellen|(?:un)?gedruckte\s+quellen|archivalien|(?:archivalische|archivische)\s+quellen|'
    # Spanish
    r'bibliograf[ií]a(?:\s+(?:y|e|i)\s+(?:fuentes|fontes|fonti|fonts|referencias|refer[eè]ncies))?'
    r'(?:\s+(?:citada|consultada|esmentada|utilizada|utilitzada|general|seleccionada|selecta))?|'
    r'fuentes\s+y\s+bibliograf[ií]a|referencias(?:\s+bibliogr[aá]ficas)?|'
    r'obras\s+citadas|fuentes(?:\s+(?:primarias|documentales|archiv[ií]sticas|impresas|consultadas))?|'
    # Portuguese
    r'refer[eê]ncias?(?:\s+bibliogr[aá]ficas?)?|fontes\s+e\s+(?:bibliografia|refer[eê]ncias)|bibliografia\s+e\s+fontes|'
    r'fontes(?:\s+(?:prim[aá]rias|documentais|consultadas|impressas))?|'
    # Swedish
    r'k[aä]ll-?\s*och\s*litteraturf[oö]rteckning|litteraturf[oö]rteckning|k[aä]llf[oö]rteckning|'
    r'k[aä]llor\s+och\s+litteratur|referenser|litteratur|(?:o?tryckta\s+)?k[aä]llor|'
    # Italian
    r'fonti\s+e\s+bibliografia|bibliografia\s+e\s+fonti|riferimenti\s+bibliografici|opere\s+citate|'
    r'fonti(?:\s+(?:archivistiche|edite|inedite|a\s+stampa))?|'
    # Dutch
    r'literatuurlijst|bibliografie|bronnen-?\s*en\s*literatuur(?:lijst)?|geraadpleegde\s+literatuur|literatuur|bronnen|'
    # Catalan and Greek
    r'fonts\s+i\s+bibliografia|refer[eè]ncies(?:\s+bibliogr[aà]fiques)?|'
    r'fonts(?:\s+(?:esmentades|consultades|documentals|prim[aà]ries|arxiv[ií]stiques|impreses))?|arxius\s+consultats|'
    r'βιβλιογραφ[ιί]α|βιβλιογραφικ[εέ]ς\s+αναφορ[εέ]ς|δευτερογεν[ηή]ς\s+βιβλιογραφ[ιί]α|'
    r'πηγ[εέ]ς(?:\s+και\s+βιβλιογραφ[ιί]α)?|πρωτογεν[εέ]ις\s+πηγ[εέ]ς|αναφορ[εέ]ς'
    r')\s*[:.]?$', re.I)
# The weak ones mark a primary-sources part ('Quellen', 'Fuentes') that a following strong
# heading ('Literatur') extends back to, as 'Sources' does for 'Bibliography'.
WEAK_ML = re.compile(
    r'^(?:quellen|(?:un)?gedruckte\s+quellen|archivalien|(?:archivalische|archivische)\s+quellen|'
    r'fuentes(?:\s+(?:primarias|documentales|archiv[ií]sticas|impresas|consultadas))?|'
    r'fontes(?:\s+(?:prim[aá]rias|documentais|consultadas|impressas))?|(?:o?tryckta\s+)?k[aä]llor|'
    r'fonti(?:\s+(?:archivistiche|edite|inedite|a\s+stampa))?|bronnen|'
    r'fonts(?:\s+(?:esmentades|consultades|documentals|prim[aà]ries|arxiv[ií]stiques|impreses))?|arxius\s+consultats|'
    r'πηγ[εέ]ς|πρωτογεν[εέ]ις\s+πηγ[εέ]ς|literatur|litteratur|literatuur)[:.]?$', re.I)
SQUEEZED_ML = {'literaturverzeichnis', 'quellenundliteraturverzeichnis', 'quellenundliteratur', 'bibliografía',
               'litteraturforteckning', 'kallochlitteraturforteckning', 'literatuurlijst', 'bibliografie',
               'riferimentibibliografici', 'referenciasbibliograficas', 'referenciasbibliograficas', 'βιβλιογραφια'}
PRIMARY_ML = re.compile(r'quellen|archivalien|fuentes|fontes|fonti|\bfonts\b|k[aä]llor|bronnen|πηγ|zeitung|prensa|jornais|'
                        r'giornali|tidningar|kranten|entrevistas|intervist|intervjuer|ungedruckt|gedruckt|tryckta|editadas|'
                        r'in[eé]dit[ao]s|documentos|documenti|dokumente|akten', re.I)
SECONDARY_ML = re.compile(r'literatur|litteratur|literatuur|sekund[aä]r|secund[aá]ri|secondari|sekund[aä]rlitteratur|'
                          r'darstellungen|estudios|estudos|studi\b|bibliograf[ií]a\s+secundaria', re.I)


# Further forms seen in US theses (English) and BASE theses (qualified French headings, Latvian,
# Turkish), 2026-10-20. Used only as a fallback when no heading above is found, so every thesis
# that parsed before parses exactly as before.
START_US = re.compile(r'^(?:[IVX\d]+\.?\s+)?(?:bibliography\s+of\s+(?:primary|secondary)\s+sources|bibliography\s+of\s+works\s+cited|'
                      r'bibliography\s+(?:and|&)\s+(?:works\s+cited|references)|dissertation\s+bibliography|'
                      r'(?:ancient|modern|general|primary|secondary)\s+bibliography|works\s+cited\s+(?:and|&)\s+consulted|'
                      r'(?:references|literature|sources)\s+cited|bibliography\s*:\s*[\w ,]{3,30}|reference\s+list|'
                      # French qualified forms, Latvian and Turkish (BASE theses); also fallback only
                      r'bibliographie\s+(?:g[ée]n[ée]rale|th[ée]matique|s[ée]lective|indicative|raisonn[ée]e)|'
                      r'orientations\s+bibliographiques|sources\s+et\s+r[ée]f[ée]rences|'
                      r'(?:izmantoto\s+)?avotu\s+un\s+literat[uū]ras\s+saraksts|izmantot[aā]s?\s+literat[uū]ras\s+saraksts|'
                      r'izmantotie\s+avoti\s+un\s+literat[uū]ra|literat[uū]ra|(?:nepublic[eē]tie|nepublic[eē]ti|public[eē]tie)?\s*avoti|'
                      r'kaynak[cç]a|kaynaklar)\s*[:.]?$', re.I)
WEAK_US = re.compile(r'^(?:[IVX\d]+\.?\s+)?(?:bibliography\s+of\s+primary\s+sources|primary\s+bibliography|'
                     r'(?:nepublic[eē]tie|nepublic[eē]ti|public[eē]tie)?\s*avoti)\s*[:.]?$', re.I)


def ml_heading(t):
    sq = ''.join(c for c in unicodedata.normalize('NFKD', t.lower()) if c.isalpha())
    return bool(START_ML.match(t)) or sq in SQUEEZED_ML


DASH_AUTHOR = re.compile(r'^\s*[—–_\-]{2,}\s*[.,]?\s*')
OPEN_Q, CLOSE_Q = '“"«‘', '”"»’'


def merge_ocr_lines(page, textpage):
    """Tesseract returns word groups; rebuild printed lines by shared baseline."""
    pieces = [l for b in page.get_text('dict', textpage=textpage)['blocks'] for l in b.get('lines', [])
              if ''.join(s['text'] for s in l['spans']).strip()]
    pieces.sort(key=lambda l: ((l['bbox'][1] + l['bbox'][3]) / 2, l['bbox'][0]))
    rows = []
    for l in pieces:
        mid = (l['bbox'][1] + l['bbox'][3]) / 2
        if rows and abs(mid - rows[-1]['mid']) < max(3.5, (l['bbox'][3] - l['bbox'][1]) * 0.45):
            rows[-1]['parts'].append(l)
        else:
            rows.append(dict(mid=mid, parts=[l]))
    lines = []
    for r in rows:
        parts = sorted(r['parts'], key=lambda l: l['bbox'][0])
        spans = []
        for i, l in enumerate(parts):
            if i:
                spans.append(dict(spans[-1], text=' '))
            spans.extend(l['spans'])
        lines.append(dict(bbox=(min(l['bbox'][0] for l in parts), min(l['bbox'][1] for l in parts),
                                max(l['bbox'][2] for l in parts), max(l['bbox'][3] for l in parts)), spans=spans))
    return [dict(lines=lines)]


def lines_of(page, textpage=None):
    h = page.rect.height
    out = []
    blocks = merge_ocr_lines(page, textpage) if textpage is not None else page.get_text('dict', sort=True)['blocks']
    for block in blocks:
        for line in block.get('lines', []):
            spans = [s for s in line['spans'] if s['text'].strip()]
            if not spans:
                continue
            text = ''.join(s['text'] for s in line['spans']).strip()
            x0, y0, x1, y1 = line['bbox']
            if (y0 < h * 0.06 or y1 > h * 0.95) and re.fullmatch(r'[\divxlcIVXLC.\- ]{1,8}|(?:page|p\.)\s*\d+', text, re.I):
                continue  # folio; repeated running headers are dropped per bibliography
            if re.fullmatch(r'[\divxlc]{1,6}', text):
                continue
            out.append(dict(x0=x0, x1=x1, y0=y0, y1=y1, text=text, page=page.number,
                            spans=[(s['text'], bool(s['flags'] & 2) or 'italic' in s['font'].lower() or 'oblique' in s['font'].lower(),
                                    bool(s['flags'] & 16) or 'bold' in s['font'].lower(), s['size']) for s in line['spans']]))
    return out


SQUEEZED = ('bibliography', 'bibliographie', 'bibliografia', 'bibliograffa', 'selectbibliography', 'selectedbibliography',
            'workscited', 'worksconsulted', 'sourcesconsulted', 'primarysources', 'archivalsources', 'secondarysources',
            'sourcesandbibliography', 'sourcesprimaires', 'sourcesetbibliographie', 'references', 'listofsources',
            'listofreferences', 'selectivebibliography')


def squeezed_heading(t):
    """OCR headings with stray spaces or punctuation ('Secondary So u r c e s:', 'B I B L I O G R A P H Y')."""
    sq = ''.join(c for c in unicodedata.normalize('NFKD', t.lower()) if c.isalpha())
    return sq in SQUEEZED


STRONG = re.compile(r'^(?:[IVX\d]+\.?\s+)?(?:select(?:ed|ive)?\s+|annotated\s+)?(?:bibliography|works\s+cited|works\s+consulted|list\s+of\s+references|'
                    r'references|bibliographie|bibliograf[ií]a|sources\s+(?:and|&)\s+bibliography|bibliography\s+(?:and|&)\s+sources|'
                    r'sources\s+et\s+bibliographie|sources\s+consulted|list\s+of\s+sources|références(?:\s+bibliographiques)?|'
                    r'ouvrages\s+cités|liste\s+des\s+sources)\s*:?$', re.I)
STRONG_SQUEEZED = {'bibliography', 'bibliographie', 'bibliografia', 'bibliograffa', 'selectbibliography',
                   'selectedbibliography', 'workscited', 'worksconsulted', 'sourcesandbibliography', 'sourcesetbibliographie',
                   'listofreferences', 'selectivebibliography'}


def find_span(doc, fallback=False):
    """The closing bibliography: the last run of pages carrying a strong heading
    ('Bibliography', 'Works Cited', 'Bibliographie'...) after 40% of the document, walked
    back over consecutive pages (running headers) and back to a 'Sources' heading up to 15
    pages earlier. Without a strong heading, the first weak one ('Primary Sources',
    'Sources') in the last 40%. Ends at a following appendix, index or vita."""
    n = len(doc)
    floor = int(n * 0.4)
    strong, weak = [], []
    for i in range(floor, n):
        for line in doc[i].get_text().splitlines():
            t = line.strip()
            if fallback and len(t) < 50 and START_US.match(t):
                (weak if WEAK_US.match(t) else strong).append(i)
                break
            if len(t) >= 50 or not (START.match(t) or squeezed_heading(t) or ml_heading(t)):
                continue
            sq = ''.join(c for c in unicodedata.normalize('NFKD', t.lower()) if c.isalpha())
            if STRONG.match(t) or sq in STRONG_SQUEEZED or (not START.match(t) and not squeezed_heading(t) and ml_heading(t)
                                                            and not WEAK_ML.match(t)):
                strong.append(i)
            elif not ((WEAK.match(t) or WEAK_ML.match(t)) and i < n * 0.6):
                weak.append(i)
            break
    if strong:
        start = strong[-1]
        while start - 1 in strong:
            start -= 1
        earlier = [w for w in weak if start - 15 <= w < start]
        start = min(earlier) if earlier else start
    elif weak:
        start = weak[0]
    else:
        return None, None
    end = n
    for i in range(start + 1, n):
        first = [l.strip() for l in doc[i].get_text().splitlines() if l.strip()][:4]
        if any(STOP.match(t) and len(t) < 60 for t in first):
            end = i
            break
    return start, end


OCR = False  # set by --ocr: scanned theses get Tesseract text for their closing pages


def find_span_ocr(doc, floor=0.55, extra=8):
    """OCR backwards from the last page until a bibliography heading; returns (start, end, textpages)."""
    n, pages, start, end, strong_seen = len(doc), {}, None, len(doc), False
    for i in range(n - 1, int(n * floor) - 1, -1):
        page = doc[i]
        tp = page.get_textpage_ocr(dpi=200, language='eng', full=True)
        pages[i] = (page, tp)
        heads = [l['text'].strip() for l in lines_of(page, tp)[:6]]
        if any(STOP.match(t) and len(t) < 60 for t in heads) and start is None:
            end = i
        hit = [t for t in heads if len(t) < 50 and (START.match(t) or squeezed_heading(t) or ml_heading(t))]
        if hit:
            start = i
            if not any(WEAK.match(t) or WEAK_ML.match(t) or re.search(r'primary|secondary|archiv', t, re.I) for t in hit):
                break  # 'Bibliography' itself: stop
        elif start is not None and i < start - extra:
            break
    return start, end, pages


def is_heading(line, prev, body_size, margin):
    t = line['text']
    if len(re.findall(r'[A-Za-zÀ-ÿ]', t)) < 3:
        return False
    if len(t) > 80 or t.endswith(('.', ',', ';')) and not t.endswith(('etc.',)) or ENTRY_START.match(t) and ', ' in t[:40]:
        if not (len(t) < 50 and (START.match(t) or START_ML.match(t))):
            return False
    if re.search(r'\d{4}.*[.,]$', t) or t.count(',') > 2:
        return False
    bold = all(s[2] for s in line['spans'] if s[0].strip())
    larger = max(s[3] for s in line['spans']) > body_size + 0.8
    centred = line['x0'] > margin + 60
    caps = t.isupper() and len(t) > 3
    keyword = bool(PRIMARY.search(t) or SECONDARY.search(t) or START.match(t) or START_ML.match(t))
    gap_before = prev is None or prev['page'] != line['page'] or line['y0'] - prev['y1'] > 6
    return gap_before and (bold or larger or (centred and keyword) or caps or (keyword and len(t) < 45 and not t.endswith('.')))


def split_entries(lines):
    if not lines:
        return []
    body_size = statistics.median(s[3] for l in lines for s in l['spans'])
    xs = Counter(round(l['x0']) for l in lines)
    common = [x for x, c in xs.items() if c >= max(3, len(lines) * 0.05)]
    margin = min(common) if common else xs.most_common(1)[0][0]
    indented = [l for l in lines if 6 < l['x0'] - margin < 60]
    hanging = 0.12 < len(indented) / len(lines) < 0.8
    gaps = [b['y0'] - a['y1'] for a, b in zip(lines, lines[1:]) if a['page'] == b['page'] and 0 <= b['y0'] - a['y1'] < 40]
    base_gap = sorted(gaps)[len(gaps) // 4] if gaps else 2  # ordinary line spacing (blank-line gaps can be half of all gaps)
    right = sorted(l['x1'] for l in lines)[int(len(lines) * 0.9)]
    entries, path, cur, prev = [], [], None, None
    for line in lines:
        if is_heading(line, prev, body_size, margin):
            level = 0 if (START.match(line['text']) or START_ML.match(line['text']) and not WEAK_ML.match(line['text'])) and not path else (1 if (line['text'].isupper() or max(s[3] for s in line['spans']) > body_size + 0.8) else 2)
            path = [p for p in path if p[0] < level] + [(level, line['text'].strip(': '))]
            cur, prev = None, line
            continue
        at_margin = abs(line['x0'] - margin) < 4
        gap = line['y0'] - prev['y1'] if prev and prev['page'] == line['page'] else None
        big_gap = gap is not None and gap > base_gap + max(4, base_gap * 0.8)
        starts = ENTRY_START.match(line['text']) is not None
        if cur is None:
            new = True
        elif hanging:
            new = at_margin and (big_gap or gap is None and starts or gap is not None)
        else:
            ended = cur['text'].rstrip().endswith(('.', ').', '.)'))
            short = prev is not None and prev['x1'] < right - 40
            new = big_gap or (starts and ended and (gap is None or short or at_margin))
        if new:
            cur = dict(page=line['page'], section=[p[1] for p in path], spans=[])
            entries.append(cur)
        elif cur['spans'] and not cur['spans'][-1][0].endswith(('-', '/')):
            cur['spans'].append((' ', False))
        if cur['spans'] and cur['spans'][-1][0].endswith('-') and line['text'][:1].islower():
            last = cur['spans'][-1]
            cur['spans'][-1] = (last[0][:-1], last[1])
        cur['spans'].extend((s[0], s[1]) for s in line['spans'])
        cur['text'] = ''.join(s[0] for s in cur['spans'])
        prev = line
    return entries


def italic_runs(spans):
    runs, pos = [], 0
    for text, ital in spans:
        if ital and text.strip():
            if runs and runs[-1][1] >= pos - 1 and runs[-1][2]:
                runs[-1] = (runs[-1][0], pos + len(text), True)
            else:
                runs.append((pos, pos + len(text), True))
        elif runs and not text.strip():
            runs[-1] = (runs[-1][0], runs[-1][1] + len(text) if runs[-1][1] == pos else runs[-1][1], True)
        pos += len(text)
    return [(a, b) for a, b, _ in runs if re.search(r'\w', ''.join(t for t, _ in spans)[a:b])]


GIVEN = r"[A-ZÀ-Ý][\w'’\-]*\.?(?:(?:\s+|(?<=\.))[A-ZÀ-Ý][\w'’\-]*\.?){0,5}"  # tokens split by space or after a period: no backtracking blow-up
NAME = re.compile(r'[^,.“"«]{2,60},\s+' + GIVEN + r'(?:,?\s(?:Jr|Sr)\.?)?(?:,\s*eds?)?')
INITIALS_AHEAD = re.compile(r'[A-ZÀ-Ý]\.(?:\s?[A-ZÀ-Ý]\.)*(?:,\s*eds?\.)?\s')  # 'Smith, J. A. B. Title': the shortest name stops at 'J.'


# German style 'Name, Vorname: Titel, Ort Jahr' (also 'Name, V./Name2, V.: Titel'); used only when
# neither the period-terminated name nor the fallback matched, so existing parses are unchanged.
COLON_NAME = re.compile(r"^([A-ZÀ-ÝĀ-Ž][\w'’\-]+(?: [a-zà-ÿ]+)?(?: [A-ZÀ-Ý][\w'’\-]+)?,\s+" + GIVEN +
                        r"(?:\s*(?:/|;|u\.|und)\s*[A-ZÀ-ÝĀ-Ž][\w'’\-]+,\s+" + GIVEN + r")*(?:\s*\((?:Hg|Hrsg|Ed|Eds)\.?\))?)\s*:\s+")
COLON_IMPRINT = re.compile(r'^\s*(.+?),\s*(?:[A-ZÀ-ÝĀ-Ž][\w\-/ ]{1,40}?\s+)?(?:1[4-9]|20)\d\d\b')


def name_end(raw):
    """(end of name, start of title) for the shortest 'Surname, Given' before a '. ', so a title that starts
    with capitals is not swallowed ('McArthur, Lewis A. Oregon Geographic Names.'); initials run on."""
    for d in re.finditer(r'\.\s', raw[:200]):
        if NAME.fullmatch(raw, 0, d.start()):
            end, start = d.start(), d.end()
            more = INITIALS_AHEAD.match(raw, start)
            if more and not re.search(r'\beds?$', raw[:end]):
                end, start = more.end() - 2, more.end()
            # an initial or honorific before one given name: 'Thomson, E. Janice.', 'Knight, Rev. William.'
            given = re.match(r"([A-ZÀ-Ý][a-zà-ÿ'’\-]+(?:\s[A-ZÀ-Ý](?=[\s.]))*)(,\s*eds?)?\.\s", raw[start:])
            if given and re.search(r'(?:\b[A-ZÀ-Ý]|\b(?:Rev|Mrs|Mr|Dr|Sir|Hon|Mme|Mgr|Fr|Prof))$', raw[:end]):
                end, start = start + given.end() - 2, start + given.end()
            return end, start
    return None
CLOSERS = {'“': '”', '"': '"', '«': '»', '‘': '’'}


def close_quote(raw, qpos):
    want = CLOSERS[raw[qpos]]
    for i in range(qpos + 1, len(raw)):
        if raw[i] == want and (want != '’' or i + 1 == len(raw) or not raw[i + 1].isalpha()):
            return i
        if want == '"' and raw[i] == '”' or want == '”' and raw[i] == '"':  # mixed straight and curly quotes
            return i
    return None


def pub_years(text):
    """Publication-year candidates: drop date ranges and access dates, prefer the last."""
    text = re.split(r'\b(?:accessed|consulted|consulté|retrieved)\b', text, flags=re.I)[0]
    found = [m.group(1) for m in YEAR.finditer(text)
             if not re.match(r'\s*[-–—]\s*\d', text[m.end():]) and not re.search(r'\d\s*[-–—]\s*$', text[:m.start()])]
    return found[-1:] if found else []


def clean(t):
    return re.sub(r'\s+', ' ', t).strip(' .,;:')


INITIAL_PAIRS = re.compile(r'\s*(?:&|\band\b|\bet\b)?\s*([^,&;]+?),\s*([A-ZÀ-Ý][a-zà-ÿ]{0,2}\.(?:\s?-?\s?[A-ZÀ-Ý][a-zà-ÿ]{0,2}\.)*|[A-ZÀ-Ý](?=\s*$))\s*(?:,|&|;|$|(?=and\b|et\b))')
AUTHOR_DATE = re.compile(r'^(.{2,200}?)[\s.,]*\(?((?:1[4-9]|20)\d\d)[a-z]?\)?[.,:]\s+')
TRAILING_YEAR = re.compile(r'[\s.,]*\(?(?:1[4-9]|20)\d\d[a-z]?\)?\s*$')


def split_authors(author):
    author = re.split(r'\.\s+(?:by|trans|translated|edited|ed|introduction|with)\b', author, flags=re.I)[0]
    author = re.sub(r',?\s*\bet\s+al\b\.?', '', author)
    a = re.sub(r',?\s*\b(?:eds?|editors?|comps?|compilers?|trans|translators?|dir|dirs|sous la dir(?:ection)? de)\b\.?', '', author, flags=re.I)
    a = re.sub(r'\(\s*\)', '', a).strip(' .,;')
    if not a:
        return []
    if ',' not in a:  # corporate or single-name author: keep whole
        return [a]
    # "SURNAME, I., SURNAME, I. & SURNAME, I." lists (author-date styles)
    pairs = INITIAL_PAIRS.findall(a)
    if len(pairs) >= 2:
        return [f'{s.strip()}, {g.strip()}' for s, g in pairs]
    parts = re.split(r'\s*(?:;|\band\b|\bet\b|&)\s*', a)
    first = parts[0]
    # "Surname, Given, Given2 Surname2" style: split after the first given name.
    m = re.match(r'^([^,]+,\s*[^,]+?),\s+(.+)$', first)
    if m and not re.search(r'\b(?:Jr|Sr|II|III)\b', m.group(2)):
        parts = [m.group(1)] + re.split(r',\s*', m.group(2)) + parts[1:]
    return [p.strip(' .,') for p in parts if p.strip(' .,')]


def surname(name, first):
    name = re.sub(r'\b(?:Jr|Sr|II|III)\.?$', '', name).strip(' ,')
    if ',' in name:  # inverted name
        return name.split(',')[0].strip()
    m = re.fullmatch(r"([A-ZÀ-Ý'’\-]{2,}(?:\s[A-ZÀ-Ý'’\-]{2,})*)\s+(?:[A-ZÀ-Ý]\.?\s?-?)+", name)
    if m:  # "BOURGUIGNON E." (surname, initials, no comma)
        return m.group(1)
    if first:  # bibliographies invert the first name; no comma means a corporate or single name
        return name
    toks = name.split()
    return toks[-1] if toks else ''


def parse(entry, prev_author):
    text = re.sub(r'\s+', ' ', entry['text']).strip()
    spans, shift = entry['spans'], 0
    dash = DASH_AUTHOR.match(text)
    if dash:
        shift = dash.end()
    runs = [(a, b) for a, b in italic_runs(spans) if b > shift]
    raw = ''.join(t for t, _ in spans)

    def seg(a, b):
        return clean(raw[a:b])
    qpos = next((i for i, c in enumerate(raw) if c in OPEN_Q and i >= shift and (c != '‘' or i == 0 or raw[i - 1] == ' ')), None)
    ipos = runs[0][0] if runs else None
    result = dict(raw=text, page=entry['page'] + 1 if entry['page'] is not None else None, section=entry['section'])
    colon = None  # set only by the German 'Name, Vorname:' path below
    cut = min(p for p in (qpos, ipos) if p is not None) if (qpos is not None or ipos is not None) else None
    if dash:
        author = prev_author
        if cut is None:
            cut = shift
    elif cut is not None and cut < 220:
        author = clean(TRAILING_YEAR.sub('', clean(raw[:cut])))
    elif (m := AUTHOR_DATE.match(raw)) and len(m.group(1)) < 120 and not re.search(r'\.\s+[A-ZÀ-Ý][a-zà-ÿ]{2,}', m.group(1)) \
            and (',' in m.group(1) or m.group(1).split()[:1] and m.group(1).split()[0].isupper()):
        author, cut = clean(m.group(1)), m.end()
    else:
        m = name_end(raw)
        if m is None and (fallback := re.match(r'^(.{2,200}?(?:[a-zà-ÿ\)]{2}|[A-Z]{2,}))\.\s', raw)):
            m = fallback.end(1), fallback.end()
        if m is None and (colon := COLON_NAME.match(raw)):
            m = colon.end(1), colon.end()
        author = clean(raw[:m[0]]) if m else None
        cut = m[1] if m else None
        # co-authors after an inverted first name: "Long, T.D. and C. Wright, eds."
        more = m and re.match(r"(?:and|et|&)\s+(?:[A-ZÀ-Ý][\w'’\-]*\.?\s?){1,5}(?:,\s*eds?\.?)?\.?\s", raw[cut:])
        if more:
            author, cut = clean(raw[:cut + more.end()]), cut + more.end()
    title = container = None
    title_end = cut or 0
    if qpos is not None and (ipos is None or qpos < ipos):
        m_end = close_quote(raw, qpos)
        if m_end:
            title, title_end = clean(raw[qpos + 1:m_end]), m_end
            after = [r for r in runs if r[0] > m_end]
            if after:
                container = seg(*after[0])
                title_end = after[0][1]
            else:  # no italics: journal runs from the closing quote to the volume or year
                m = re.match(r'^[\s.,”"’»]*(?:[Ii]n\s+)?([^0-9(]{3,150}?)[\s,]*(?:\d|\(|vol\.|no\.)', raw[m_end + 1:])
                if m:
                    container = clean(m.group(1))
                    title_end = m_end + 1 + m.end(1)
    elif ipos is not None:
        title, title_end = seg(*runs[0]), runs[0][1]
    elif cut is not None:
        if (y := re.match(r'\s*\(?(?:1[4-9]|20)\d\d[a-z]?\)?[.,]\s+', raw[cut:])):  # author-date: the year before the title
            cut += y.end()
        rest = raw[cut:]
        m = re.match(r'^\s*(.+?)(?<!\b[A-Z])(?<!\bSt)(?<!\bvol)(?<!\bNo)(?<!\bRev)(?<!\bMr)(?<!\bMrs)(?<!\bDr)\.\s+(?=[A-Z0-9(\[])', rest)
        title = clean(m.group(1)) if m else clean(rest[:200])
        title_end = cut + (m.end(1) if m else min(len(rest), 200))
        if colon and (imprint := COLON_IMPRINT.match(rest)):  # 'Titel, Ort Jahr': the imprint is not title
            title, title_end = clean(imprint.group(1)), cut + imprint.end(1)
    years = pub_years(raw[title_end:]) or pub_years(raw[cut or 0:]) or YEAR.findall(raw)
    low = text.lower()
    section = ' > '.join(entry['section']).lower()
    if re.search(r'https?://|www\.', low) and not runs:
        kind = 'web'
    elif re.search(r'ph\.?\s?d\.?|m\.?\s?a\.?\s+thesis|doctoral|dissertation|master.s thesis|thèse de doctorat|thèse \(ph|mémoire de maîtrise|mémoire \(m\.?a|\bthesis\b', low):
        kind = 'thesis'
    elif title and container and qpos is not None and re.search(r'\bin\b|\bdans\b|eds?\.|edited by|sous la dir', raw[qpos:qpos + 400], re.I) \
            and not re.search(r'\b(?:vol|no)\.|\d+\s*[,(:]\s*(?:no\.?\s*)?\d+', raw[(runs[0][1] if runs else 0):][:40]):
        kind = 'chapter'
    elif title and container and qpos is not None:
        kind = 'article'
    elif title and qpos is not None and re.search(r'\d+\s*[,(:.]\s*(?:no\.?\s*)?\d+|\(\s*\d{4}\s*\)\s*:', raw[title_end:]):
        kind = 'article'
    elif title and (re.search(r'[A-Za-z]\s*:\s*[A-Z][^,]{2,80},\s*(?:c\.\s*)?(?:1[4-9]|20)\d\d', raw) or
                    re.search(r',\s*[A-ZÀ-Ý][^,]{2,40},\s*[A-ZÀ-Ý][^,]{2,60},\s*(?:c\.\s*)?(?:1[4-9]|20)\d\d', raw)):
        kind = 'book'
    elif re.search(r'\bfonds\b|\bpapers\b|\bcollection\b|\bRG\s?\d|\bMG\s?\d|archives|\bfile\b|\bbox\b|\bvol\. \d+, file', raw, re.I):
        kind = 'archival'
    elif runs and not qpos:
        kind = 'book_or_serial'
    elif title and len(title) >= 8 and author and years and not re.search(r'https?://|www\.', low):
        kind = 'unstyled'  # author, title and year without italics, quotes or a colon imprint (French, older typescripts)
    else:
        kind = 'other'
    side = 'primary' if PRIMARY.search(section) and not SECONDARY.search(section) else \
           'secondary' if SECONDARY.search(section) else \
           'primary' if PRIMARY_ML.search(section) and not SECONDARY_ML.search(section) else \
           'secondary' if SECONDARY_ML.search(section) else 'unspecified'
    authors = split_authors(author) if author else []
    result.update(author=author, authors=authors,
                  surnames=[surname(a, i == 0) for i, a in enumerate(authors)],
                  title=title, container=container, year=int(years[0]) if years else None,
                  kind=kind, section_side=side, author_from_dash=bool(dash))
    return result, author


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout('extraction exceeded time limit')


# --- Text-only theses (UBC Open Collections full text): no italics, no line geometry ---
#
# Three layouts reach us: born-digital text whose line ends are '\xa0 ' (blank lines between
# entries), text with '\t\r' page breaks where hanging-indent continuation lines survive as
# runs of spaces, and flat OCR text (retrospective scans) with no line breaks at all, often
# letter-spaced ('M i s s i o n a r y S o c i e t y'). Entries are cut at sentence ends
# followed by an author start ('Surname, G', a dash, a government author), section headings
# are found inline, and printed folios are stripped by following the page-number sequence.

VOCAB = {}  # word -> cost, from the cited works' titles, authors and containers (letter-spacing repair)
TEXT_STRONG = re.compile(r'(?:(?:SELECT(?:ED)?|Select(?:ed)?)\s+)?(?:BIBI?LIOGRAPHY|Bibliography|BIBLIOGRAPHIE|Bibliographie|'
                         r'WORKS\s+CITED|Works\s+Cited|WORKS\s+CONSULTED|Works\s+Consulted|REFERENCES|References|'
                         r'SOURCES\s+AND\s+BIBLIOGRAPHY|Sources\s+and\s+Bibliography|LIST\s+OF\s+SOURCES|List\s+of\s+Sources|'
                         r'SOURCES\s+CONSULTED|Sources\s+Consulted)(?![^\W\d_])')
TEXT_WEAK = re.compile(r'(?:(?:UN)?PUBLISHED\s+|PRINTED\s+|(?:Un)?[Pp]ublished\s+|Printed\s+)?(?:PRIMARY|Primary|ARCHIVAL|Archival|MANUSCRIPT|Manuscript)\s+(?:SOURCES|[Ss]ources)(?![^\W\d_])')
TEXT_STOP = re.compile(r'(?:APPENDI(?:X|CES)|Appendi(?:x|ces)|ANNEXES?|Annexes?|INDEX|Index|CURRICULUM\s+VITAE|Curriculum\s+Vitae|VITA)(?!\w)'
                       r'(?:\s*(?:[A-Z]|[IVX]+|\d{1,2})(?!\w))?\s*[:.\-–—]?')
SECTION_WORDS = (r'Sources|Documents|Materials|Books|Articles|Monographs|Newspapers|Periodicals|Theses|Dissertations|Interviews|'
                 r'Manuscripts|Publications|Websites|Collections|Records|Archives|Reports|Chapters')
HEAD_CAPS = re.compile(r'(?<![\w,])(?:(?:[IVX]{1,4}|[A-H]|\d{1,2})[.)]?[ \t]+)?(?:[A-Z][A-Z\'’\-]+[ \t]+(?:(?:AND|OF|&)[ \t]+)?){0,4}'
                       r'(?:' + SECTION_WORDS.upper() + r')(?:[ \t]+(?:AND|&)[ \t]+[A-Z]{3,})?(?:[ \t]*\([A-Za-z ,\-]{1,40}\))?[ \t]*:?(?![\w])')
HEAD_TITLE = re.compile(r'(?<![\w,])(?:(?:[IVX]{1,4}|[A-H]|\d{1,2})[.)][ \t]+)?(?:[A-Z][a-z\-]+[ \t]+(?:(?:and|of|&)[ \t]+)?){0,3}'
                        r'(?:' + SECTION_WORDS + r')(?:[ \t]+(?:and|&)[ \t]+[A-Z][a-z]+)?(?:[ \t]*\([A-Za-z ,\-]{1,40}\))?([ \t]*:)?(?![\w])')
HEAD_WORDS = set('''primary secondary tertiary archival archive archives manuscript manuscripts unpublished published printed print
    government governmental official other contemporary selected select online internet electronic web digital oral newspaper
    newspapers periodical periodicals journal journals magazine magazines press english french chinese japanese korean russian
    spanish german italian portuguese dutch latin language languages and & of books book articles article chapters theses
    dissertations library libraries collections collection interviews interview records documents document materials material
    sources source reports report publications films film audiovisual maps websites community non-profit nonprofit legal
    statutes parliamentary court miscellaneous general background private personal papers correspondence letters diaries
    memoirs monographs edited reference proquest'''.split())
STRICT_SECTION = re.compile(r'\b(?:Sources|Documents|Materials|Books|Articles|Monographs|Newspapers|Periodicals|Theses|'
                            r'Dissertations|Interviews|Manuscripts|Literature|Publications|Websites)\b', re.I)
AUTHOR_AHEAD = re.compile(r'(?:[—–_\-]{2,}|(?:[A-ZÀ-Ý][\w\'’\-]+|[A-ZÀ-Ý]{2,})(?:\s(?:[A-ZÀ-Ý][\w\'’\-]+|de|du|des|van|von|der|da|di|la|le|St\.)){0,2}'
                          r'\s?,\s*(?:[A-ZÀ-Ý]|de\b|d’|d\')|(?:Canada|Great Britain|United States|British Columbia|Ontario|Qu[eé]bec|Manitoba|'
                          r'Saskatchewan|Alberta|Nova Scotia|New Brunswick|Newfoundland|France|Province of [A-Z]\w+)\.\s+[A-Z])')
BOUNDARY = re.compile(r'(?<=[.)\]”"’])(\s+)(?=' + AUTHOR_AHEAD.pattern + ')')
NOT_AUTHOR = {'ottawa', 'toronto', 'london', 'paris', 'montreal', 'montréal', 'quebec', 'québec', 'vancouver', 'victoria',
              'winnipeg', 'edmonton', 'halifax', 'boston', 'cambridge', 'oxford', 'edinburgh', 'dublin', 'chicago', 'washington',
              'berkeley', 'kingston', 'regina', 'saskatoon', 'calgary', 'fredericton', 'sydney', 'melbourne', 'beijing', 'tokyo',
              'delhi', 'new', 'vol', 'vols', 'no', 'nos', 'box', 'file', 'files', 'reel', 'series', 'part', 'section', 'chapter',
              'ibid', 'see', 'also', 'microfilm', 'folder', 'item', 'page', 'pages', 'january', 'february', 'march', 'april', 'may',
              'june', 'july', 'august', 'september', 'october', 'november', 'december'}
NOT_AUTHOR |= {'the', 'a', 'an', 'in', 'journal', 'proceedings', 'annals', 'bulletin', 'review', 'transactions', 'reprint',
               'reprinted', 'trans', 'translated', 'edited', 'originally', 'first', 'published'}
FOLIO = re.compile(r'(?<!\S)\d{1,4}(?!\S)')


def not_imprint(chunk, i):
    """An author start, not a place of publication ('Durham, NC: Duke'), a serial ('The China Quarterly, No. 45')
    or a running sentence."""
    head = chunk[i:i + 120]
    name = head.split(',')[0].split('.')[0].strip()
    if name.lower() in NOT_AUTHOR or name.split()[0].lower() in NOT_AUTHOR:
        return False
    if re.match(r'[^.,:]{2,40},\s*(?:[A-Z][A-Za-z.]{0,5}|[A-Z][a-z]+(?: [A-Z][a-z]+)?)\s*:\s', head):  # Place, ST: Publisher
        return False
    return not re.match(r'[^.,]{2,60},\s*(?:No|Nos|Vol|Vols|pp?|Issue|Part|Tome|t)\b\.?\s*[\dIVXivx]', head)


def load_vocab(out):
    """Word costs (wordninja style, by frequency rank) from the corpus's cited titles, authors and containers."""
    import csv
    counts = Counter()
    path = out / 'works.csv'
    if path.exists():
        csv.field_size_limit(1 << 24)
        for row in csv.DictReader(path.open()):
            w = int(row['cited_by_all'] or 1)
            for field in ('title', 'authors', 'container'):
                for tok in re.findall(r"[^\W\d_]+", row[field] or ''):
                    counts[tok.lower()] += w
    ranked = [w for w, c in counts.most_common() if c >= 2 and (len(w) > 1 or w in 'ai')]
    logn = math.log(len(ranked) or 1)
    return {w: math.log((i + 1) * logn) for i, w in enumerate(ranked)}


def segment(run, extra):
    """Split a run of letters into words: known words by rank; an unknown word costs a flat penalty
    so a name stays whole rather than being chopped into pieces."""
    low, n = run.lower(), len(run)
    best = [(0.0, 0)] + [(math.inf, 0)] * n
    for i in range(1, n + 1):
        for j in range(max(0, i - 24), i):
            w = low[j:i]
            c = extra.get(w, VOCAB.get(w))
            c = (18 + 0.3 * len(w)) if c is None else c
            if best[j][0] + c < best[i][0]:
                best[i] = (best[j][0] + c, j)
    words, i = [], n
    while i:
        j = best[i][1]
        words.append(run[j:i])
        i = j
    return ' '.join(reversed(words))


SPACED = re.compile(r'(?<![^\W\d_])(?:[^\W\d_]{1,3} )?(?:[^\W\d_] ){2,}[^\W\d_](?: [^\W\d_]{1,3}(?![^\W\d_]))?(?![^\W\d_])')


SPACED_LOOSE = re.compile(r'(?<![^\W\d_])(?:[^\W\d_]{1,5} )?(?:[^\W\d_]{1,2} ){2,}[^\W\d_]{1,2}(?: [^\W\d_]{1,5})?(?![^\W\d_])')
CAMEL = re.compile(r'\b[^\W\d_]*[a-z][A-Z][^\W\d_]*\b')


def known_split(token, extra):
    """'TheShieldofAchilles' -> 'The Shield of Achilles' when every piece is a known word; else unchanged."""
    out = []
    for piece in re.split(r'(?<=[a-z])(?=[A-Z])', token):
        low, n = piece.lower(), len(piece)
        best = [(0.0, 0)] + [(math.inf, 0)] * n
        for i in range(1, n + 1):
            for j in range(max(0, i - 24), i):
                c = extra.get(low[j:i], VOCAB.get(low[j:i]))
                if c is not None and best[j][0] + c < best[i][0]:
                    best[i] = (best[j][0] + c, j)
        if best[n][0] == math.inf:
            return token
        words, i = [], n
        while i:
            words.append(piece[best[i][1]:i])
            i = best[i][1]
        out.extend(reversed(words))
    return ' '.join(out)


def repair_text(text):
    """Undo OCR letter-spacing and rejoin words broken at line-end hyphens. Texts that are measurably
    letter-spaced (retrospective scans) also get the looser OCR repairs; born-digital text is left alone."""
    own = Counter(t.lower() for t in re.findall(r'[^\W\d_]{4,}', text))
    extra = {w: 9.0 for w, c in own.items() if c >= 2 and w not in VOCAB}  # the thesis's own names and terms
    noisy = len(SPACED.findall(text)) > len(text) / 3000
    text = re.sub(r'(?<=[.)])\s+[.,]\s+(?=[A-Z"“])', ' ——. ', text)  # a repeat-author rule the OCR read as '.' or ','
    if noisy:
        text = re.sub(r'(?<=\S) +([,.;:)])', r'\1', text)  # 'Russell , C. Allyn .'
        text = re.sub(r'\b([Ee]) d(s?)\.', r'\1d\2.', text)  # 'e d .'
        text = re.sub(r'(?<!\d)([12]) ?(\d) (\d) ?(\d)(?!\d)', r'\1\2\3\4', text)  # '1 8 7 9'
        text = SPACED_LOOSE.sub(lambda m: segment(m.group().replace(' ', ''), extra)
                                if sum(len(t) == 1 for t in m.group().split()) >= 2 else m.group(), text)
        text = CAMEL.sub(lambda m: known_split(m.group(), extra) if len(m.group()) >= 8 else m.group(), text)
    else:
        text = SPACED.sub(lambda m: segment(m.group().replace(' ', ''), extra), text)
    text = re.sub(r'\b([A-Z]) \.(?= )', r'\1.', text)  # 'Richard L . Nigerian'

    def dehyphen(m):
        joined = (m.group(1) + m.group(2)).lower()
        return m.group(1) + m.group(2) if joined in VOCAB or joined in extra else m.group(1) + '-' + m.group(2)
    return re.sub(r'([^\W\d_]{2,})\s?-\s?([a-zà-ÿ]{2,})', dehyphen, text)


GLUE = re.compile(r'[a-z]{3}[A-Z][a-z]|[.,;][A-Z][a-z]')


def deglue(text):
    """Text whose converter dropped line breaks without a space ('1977.Religious', 'ElizabethanAge', '272SELECT')."""
    text = re.sub(r'(\d)([A-Z][A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([.,;:)\]"”’])([A-Z“"(])', r'\1 \2', text)
    text = re.sub(r'(?<![A-Za-z])((?!Mac)[A-Za-z][a-z]{2,})([A-Z][a-z])', r'\1 \2', text)
    return re.sub(r'(BIBLIOGRAPHY|SOURCES|REFERENCES|MANUSCRIPTS|DOCUMENTS|PUBLICATIONS|COLLECTIONS)(?=[A-Z])', r'\1 ', text)


def text_layout(raw):
    if raw.count('\x02') > 0.2 * max(raw.count(' '), 1):  # some converters separate words with STX
        raw = raw.replace('\x02', ' ')
    raw = re.sub(r'(?<![A-Za-z])(?:[A-Z] ){4,}[A-Z](?![A-Za-z])', lambda m: m.group().replace(' ', ''), raw)  # 'B I B L I O G R A P H Y'
    raw = re.sub(r'(?<![A-Za-z])B ?i ?b ?l ?i ?o ?g ?r ?a ?p ?h ?y(?![a-z])', 'Bibliography', raw)  # 'B i b l i o g r a p h y'
    raw = re.sub(r'(BIBLIOGRAPHY)(?=[A-Z])', r'\1 ', raw)  # 'BIBLIOGRAPHYBIBLIOGRAPHYI. MANUSCRIPT'
    if len(GLUE.findall(raw)) > len(raw) / 1000:
        raw = deglue(raw)
    if raw.count('\xa0') > 0.2 * max(raw.count(' '), 1):
        return 'lines', raw.replace('\xa0 ', '\n').replace('\xa0', ' ')
    if raw.count('\t\r') > 10:  # page breaks; a run of spaces is an indented continuation line
        return 'indent', re.sub(r' {3,}', '\x01', raw.replace('\t\r', '\n').replace('\xa0', ' '))
    return 'flat', raw.replace('\xa0', ' ')


def heading_context(text, m):
    """A heading stands at a line start, after a sentence end or a page number, and is not followed by a lowercase word."""
    before = text[max(0, m.start() - 12):m.start()]
    ok_before = not before.strip() or re.search(r'(?:[\n\f\x01]|(?<![^\W\d_])\d[\dA-Za-z]{0,7}|[.!?:”")\]\-])\s*$', before)
    after = text[m.end():m.end() + 30]
    return bool(ok_before) and (not re.match(r'\s*(?:[a-zà-ÿ]|\()', after) or bool(re.match(r'\s*o ?f\s+(?:l ?i ?t|w ?o ?r ?k|s ?o ?u ?r)', after)))


def citation_density(text, a, b):
    return sum(1 for _ in BOUNDARY.finditer(text, a, b))


def text_span(text):
    n = len(text)
    strong = [m for m in TEXT_STRONG.finditer(text, int(n * 0.4)) if heading_context(text, m)]
    weak = [m for m in TEXT_WEAK.finditer(text, int(n * 0.4)) if heading_context(text, m)]
    def stop(start):
        return next((m.start() for m in TEXT_STOP.finditer(text, start + 2000) if heading_context(text, m)
                     and not re.match(r'\s*,', text[m.end():]) and citation_density(text, m.end(), m.end() + 3000) < 10), n)
    if strong:
        runs = []  # (first, last) heading of each run; running headers sit on consecutive pages
        for m in strong:
            if runs and m.start() - runs[-1][1] < 6000:
                runs[-1][1] = m.start()
            else:
                runs.append([m.start(), m.start()])
        # the last run that is followed by entries (a stray heading near the end is not the bibliography)
        start = next((a for a, _ in reversed(runs) if citation_density(text, a, stop(a)) >= 15), runs[-1][0])
        earlier = [w.start() for w in weak if start - 30000 <= w.start() < start]
        start = min(earlier) if earlier else start
    elif weak and weak[0].start() > n * 0.6:
        start = weak[0].start()
    else:
        return None, None
    return start, stop(start)


def folios(span):
    """The printed page-number sequence: the longest chain k, k+1 (or k+2), ... spaced like pages."""
    nums = [(m.start(), m.end(), int(m.group())) for m in FOLIO.finditer(span)]
    best = []
    for s in range(min(len(nums), 40)):
        chain = [nums[s]]
        for p in nums[s + 1:]:
            gap = p[0] - chain[-1][0]
            if gap > 12000:
                break
            if gap > 600 and p[2] in (chain[-1][2] + 1, chain[-1][2] + 2):
                chain.append(p)
        if len(chain) > len(best) and chain[0][2] < 1200:  # page numbers, not a run of years
            best = chain
    return best if len(best) >= 3 or (best and len(span) < 6000 and len(best) >= 1 and best[0][2] > 20) else []


def text_entries(span):
    chain = folios(span)
    cuts = [(a, b) for a, b, _ in chain]
    pages = [(a, k) for a, _, k in chain]
    for a, b in reversed(cuts):
        span = span[:a] + ' ' * (b - a) + span[b:]  # keep offsets for the page lookup
    span = TEXT_STRONG.sub(lambda m: ' ' * len(m.group()), span)  # opening heading and running headers
    heads = []
    for rx in (HEAD_CAPS, HEAD_TITLE):
        for m in rx.finditer(span):
            t = m.group().strip(' :')
            words = re.sub(r'\([^)]*\)|^(?:[IVX]{1,4}|[A-H]|\d{1,2})[.)]?\s+', '', t).lower().split()
            if not heading_context(span, m) or len(t) > 70 or span[max(0, m.start() - 3):m.start()].rstrip().endswith(':') \
                    or not all(w in HEAD_WORDS for w in words):
                continue
            colon = m.group().rstrip().endswith(':')
            ahead = span[m.end():m.end() + 80].lstrip(' \n\x01:')
            if rx is HEAD_TITLE and not (colon or (STRICT_SECTION.search(t) and AUTHOR_AHEAD.match(ahead)) or HEAD_CAPS.match(ahead)):
                continue
            if rx is HEAD_CAPS and not (colon or AUTHOR_AHEAD.match(ahead) or re.match(r'[A-Z]', ahead)):
                continue
            heads.append((m.start(), m.end(), 1 if rx is HEAD_CAPS else 2, t))
    heads.sort(key=lambda h: (h[0], -h[1]))  # the longest heading at a position
    kept, last = [], -1
    for h in heads:
        if h[0] >= last:
            kept.append(h)
            last = h[1]
    entries, path, pos = [], [], 0

    def page_at(i):
        before = [k for a, k in pages if a <= i]
        return (before[-1] - 1) if before else (pages[0][1] - 2 if pages else None)

    def cut(chunk, offset):
        starts = [0] + [m.end(1) for m in BOUNDARY.finditer(chunk)
                        if '\x01' not in m.group(1) and AUTHOR_AHEAD.match(chunk, m.end(1))
                        and not_imprint(chunk, m.end(1))
                        and not re.search(r'(?:\b[A-Z]|\b(?:St|Mr|Mrs|Dr|Rev|vol|no|ed|eds|trans|comp))\.$', chunk[:m.start(1)])]
        kept_starts = []
        for a in starts:
            if kept_starts and len(chunk[kept_starts[-1]:a].strip()) < 25:  # too short for an entry: an author list
                continue
            kept_starts.append(a)
        for a, b in zip(kept_starts, kept_starts[1:] + [len(chunk)]):
            t = re.sub(r'\s+', ' ', chunk[a:b].replace('\x01', ' ')).strip()
            if t:
                entries.append(dict(page=page_at(offset + a), section=[p[1] for p in path], spans=[(t, False)], text=t))

    for a, b, level, title in kept + [(len(span), len(span), None, None)]:
        chunk = span[pos:a]
        if re.search(r'\n[ \t]*\n', chunk):  # 'lines' layout: blank lines separate entries
            off = 0
            for part in re.split(r'(\n[ \t]*\n)', chunk):
                if part.strip():
                    cut(part, pos + off)
                off += len(part)
        else:
            cut(chunk, pos)
        if level is not None:
            path = [p for p in path if p[0] < level] + [(level, title)]
        pos = b
    return entries, chain


def _process_text(path):
    raw = path.read_text()
    layout, text = text_layout(raw)
    start, end = text_span(text)
    if start is None:
        return dict(file=str(path), chars=len(raw), status='no_bibliography_heading', layout=layout), []
    bad = sum(c == '?' or c == '\ufffd' or (ord(c) < 32 and c not in '\n\t\r\x01') for c in text[start:end])
    if bad > 0.05 * (end - start):  # broken font encoding: the bibliography is not readable text
        return dict(file=str(path), chars=len(raw), status='unreadable_text', layout=layout, bib_chars=[start, end]), []
    span = repair_text(text[start:end])
    entries, chain = text_entries(span)
    parsed, prev_author = [], None
    for e in entries:
        if len(e['text']) < 12:
            continue
        r, prev_author = parse(e, prev_author)
        parsed.append(r)
    other = sum(r['kind'] == 'other' for r in parsed) / max(len(parsed), 1)
    status = 'parsed' if len(parsed) >= 10 else 'few_entries'
    if status == 'parsed' and other > 0.6 and ((end - start) / len(text) > 0.25 or len(parsed) > 2500):
        status = 'suspect_span'
    return dict(file=str(path), chars=len(raw), status=status, layout=layout, text_only=True,
                bib_chars=[start, end], bib_pages=[chain[0][2], chain[-1][2]] if chain else None, entries=len(parsed),
                kinds=dict(Counter(p['kind'] for p in parsed)), sides=dict(Counter(p['section_side'] for p in parsed))), parsed


def process(path, limit=None, parts=None):
    """``parts``: every declared part of a multi-part dissertation, in part order (the
    primary ``path`` first); they are read as one document."""
    limit = limit or (1500 if OCR else 300)
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(limit)
    try:
        if str(path).endswith('.txt'):
            return _process_text(Path(path))
        return _process(Path(path), parts=[Path(p) for p in parts] if parts and len(parts) > 1 else None)
    except Exception as exc:  # one malformed PDF must not stop the batch
        return dict(file=str(path), status='extraction_error', error=f'{type(exc).__name__}: {exc}'), []
    finally:
        signal.alarm(0)


def open_parts(parts):
    """One in-memory document from the declared parts of a multi-part dissertation (US
    repositories split some deposits into front matter, chapters and bibliography)."""
    doc = fitz.open()
    for p in parts:
        with fitz.open(p) as part:
            doc.insert_pdf(part)
    return doc


def _process(path, parts=None):
    fitz.TOOLS.mupdf_display_errors(False)
    try:
        doc = open_parts(parts) if parts else fitz.open(path)
    except Exception as exc:
        return dict(file=str(path), status='unreadable', error=str(exc)), []
    pages = len(doc)
    text_chars = sum(len(doc[i].get_text()) for i in range(0, pages, max(1, pages // 12)))
    ocr = {}
    if text_chars < 2000:
        if not OCR:
            return dict(file=str(path), pages=pages, status='no_text_layer'), []
        start, end, ocr = find_span_ocr(doc)
    else:
        start, end = find_span(doc)
        if start is None:  # further English heading forms, tried only when none of the usual ones is found
            start, end = find_span(doc, fallback=True)
    if start is None:
        return dict(file=str(path), pages=pages, status='no_bibliography_heading', ocr=bool(ocr), ocr_pages=len(ocr)), []
    lines = [l for i in range(start, end) for l in (lines_of(*ocr[i]) if ocr else lines_of(doc[i]))]
    # Drop the opening heading line itself and repeated running headers.
    repeat = Counter(re.sub(r'\d+', '#', l['text']) for l in lines)
    npages = end - start
    lines = [l for l in lines if not (npages > 3 and repeat[re.sub(r'\d+', '#', l['text'])] > max(2, npages * 0.4)
                                      and len(l['text']) < 80 and len(re.findall(r'[A-Za-z]', l['text'])) >= 4)]
    entries = split_entries(lines)
    parsed, prev_author = [], None
    for e in entries:
        if len(e.get('text', '')) < 12:
            continue
        r, prev_author = parse(e, prev_author)
        parsed.append(r)
    other = sum(r['kind'] == 'other' for r in parsed) / max(len(parsed), 1)
    status = 'parsed' if len(parsed) >= 10 else 'few_entries'
    if status == 'parsed' and other > 0.6 and ((end - start) / pages > 0.25 or len(parsed) > 2500):
        status = 'suspect_span'  # body text or unreadable OCR swallowed: kept out of the graph
    return dict(file=str(path), pages=pages, status=status, bib_pages=[start + 1, end], entries=len(parsed), ocr=bool(ocr),
                kinds=dict(Counter(p['kind'] for p in parsed)), sides=dict(Counter(p['section_side'] for p in parsed)),
                **({'parts': len(parts)} if parts else {})), parsed


def read_log(path):
    """Rows of a download log, tolerating a final line still being written."""
    rows = []
    for line in path.open():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def declared_parts(d, out):
    """All part paths of a dissertation whose files declare part numbers (``part`` 1..n),
    in order; None for single files and for undeclared extra bitstreams (which stay unread,
    as before)."""
    files = d.get('files', [])
    if len(files) < 2 or not all(f.get('part') for f in files):
        return None
    return [str(out / f['path']) for f in sorted(files, key=lambda f: f['part'])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--only', nargs='*', help='specific PDF paths (testing)')
    parser.add_argument('--only-file', type=Path, help='file listing PDF paths (one per line, relative to --out), as --only '
                                                       '(written by dissertation_ingest.py for incremental runs)')
    parser.add_argument('--rebuild', action='store_true', help='re-extract everything (needed after parser changes)')
    parser.add_argument('--retry-status', nargs='*', default=[], help='re-extract PDFs whose last status is one of these')
    parser.add_argument('--ocr', action='store_true', help='OCR scanned theses (needs Tesseract; TESSDATA_PREFIX)')
    args = parser.parse_args()
    fitz.TOOLS.mupdf_display_errors(False)
    global OCR
    OCR = args.ocr
    if args.only_file:
        args.only = (args.only or []) + [l.strip() for l in args.only_file.open() if l.strip()]
    done = {}  # file -> sha256 of the extracted copy (None for rows written before hashes were recorded)
    if not args.rebuild and (args.out / 'extraction.jsonl').exists():
        last = {}
        for line in (args.out / 'extraction.jsonl').open():
            x = json.loads(line)
            last[x['file']] = (x['status'], x.get('sha256'))
        done = {f: sha for f, (st, sha) in last.items() if st not in args.retry_status}
    latest = {}
    for log in sorted(args.out.glob('downloads*.jsonl')):
        for d in read_log(log):
            if 'institution' not in d or 'id' not in d:
                continue  # raw logs of sources not yet in the manifest (BASE); dissertation_ingest.py maps them
            if d['status'] == 'downloaded' or (d['institution'], d['id']) not in latest:
                latest[(d['institution'], d['id'])] = d
    downloads = list(latest.values())
    only = set(args.only or [])
    jobs = []
    for d in downloads:
        for f in d.get('files', []):
            if not f['primary'] or (only and f['path'] not in only and str(args.out / f['path']) not in only):
                continue
            # Done when extracted before, unless the file has since been replaced (sha256 differs).
            if f['path'] in done and (done[f['path']] is None or not f.get('sha256') or done[f['path']] == f['sha256']):
                continue
            jobs.append((d, args.out / f['path']))
    if any(str(path).endswith('.txt') for _, path in jobs):
        VOCAB.update(load_vocab(args.out))  # inherited by the forked workers
    mode = 'w' if args.rebuild or not done else 'a'
    print(f'{len(jobs)} PDFs to extract ({len(done)} already done)', flush=True)
    with ProcessPoolExecutor(args.workers) as pool, \
            (args.out / 'extraction.jsonl').open(mode) as log, (args.out / 'entries.jsonl').open(mode) as ent:
        futures = {pool.submit(process, str(path), None, declared_parts(d, args.out)): (d, path) for d, path in jobs}
        for future in as_completed(futures):
            (d, path), (info, parsed) = futures[future], future.result()
            info.update(institution=d['institution'], id=d['id'], file=str(path.relative_to(args.out)))
            sha = next((f.get('sha256') for f in d.get('files', []) if f['primary']), None)
            if sha:
                info['sha256'] = sha
            log.write(json.dumps(info, ensure_ascii=False) + '\n')
            for i, r in enumerate(parsed):
                ent.write(json.dumps(dict(dissertation=d['id'], institution=d['institution'], n=i, **r), ensure_ascii=False) + '\n')
            print(d['institution'], info['status'], info.get('entries'), info.get('kinds'), flush=True)


if __name__ == '__main__':
    main()
