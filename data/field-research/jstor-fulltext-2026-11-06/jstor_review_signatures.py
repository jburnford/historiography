"""Reviewer signatures from JSTOR book-review text: the reviewer's name and institution as printed (2026-11-06).

The metadata lists the names on a review (the books' authors and the reviewer, in no fixed order). A listed name is
the reviewer when it is printed as a signature: in the last part of the text, as a name span, followed (or, in
older American journals, preceded) by an institution, or at the very end; and it is not in the heading. Pages are
shared with neighbouring reviews, so the signature is found by the name, not by the end of the text.

Output (E:, not committed; names and institutions as printed, no review text):
  /mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz
  iid, creator (metadata form), reviewer (as printed), institution (as printed or null), place (a bare town after the name),
  where (after | before | bio | end-only), pos (0-1 position in the text), conf
Rows only for reviews where a signature was found; summary counts on stdout.

    python3 jstor_review_signatures.py [--ids FILE] [--out PATH]
"""
import argparse, gzip, json, os, re, sqlite3, time, unicodedata
from collections import Counter

SRC = '/mnt/e/jstor-fulltext-2026-11-06/reviews.jsonl.gz'
DB = 'file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro'
OUT = '/mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz'

INST = re.compile(r"\b(?:Univ\w*|Instituut|College|Coll[eè]ge|Institut\w*|School|Academ\w*|Akademie|Museum|Mus[ée]e|Library|Biblioth\w*|"
                  r"Archiv\w*|Society|Seminary|Hochschule|Centre|Center|Centro|Polytechnic|Faculty|Facult[ée]|CNRS|EHESS|"
                  r"Max[- ]Planck|Smithsonian|Department|Dept|Laborator\w*|Foundation|Fondation|Escuela|Instituto|Universidad|"
                  r"Universit[àaé]|Universidade|Universität|Universiteit|Uniwersytet|Sorbonne|Polytechni\w*|Ministry|Service|"
                  r"Survey|Office|Trust|Council|Commission|Hospital|Clinic|Board|Agency|Corporation|Company|Inc\b|Ltd\b|"
                  r"Historical|Gymnasium|Lyc[ée]e|Normale|Studies|Studi|Fellow|Emerit\w*|Retired|Independent Scholar)", re.I)
STOP = re.compile(r'\s(?:\d{2,4}\s|doi\b|Advance Access|BOOK REVIEWS|REVIEWS\b|Book Reviews|Reviews\b|Comptes rendus|'
                  r'Besprechungen|Recensioni|Rese[ñn]as|NOTES\b|By\s[A-Z]|Pp\.\s|[“"«]|E-?mail\b|edited\b|by\s|working\b|'
                  r'The\s(?!(?:Open|Johns|Ohio|Catholic|City|Graduate|Hebrew|Pennsylvania|American|George|Australian|Chinese|Hong)\b)[A-Z]|'
                  r'[A-Z][a-z]+\s(?:[A-Z]\.\s)?[A-Z][a-z]+,\s[A-Z][a-z]+\s[a-z])|\.\s+[A-Z][a-z]+\s[a-z]', re.S)
NAMETOK = r"(?:[A-ZÀ-Ý][\w'’\-]*\.?|[A-ZÀ-Ý]\.|de|du|van|von|der|da|di|la|le|St\.)"


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def fold1(s):
    """Fold accents and case one character for one, so offsets in the folded text are offsets in the text."""
    out = []
    for ch in s:
        d = unicodedata.normalize('NFKD', ch)
        c = d[0] if d and d[0].isascii() else ch
        c = c.lower()
        out.append(c if len(c) == 1 else ch)
    return ''.join(out)


PARTICLES = {'de', 'du', 'van', 'von', 'der', 'da', 'di', 'la', 'le', 'y', 'del', 'den', 'ten'}
TITLES = {'dr', 'prof', 'mrs', 'mr', 'ms', 'mme', 'mlle', 'sir', 'rev', 'fr', 'abbe', 'pere', 'mgr'}


def creators(cr):
    cr = re.sub(r',?\s*<suffix>([^<]*)</suffix>', r' \1', cr or '')
    cr = re.sub(r'<[^>]+>', '', cr)
    names = [c.strip() for c in cr.split(',') if c.strip() and not re.fullmatch(r'(?:Jr|Sr|II|III)\.?', c.strip())]
    # corporate creators ('President's Committee on Education Beyond the High') are not reviewers
    return [n for n in names if len(n.split()) <= 5 and not any(w.islower() and len(w) > 1 and w not in PARTICLES for w in n.split())]


def family(name):
    toks = [t for t in re.split(r'\s+', name.strip()) if t and not re.fullmatch(r'(?:Jr|Sr|II|III)\.?', t)]
    return toks[-1] if toks else ''


def find_sig(text, ftext, name, start_at):
    """Last printed occurrence of `name` (family name, case-insensitive) after start_at -> (span start, span end, printed)."""
    fam = fold(family(name))
    if len(fam) < 2:
        return None
    best = None
    for m in re.finditer(r'(?<![a-z])' + re.escape(fam) + r'(?![a-z])', ftext):
        if m.start() < start_at:
            continue
        # extend left only over this person's given names, initials, particles and titles ('J. A.', 'Peter-Michael', 'Dr')
        given = [fold(g).strip('.') for g in re.split(r'[\s\-]+', name)[:-1] if g.strip('.')]
        s = m.start()
        for _ in range(6):
            lm = re.search(r"([\w'’.\-]+)\s*$", text[max(0, s - 40):s])
            if not lm:
                break
            parts = [x for x in re.split(r'[.\-]', fold(lm.group(1))) if x]
            if parts and all(x in PARTICLES or x in TITLES or any(g == x or (len(x) == 1 and g[:1] == x) for g in given) for x in parts):
                s -= len(lm.group(0))
            else:
                break
        e = m.end()
        if re.match(r"\s*['’]s?\b|\s+(?!is\b|was\b|teaches\b|received\b|holds\b|works\b|has\b)[a-z]", text[e:e + 12]):
            continue   # a mention in a sentence ("Dr. Name's work"), not a signature
        jr = re.match(r',?\s*(?:Jr|Sr|II|III)\.?', text[e:e + 6])
        if jr:
            e += jr.end()
        printed = text[s:e].strip()
        # the name in a signature: the given name or initial printed with it (not a bare surname in a sentence)
        g0 = fold(name.split()[0])[:1] if name.split() else ''
        if g0 and not fold(printed).startswith(g0) and len(printed.split()) < 2 and len(name.split()) > 1:
            continue
        best = (s, e, printed)
    return best


_CAP = r"(?!(?:The|A|An|Le|La|Les|Die|Der|Das|Il|Lo|El|Los|Las|Some|This|These|Un|Une|Ein|Eine)\b)[A-ZÀ-Ý][\w'’.&\-]*"
_CONN = r"(?i:of|at|for|de|di|du|des|in|für|del|della|of the|de la|d'|d’|voor|van|zu|zur|per|do|da|e|y)"
INST_PHRASE = re.compile(
    rf"(?:(?:{_CAP}|of|the|and|&|for|de|di|du|des|la|für|on)\s+){{0,6}}?"           # 'Department of History, ' / 'Brigham Young '
    rf"(?i:{INST.pattern[2:]})[\w'’]*"                                                  # the institution word (any case)
    rf"(?:\s*{_CONN}\s*(?:the\s+)?{_CAP}(?:\s+{_CAP}){{0,2}}){{0,3}}"                  # 'of Texas at Austin'
    rf"(?:\s*,\s*{_CAP}(?:\s+{_CAP})?){{0,2}}")                                        # ', Kingston' / ', Washington, D.C'


def trim_inst(seg):
    """Keep the institution phrase; drop what runs on after it (the next review's heading, a bio sentence)."""
    if not seg:
        return None
    end = None
    for m in INST_PHRASE.finditer(seg):
        if m.start() > 70:
            break
        end = m.end()   # keep the head ('Department of Geography, University College Dublin')
    if end is None:
        return None
    # capitalised words right after the phrase belong to it ('University College Dublin') unless a lowercase word
    # follows them: then they open the next review's title ('Smith College' + a following book title)
    tail = re.match(rf"((?:\s+(?![A-ZÀ-Ý]\.){_CAP}){{1,2}})(?=\s*(?:$|[,.;)]|\d|[A-ZÀ-Ý]{{2,}}\b))", seg[end:])
    if tail:
        end += len(tail.group(1))
    out = seg[:end]
    # a mixed-case institution does not end in capitals: an institution + the next review's capitalised author
    if not out.isupper():
        while (m := re.search(r"[\s,]+([A-ZÀ-Ý][A-ZÀ-Ý'’\-]{1,})$", out)) and m.group(1) not in ('CUNY', 'MIT', 'UCLA', 'CNRS', 'EHESS', 'NBER', 'SUNY', 'LSE', 'UCL', 'CEU', 'USA', 'UK'):
            out = out[:m.start()]
    # and words the phrase took that open a title: drop trailing capitalised words followed by a lowercase word
    while True:
        m = re.search(rf"\s+({_CAP})$", out)
        nxt = seg[len(out):len(out) + 20]
        if m and re.match(r"\s+(?!of\b|at\b|for\b|de\b|di\b|du\b|des\b|in\b|und\b|and\b|the\b)[a-zà-ÿ]", nxt) and not INST.search(m.group(1)):
            out = out[:m.start()]
        else:
            break
    return out.strip(' ,;.') or None


def institution_after(text, e):
    seg = text[e:e + 160]
    seg = re.sub(r'^[\s,;.:\-–—]+', '', seg)
    st = STOP.search(' ' + seg)
    if st:
        seg = seg[:max(0, st.start() - 1)]
    seg = seg.strip(' ,;.')
    seg = re.split(r'\s{2,}|(?<=[a-z])\.\s', seg)[0]
    return trim_inst(seg) if seg and INST.search(seg) and len(seg) <= 140 else None


def institution_before(text, s):
    seg = text[max(0, s - 110):s]
    seg = re.split(r'[.!?;)]\s+(?=[A-Z])|[.!?]["”’]\s+', seg)[-1].strip(' ,;')
    return trim_inst(seg) if seg and INST.search(seg) and len(seg.split()) <= 12 and seg[:1].isupper() else None


def bio(text, e):
    m = re.match(r"\s*(?:\(|,)?\s*(?:is|was|teaches|received|holds|works|lectures|has taught)\b[^.]{0,200}?\b(?:at|in|from)\s+(?:the\s+)?"
                 r"(?P<i>(?:Department|School|Faculty|Institute|Centre|Center)[^.;]{0,80}?,\s*)?(?P<j>[A-Z][^.;]{2,100})", text[e:e + 320])
    if m and INST.search((m.group('i') or '') + m.group('j')):
        return trim_inst(((m.group('i') or '') + m.group('j')).strip(' ,'))
    return None


def signature(text, meta_title, names):
    ftext = fold1(text)
    n = len(text)
    head_end = min(n, 600)
    out = []
    for name in names:
        fam = fold(family(name))
        if len(fam) < 2:
            continue
        in_title = fam in fold(meta_title)
        in_head = re.search(r'(?<![a-z])' + re.escape(fam) + r'(?![a-z])', ftext[:head_end]) is not None
        hit = find_sig(text, ftext, name, int(n * 0.5) if n > 1500 else 0)
        if not hit:
            continue
        s, e, printed = hit
        pm = re.match(r"\s*,\s*([A-ZÀ-Ý][\w'’\-]+(?:[ \-][A-ZÀ-Ý][\w'’\-]+)?)\s*\.?\s*(?:$|\d|[A-ZÀ-Ý]{3,}|\s{2})", text[e:e + 60])
        place = pm.group(1) if pm and not INST.search(pm.group(1)) else None
        inst, where = bio(text, e), 'bio'   # a contributor note: 'NAME is professor of history at INSTITUTION'
        if not inst:
            inst, where = institution_after(text, e), 'after'
        if not inst:
            inst, where = institution_before(text, s), 'before'
        if not inst:
            where = 'end-only' if n - e < 40 else None
        if not where:
            continue
        conf = 0.9 if inst and not in_title and not in_head else 0.75 if inst else 0.6 if not in_title and not in_head else 0.3
        out.append(dict(creator=name, reviewer=printed, institution=inst, place=place, where=where, pos=round(e / max(n, 1), 3), conf=conf))
    if not out:
        return None
    out.sort(key=lambda r: (-r['conf'], -r['pos']))
    return out[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ids')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()
    want = {json.loads(l)['id'] for l in open(args.ids)} if args.ids else None
    c = sqlite3.connect(DB, uri=True)
    meta = {i.split(':')[-1]: (t or '', cr or '') for i, t, cr in
            c.execute("select item_id, title, creators_string from records where included and genre='book_review_as_deposited'")}
    tmp = args.out + '.tmp'
    C = Counter(); t0 = time.time()
    with gzip.open(SRC, 'rt', encoding='utf-8') as f, gzip.open(tmp, 'wt', encoding='utf-8') as o:
        for line in f:
            iid = line[9:45]
            if want is not None and iid not in want:
                continue
            r = json.loads(line)
            t, cr = meta[iid]
            names = creators(cr)
            C['reviews'] += 1
            if not names:
                C['no_names'] += 1
                continue
            text = re.sub(r'\s+', ' ', ' '.join(p for p in r['full_text'] if isinstance(p, str))).strip()
            sig = signature(text, re.sub(r'\s+', ' ', t), names)
            if not sig:
                C['no_signature'] += 1
                continue
            C['signed'] += 1; C['where:' + sig['where']] += 1; C['with_institution'] += bool(sig['institution'])
            C['conf>=0.75'] += sig['conf'] >= 0.75
            o.write(json.dumps(dict(iid=iid, **sig), ensure_ascii=False) + '\n')
            if C['reviews'] % 50000 == 0:
                print(dict(C), round(time.time() - t0), flush=True)
    os.replace(tmp, args.out)
    print(json.dumps(dict(C), indent=1), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
