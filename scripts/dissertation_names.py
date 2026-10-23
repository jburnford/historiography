#!/usr/bin/env python3
"""Surname and given name of a cited author printed without a comma.

Bibliography parsing takes 'Surname, Given' apart at the comma. Without one the whole name
became the surname, so 'GINZBURG Carlo', 'Robert Dallek', 'Sassoon D.' and 'Zhang Kuitang'
keyed works and people apart from 'Ginzburg, Carlo', 'Dallek, Robert' and so on (7.7% of
citable bibliography entries, most of them French 'NOM Prénom' in BASE theses; measured
2026-10-21). Notes name authors in natural order throughout.

Rules, in order (``split_name``):
1. trailing initials: 'Sassoon D.', 'De Niro MJ', 'Soeradi E.S' -> surname before them;
2. leading initials: 'M. MASSENZIO', 'P. De Souza' -> surname after them;
3. a run of capitalised tokens beside ordinary ones is the surname: 'GINZBURG Carlo',
   'Pierre BARRAL', 'EL HOUCINE Rahmoune', 'BEAUVALET-BOUTOUYRIE Scarlett';
4. otherwise the name order: 'natural' (notes; 'Given Surname', with particles: 'Alexis de
   Tocqueville' -> 'de Tocqueville') or 'surname_first' ('Zhang Kuitang', 'Confino Michael').
Particles stay as printed, as in inverted names; regnal names ('Léon XIII') and corporate
authors stay whole.

A bibliography's order is read from its own alphabetisation (``bibliography_order``): when
the first tokens of its comma-less author names run in alphabetical order and the last
tokens do not, names are surname-first, and the reverse means natural order. Without a clear
signal the name is left as it was. Corporate authors ('American Friends Service Committee')
and anything longer than five tokens are never split.
"""
import re
import unicodedata

PARTICLES = {'de', 'du', 'des', 'la', 'le', 'van', 'von', 'der', 'den', 'di', 'da', 'dos', 'das', 'del', 'della', 'ten', 'ter', "d'", 'd’'}
CORPORATE = re.compile(r'\b(?:committee|society|group|church|research|association|university|universit[éy]|department|commission|'
                       r'ministry|minist[èe]re|office|council|company|compagnie|institute|institut|library|biblioth[èe]que|archives?|'
                       r'bureau|board|government|gouvernement|service|services|foundation|fondation|league|union|party|parti|congress|'
                       r'conference|museum|mus[ée]e|center|centre|agency|corporation|bank|banque|press|club|federation|f[ée]d[ée]ration|'
                       r'staff|team|collective|collectif|project|world|nations|states|canada|qu[ée]bec|france|britain|anonymous|anonyme)\b',
                       re.I)
INITIALS = re.compile(r"(?:[A-ZÀ-Ý]\.?-?){1,3}\.?|[A-ZÀ-Ý]\.(?:-?[A-ZÀ-Ý]\.)+")


def _letters(tok):
    return ''.join(c for c in tok if c.isalpha())


def is_caps(tok):
    s = _letters(tok)
    return len(s) >= 2 and s.isupper()


def is_initials(tok):
    """'D', 'D.', 'MJ', 'E.S', 'J.-P.'; an undotted capital word of three or more letters is a
    surname ('RAY', 'LEE', 'HAO')."""
    n = len(_letters(tok))
    return bool(INITIALS.fullmatch(tok)) and (n <= 2 or '.' in tok and n <= 3)


def fold_token(t):
    t = unicodedata.normalize('NFKD', t)
    return ''.join(c for c in t if c.isalpha()).lower()


def split_name(name, order=None):
    """(surname, given) for a comma-less personal name, or None to leave it unchanged.
    ``order``: 'natural', 'surname_first' or None (decide only by rules 1-3)."""
    name = re.sub(r'(?<=\w)-\s+(?=\w)', '-', re.sub(r'\s+', ' ', name or '')).strip(' .,;')  # 'BRUNETON- GOVERNATORI'
    if not name or ',' in name or CORPORATE.search(name):
        return None
    toks = name.split(' ')
    if not 2 <= len(toks) <= 5 or any(not (t[:1].isupper() or t.lower() in PARTICLES or t[:2].lower() in ("d'", 'd’')) for t in toks):
        return None
    if not any(len(_letters(t)) >= 2 for t in toks):
        return None
    if any(re.fullmatch(r'(?=[IVXL])X{0,3}(?:IX|IV|V?I{0,3})|L?X{0,3}(?:IX|IV|V?I{0,3})', t.strip('.,')) and t.strip('.,') not in ('I', 'V', 'X', 'L')
           for t in toks[1:]):
        return None  # regnal and papal names ('Léon XIII', 'Pius XI') stay whole
    # 1. trailing initials
    k = len(toks)
    while k > 1 and is_initials(toks[k - 1]) and not (is_caps(toks[k - 1]) and k == len(toks) and all(is_caps(t) for t in toks)):
        k -= 1
    if 0 < k < len(toks) and not all(is_initials(t) for t in toks[:k]) and not is_caps(toks[k - 1]) or \
            0 < k < len(toks) and all(is_caps(t) for t in toks[:k]) and len(_letters(toks[k - 1])) > 3:
        return ' '.join(toks[:k]), ' '.join(toks[k:])
    # 2. leading initials
    j = 0
    while j < len(toks) - 1 and is_initials(toks[j]) and '.' in toks[j]:
        j += 1
    if j:
        return ' '.join(toks[j:]), ' '.join(toks[:j])
    # 3. a capitalised run among ordinary tokens
    caps = [i for i, t in enumerate(toks) if is_caps(t)]  # initials were taken by rules 1 and 2
    if caps and len(caps) < len(toks) and caps == list(range(caps[0], caps[-1] + 1)) and (caps[0] == 0 or caps[-1] == len(toks) - 1):
        a, b = caps[0], caps[-1] + 1
        while a > 0 and toks[a - 1].lower() in PARTICLES:
            a -= 1
        return ' '.join(toks[a:b]), ' '.join(toks[:a] + toks[b:])
    # 4. by order
    if order == 'natural':
        i = len(toks) - 1
        while i > 1 and toks[i - 1].lower() in PARTICLES:
            i -= 1
        return ' '.join(toks[i:]), ' '.join(toks[:i])
    if order == 'surname_first':
        i = 1
        if toks[0].lower() in PARTICLES and len(toks) > 2:
            i = 2
        return ' '.join(toks[:i]), ' '.join(toks[i:])
    return None


def bibliography_order(names):
    """'surname_first', 'natural' or None from the sequence (in entry order) of a thesis's
    comma-less author names that rules 1-3 leave undecided."""
    toks = [n.split() for n in names if n and 2 <= len(n.split()) <= 5]
    if len(toks) < 6:
        return None

    def sortedness(seq):
        seq = [fold_token(s) for s in seq if fold_token(s)]
        pairs = list(zip(seq, seq[1:]))
        return sum(a <= b for a, b in pairs) / len(pairs) if pairs else 0
    first, last = sortedness([t[0] for t in toks]), sortedness([t[-1] for t in toks])
    if first >= 0.8 and first - last >= 0.15:
        return 'surname_first'
    if last >= 0.8 and last - first >= 0.15:
        return 'natural'
    return None


def normalise_first_authors(entries, order=None):
    """Rewrite, in place, the first author of entries whose first author has no comma:
    ``authors[0]`` becomes 'Surname, Given' and ``surnames[0]`` the surname. ``entries`` are one
    thesis's entries in order; ``order`` None means read it from their alphabetisation.
    Returns the number of entries changed."""
    if order is None:
        undecided = [e['authors'][0] for e in entries if e.get('authors') and split_name(e['authors'][0]) is None
                     and ',' not in e['authors'][0] and not e.get('author_from_dash')]
        order = bibliography_order(undecided)
    changed = 0
    for e in entries:
        if not e.get('authors') or not e.get('surnames'):
            continue
        split = split_name(e['authors'][0], order)
        if not split:
            continue
        sur, given = split
        e['authors'][0] = f'{sur}, {given}'
        e['surnames'][0] = sur  # particles kept as printed, like inverted names ('de Certeau, Michel')
        changed += 1
    return changed
