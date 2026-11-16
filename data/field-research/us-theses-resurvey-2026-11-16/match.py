"""Record linkage: AHA record <-> OpenAlex work. Surname + title words + year window + institution; one clear winner."""
import difflib
from common import *

SKIP = ('muse.jhu.edu', 'cambridge.org', 'europepmc.org', 'soas-repository', 'discovery.ucl.ac.uk', 'works.bepress.com', 'repository.upenn.edu/cgi/', 'repository.upenn.edu/dissertations/', 'repository.upenn.edu/edissertations/', 'ci.nii.ac.jp', 'ebscohost.com', 'search.ebscohost', 'bvbr.bib-bvb.de', 'proquest', 'dissertations.umi.com', 'umi.com', 'pqdtopen', 'researchgate', 'academia.edu', 'scribd', 'semanticscholar', 'core.ac.uk/download',
        'books.google', 'worldcat', 'catalog.', 'hathitrust', 'archive.org', 'jstor.org')
YEAR_LO, YEAR_HI = 3, 4


def author_tokens(work):
    return set(fold(' '.join(work.get('authors') or [])).split())


def score(rec, work):
    """(ok, score, why) for AHA record rec vs compact work (institution checked by the caller)."""
    sur = surname_words(rec['dissertator'])
    toks = author_tokens(work)
    if not sur or not toks:
        return False, 0, 'no author'
    if not (all(w in toks for w in sur) or (len(sur) > 1 and sur[-1] in toks and len(sur[-1]) > 3)):
        return False, 0, 'surname'
    t = work.get('title') or ''
    if re.search(r'\.pdf$|^\w+_\w+_\d+', t):
        return False, 0, 'file-name title'
    a, b = title_overlap(rec['title'], t)
    ratio = difflib.SequenceMatcher(None, fold(rec['title']), fold(t)).ratio()
    if not ((a >= 0.7 and b >= 0.5) or ratio >= 0.85):
        return False, 0, f'title {a:.2f}/{b:.2f}/{ratio:.2f}'
    y, wy = int(rec['year']), work.get('year')
    if not wy or not (y - YEAR_LO <= wy <= y + YEAR_HI):
        return False, 0, f'year {wy}'
    return True, round(a + b + ratio, 3), ''


def open_links(work):
    """Open non-commercial copies: list of (url, kind, source)."""
    out = []
    for l in work.get('locations') or []:
        if (l.get('source_type') or 'repository') not in ('repository', 'other'):
            continue
        for kind in ('pdf', 'landing'):
            u = l.get(kind)
            if not u or any(s in u.lower() for s in SKIP):
                continue
            out.append({'url': u, 'kind': kind, 'oa': l.get('oa'), 'source': l.get('source') or '',
                        'stype': l.get('source_type') or ''})
    return out


def link(records, works):
    """records: AHA rows of one institution; works: compact works believed to be of that institution.
    Returns {aha_id: (work, score, n_candidates)} with one clear winner per record and per work."""
    by_sur = {}
    for w in works:
        for t in author_tokens(w):
            by_sur.setdefault(t, []).append(w)
    cand = {}
    for r in records:
        sur = surname_words(r['dissertator'])
        if not sur:
            continue
        pool = {w['id']: w for w in by_sur.get(sur[-1], [])}
        hits = []
        for w in pool.values():
            ok, s, _ = score(r, w)
            if ok:
                hits.append((s, w))
        if not hits:
            continue
        hits.sort(key=lambda h: -h[0])
        # duplicates of one thesis (same folded title) are one candidate; distinct works must be beaten clearly
        top = hits[0]
        rivals = [h for h in hits[1:] if fold(h[1]['title']) != fold(top[1]['title']) and h[0] > top[0] - 0.15]
        if rivals:
            continue
        same = [h[1] for h in hits if fold(h[1]['title']) == fold(top[1]['title'])]
        merged = dict(top[1], locations=[l for w in same for l in w.get('locations') or []], dup_ids=[w['id'] for w in same])
        cand[r['id']] = (merged, top[0], len(hits))
    # one AHA record per work
    owner = {}
    for aid, (w, s, n) in cand.items():
        for wid in w['dup_ids']:
            owner.setdefault(wid, []).append((s, aid))
    out = {}
    for aid, (w, s, n) in cand.items():
        clash = False
        for wid in w['dup_ids']:
            others = [o for o in owner[wid] if o[1] != aid]
            if any(o[0] >= s - 0.15 for o in others):
                clash = True
        if not clash:
            out[aid] = (w, s, n)
    return out
