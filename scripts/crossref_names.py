"""Shared name and title helpers for the Crossref dump matchers (2026-11-17).

Runs locally and on spark (no imports from the rest of the repo, so the file can be copied alone). The name
functions are copies of scripts/link_cited_work_authors.py (nfold, fam_norm, gwords, forms, name_level) with
LETTERS and PARTICLES from scripts/namesake_check_groups.py, so a family read here is the family the linkers use.
"""
import re
import unicodedata

LETTERS = str.maketrans({'ł': 'l', 'Ł': 'L', 'ø': 'o', 'Ø': 'O', 'đ': 'd', 'Đ': 'D', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe'})
PARTICLES = {'de', 'da', 'do', 'dos', 'das', 'e', 'van', 'von', 'der', 'den', 'la', 'le', 'du', 'di', 'del', 'y', 'jr',
             'sr', 'ii', 'iii', 'dr', 'orgs', 'org', 'ed', 'eds', 'mr', 'mrs', 'ms', 'miss', 'sir', 'rev', 'prof', 'hon',
             'lord', 'lady', 'dame', 'fr', 'sra', 'sr', 'dom', 'dona'}
SUFFIX = re.compile(r',?\s+(jr|sr|ii|iii|iv)\.?$', re.I)
TITLES = {'sir', 'dr', 'rev', 'prof', 'mr', 'mrs', 'ms', 'miss', 'jr', 'sr', 'ii', 'iii', 'iv', 'hon', 'lord', 'lady',
          'dame', 'fr', 'baron', 'baroness', 'count', 'countess', 'graf', 'freiherr', 'saint', 'st', 'father', 'sister',
          'brother', 'mother', 'dom', 'dona', 'don', 'mme', 'mlle', 'm', 'herr', 'frau', 'esq', 'phd', 'md'}


def nfold(s):
    return unicodedata.normalize('NFKD', (s or '').translate(LETTERS)).encode('ascii', 'ignore').decode().lower()


def fam_norm(s):
    ws = [w for w in re.split(r'[^a-z]+', nfold(s)) if w]
    while len(ws) > 1 and ws[0] in PARTICLES:
        ws = ws[1:]
    return ' '.join(ws)


def gwords(form):
    _, _, giv = form.partition(',')
    m = re.search(r'\(([^)]*)\)', giv)
    if m and re.search(r'[A-Za-z]{2}', m.group(1)):
        giv = m.group(1)
    else:
        giv = re.sub(r'\(.*?\)', ' ', giv)
    giv = giv.split(',')[0]
    giv = re.sub(r'\b(1[0-9]{3}|20[0-9]{2}|approximately|active|born|died|fl\.|b\.|d\.).*', '', giv)
    out = []
    for t in re.split(r"[\s\-‐.]+", giv.translate(LETTERS)):
        raw = t.strip("'’`\"")
        f = re.sub('[^a-z]', '', nfold(raw))
        if not f or f in TITLES and len(f) > 1:
            continue
        if raw[:1].islower() and (f in PARTICLES or f in ('e', 'y', 'd', 'l')):
            continue
        out.append(f)
    return out


def forms(label):
    """(family, 'Family, Given' form, given names) readings of a name."""
    label = SUFFIX.sub('', (label or '').strip().rstrip('.'))
    out = []
    if ',' in label:
        fam, _, giv = label.partition(',')
        out.append((fam_norm(fam), label))
    else:
        ws = label.split()
        if len(ws) < 2:
            return []
        out.append((fam_norm(ws[-1]), ws[-1] + ', ' + ' '.join(ws[:-1])))
        if len(ws) >= 3:
            out.append((fam_norm(' '.join(ws[-2:])), ' '.join(ws[-2:]) + ', ' + ' '.join(ws[:-2])))
    seen, res = set(), []
    for f, form in out:
        g = gwords(form)
        if f and g and f not in seen:
            seen.add(f)
            res.append((f, form, tuple(g)))
    return res


def families(label):
    """Every family reading of a printed name (for title matching, where the given name is not needed)."""
    label = SUFFIX.sub('', (label or '').strip().rstrip('.'))
    if not label:
        return set()
    if ',' in label:
        f = fam_norm(label.partition(',')[0])
        return {f} if f else set()
    ws = label.split()
    out = {fam_norm(ws[-1])}
    if len(ws) >= 3:
        out.add(fam_norm(' '.join(ws[-2:])))
    return {f for f in out if f}


def _close(a, b):
    lo, hi = sorted((a, b), key=len)
    return len(lo) >= 3 and hi.startswith(lo) or len(lo) >= 4 and re.sub(r'[aeiouy]+', '', a) == re.sub(r'[aeiouy]+', '', b)


def name_level(gs, gk):
    """'full' / 'variant' / 'initial' / None, as scripts/link_cited_work_authors.name_level."""
    if not gs or not gk:
        return None
    a, b = list(gs), list(gk)
    if len(a[0]) > 1 and len(b[0]) > 1:
        lev = 'full' if a[0] == b[0] else 'variant' if _close(a[0], b[0]) else None
        ra, rb = a[1:], b[1:]
    elif len(a[0]) == 1 and len(b[0]) == 1:
        lev = 'initial' if a[0] == b[0] else None
        ra, rb = a[1:], b[1:]
    else:
        x, y = (a, b) if len(a[0]) == 1 else (b, a)
        i = next((j for j, w in enumerate(x) if len(w) > 1), None)
        if i is not None and x[i] == y[0]:
            lev, ra, rb = 'full', x[i + 1:], y[1:]
        elif y[0].startswith(x[0]):
            lev, ra, rb = 'initial', x[1:], y[1:]
        else:
            return None
    if lev is None:
        return None
    short, long_ = (ra, rb) if len(ra) <= len(rb) else (rb, ra)

    def agree(w, t):
        lo, hi = sorted((w, t), key=len)
        return w == t or len(lo) == 1 and hi.startswith(lo) or _close(w, t)
    for w in short:
        if not any(agree(w, t) for t in long_):
            return None
    return lev


def fam_agree(fa, fb):
    """Two folded family names agree: equal, or one's words all in the other's (double surnames, hyphens)."""
    if not fa or not fb:
        return False
    if fa == fb:
        return True
    wa, wb = set(fa.split()), set(fb.split())
    wa = {w for w in wa if len(w) > 2} or wa
    wb = {w for w in wb if len(w) > 2} or wb
    return wa <= wb or wb <= wa


# ---- titles -------------------------------------------------------------------------------------------------
LEADING = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'los', 'las', 'il', 'lo', 'gli', 'o',
           'os', 'as', 'un', 'une', 'ein', 'eine', 'de', 'het', 'een'}
STOP = LEADING | {'of', 'and', 'in', 'on', 'for', 'to', 'at', 'by', 'with', 'from', 'et', 'du', 'des', 'en', 'und',
                  'im', 'zur', 'zum', 'von', 'del', 'di', 'da', 'do', 'dos', 'e', 'y', 'au', 'aux', 'its', 'his',
                  'her', 'their', 'into', 'as', 'or', 'is'}
DE_WORDS = {'und', 'der', 'des', 'dem', 'im', 'zur', 'zum', 'fur', 'uber', 'eine', 'einer', 'eines', 'einem', 'vom',
            'bei', 'mit', 'nach', 'zwischen', 'auf', 'aus', 'als', 'ihre', 'seine', 'sich', 'das', 'die', 'den',
            'geschichte', 'deutschen', 'deutsche', 'deutschland', 'jahrhundert', 'jahrhunderts', 'und', 'zeit',
            'unter', 'wahrend', 'gegen', 'bis', 'zu', 'beitrag', 'beitrage', 'studien', 'untersuchungen', 'reich',
            'kirche', 'politik', 'gesellschaft', 'wirtschaft', 'kultur', 'staat', 'stadt', 'jahre', 'jahren'}
FR_WORDS = {'le', 'la', 'les', 'du', 'et', 'avec', 'pour', 'dans', 'sur', 'au', 'aux', 'l', 'd', 'une', 'un', 'de',
            'del', 'el', 'los', 'las', 'y', 'e', 'il', 'della', 'di', 'o', 'os', 'em', 'na', 'no', 'het', 'een', 'van'}
EN_WORDS = {'the', 'of', 'and', 'in', 'on', 'for', 'to', 'a', 'an', 'with', 'from', 'by', 'its', 'their'}


def norm_title(t):
    t = re.sub(r'<[^>]+>', ' ', t or '')
    t = t.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    t = nfold(t)
    t = t.replace('&', ' and ')
    t = re.sub(r"['’`]", '', t)
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


def main_title(t):
    """Title before its subtitle: first ':' ';' ' = ' ' / ' or '. ' (LC style), else the whole title."""
    t = re.sub(r'<[^>]+>', ' ', t or '').replace('&amp;', '&')
    m = re.split(r'\s*[:;]\s+|\s*[:;]$|\s+=\s+|\s+/\s+|\.\s+(?=[A-Za-z])|\s+[–—-]\s+', t, maxsplit=1)
    return m[0] if m and m[0].strip() else t


def strip_leading(nt):
    ws = nt.split()
    if len(ws) > 1 and ws[0] in LEADING:
        ws = ws[1:]
    return ' '.join(ws)


def german(title):
    ws = re.findall(r'[a-z]+', nfold(title))
    if len(ws) < 2:
        return False
    de = sum(w in DE_WORDS for w in ws)
    en = sum(w in EN_WORDS for w in ws)
    fr = sum(w in FR_WORDS for w in ws)
    marks = bool(re.search(r'[äöüÄÖÜß]', title or ''))
    return en == 0 and fr < de and (de >= 2 or de >= 1 and marks)
