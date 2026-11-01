"""Checks on the AHA genealogy's advisor -> own-dissertation links (2026-11-01).

The genealogy (data/field-research/aha-dissertations-2026-10-13/genealogy/advisor-links.csv) links an advisor
token to their own dissertation record by 'unique name and date'. Benchmarked against the AHA historian
directory's PhD school, the links hold for about 2,490 advisors but join some to a namesake's dissertation:
- a shared initial: D. Graham Burnett -> 'Burnett, Dorothy' (Cornell 1930), Elsa Barkley Brown -> 'Brown, E.
  Canter', Judith Bennett -> 'Bennett, J. Harry' (1948);
- a hyphenated surname read as its last part: Beth Lew-Williams -> 'Williams, Beth Ann' (Illinois 2020), while
  'Lew-Williams, Beth' (Stanford 2011) is listed too;
- the same full name at another school: Alan Taylor (Brandeis) -> 'Taylor, Alan' (Georgetown 1958).

`doubts(link, record, directory_rows, records_by_family)` returns the reasons a link is doubtful:
- `school`: the directory gives a PhD school and it is not the dissertation's;
- `given`: the dissertation spells out a different given name (not just an initial);
- `hyphen:<record>`: the advisor's hyphenated surname is listed in full on another record with the same
  first given name (that record is theirs).
"""
import re
import unicodedata

ALIAS = {'nyu': 'new york', 'ucla': 'california los angeles', 'mit': 'massachusetts technology', 'cuny': 'city new york',
         'unc': 'north carolina', 'usc': 'southern california', 'lse': 'london economics', 'suny': 'new york',
         'grad': 'graduate', 'tech': 'technology', 'ucsb': 'california santa barbara', 'ucsd': 'california san diego',
         'ucb': 'california berkeley', 'uc': 'california', 'jhu': 'johns hopkins'}
STOP = {'univ', 'university', 'dept', 'department', 'history', 'college', 'coll', 'the', 'and', 'state', 'school', 'program',
        'graduate', 'studies', 'inst', 'institute', 'at', 'can', 'in', 'for', 'arts', 'sciences', 'faculty', 'division',
        'committee', 'center', 'centre', 'campus', 'main', 'universite', 'universidad', 'sch'}


def unmangle(s):
    """Repair UTF-8 read as Latin-1 ('QuÃ©bec' -> 'Québec'), as in parts of the directory harvest."""
    s = s or ''
    if 'Ã' in s or 'â' in s:
        try:
            return s.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def fold(s):
    s = unicodedata.normalize('NFKD', unmangle(s).replace('ı', 'i')).encode('ascii', 'ignore').decode().lower()
    return s.replace("'", '').replace('’', '')


def school(s):
    out = []
    for w in re.findall(r'[a-z]+', fold(s)):
        out += ALIAS.get(w, w).split()
    return {w[:5] for w in out if len(w) > 2 and w not in STOP and w not in ('uk',)}


def school_agrees(a, b):
    sa, sb = school(a), school(b)
    return bool(sa and sb) and (sa <= sb or sb <= sa)


def words(s):
    return set(re.findall(r'[a-z]+', fold(s)))


def doubts(advisor_name, record, directory_rows, records_by_family):
    out = []
    ds = [d['degree_school'] for d in directory_rows if d['degree_school'] and d['degree'].upper() in ('PHD', 'DPHIL')]
    if ds and not any(school_agrees(d, record['department']) for d in ds):
        out.append('school')
    dis = record['dissertator']
    if not (words(dis) <= words(advisor_name) or words(advisor_name) <= words(dis)):
        gd = {g for g in re.findall(r'[a-z]+', fold(dis.partition(', ')[2])) if len(g) > 1}
        ga = {g for g in re.findall(r'[a-z]+', fold(' '.join(advisor_name.split()[:-1]))) if len(g) > 1}
        if gd - ga and ga - gd:
            out.append('given')
    last = fold(advisor_name.split()[-1]) if advisor_name.split() else ''
    if '-' in last:
        first = fold(advisor_name).split()[:1]
        for y in records_by_family.get(last.replace('-', ' '), ()):
            if y['id'] != record['id'] and fold(y['dissertator'].partition(', ')[2]).split()[:1] == first:
                out.append(f'hyphen:{y["id"]}')
                break
    return out


def family_index(records):
    out = {}
    for r in records:
        out.setdefault(fold(r['dissertator'].partition(', ')[0]).replace('-', ' ').strip(), []).append(r)
    return out


def same_listed_name(a, b):
    """One listing's name words contain the other's ('Smith, Caleb' / 'Smith, D. Caleb'; accents and hyphens
    folded). Family name and initial alone are not enough here: 'Taylor, Kerry' / 'Taylor, Kieran'."""
    wa, wb = words(a), words(b)
    return wa <= wb or wb <= wa


def title_words(title):
    return set(re.findall(r'[a-z]{4,}', fold(title)))


def duplicate_pairs(records):
    """One dissertation under two record ids: same school, years within one, at least 80% of the shorter
    title's words of four or more letters shared (two or more), same family name."""
    by_name = {}
    for r in records:
        if r['title'] and r['title'] != '[No title]' and (r['year'] or '').isdigit():
            by_name.setdefault(''.join(re.findall(r'[a-z0-9]+', fold(r['dissertator'].partition(', ')[0]))), []).append(r)
    pairs = []
    for rs in by_name.values():
        for i, x in enumerate(rs):
            for y in rs[i + 1:]:
                wx, wy = title_words(x['title']), title_words(y['title'])
                shared = len(wx & wy)
                if (abs(int(x['year']) - int(y['year'])) <= 1 and x['department'].split(',')[0] == y['department'].split(',')[0]
                        and shared >= 2 and shared >= 0.8 * min(len(wx), len(wy))):
                    pairs.append((x, y))
    return pairs


def rank_floor(rank):
    """Earliest plausible PhD year for a directory entry's rank (the directory is current, 2026)."""
    r = fold(rank)
    if 'emerit' in r or 'retired' in r:
        return 1945
    if 'asst' in r or 'assistant' in r:
        return 2003
    if 'assoc' in r:
        return 1985
    return 1960


def directory_records(rows, by_family, compatible):
    """AHA records that can be a directory historian's own dissertation: listed under their surname (a
    hyphenated one in full), the same first given name and a compatible name, at the PhD school the directory
    gives, no earlier than their rank allows. `rows` are the token's directory rows; `compatible` is
    identity_routes.compatible."""
    phd = [r for r in rows if r['degree'].upper() in ('PHD', 'DPHIL') and r['degree_school']]
    if not phd:
        return []
    name = phd[0]['name']
    parts = name.split()
    if len(parts) < 2:
        return []
    family, first = fold(parts[-1]).replace('-', ' '), fold(name).split()[:1]
    floor = min(rank_floor(r['rank']) for r in phd)
    out = []
    for x in by_family.get(family, ()):
        fam, _, giv = x['dissertator'].partition(', ')
        if (x['year'].isdigit() and int(x['year']) >= floor and fold(giv).split()[:1] == first
                and compatible(name, giv, fam) and any(school_agrees(r['degree_school'], x['department']) for r in phd)):
            out.append(x)
    return out


def first_and_family(name):
    """'Erika Dyck' or 'Dyck, Erika' -> ('erika', 'dyck'); a hyphenated surname stays whole ('lew williams')."""
    family, comma, given = name.partition(', ')
    if not comma:
        parts = name.split()
        if len(parts) < 2:
            return None
        family, given = parts[-1], ' '.join(parts[:-1])
    g = [w for w in re.findall(r'[a-z]+', fold(given)) if len(w) > 1]
    f = ' '.join(re.findall(r'[a-z]+', fold(family)))
    return (g[0], f) if g and f else None


def employer_matches(directory_rows, people_by_name, org_match):
    """token -> registry individual, where the AHA directory's employer agrees with an affiliation on that
    individual's own records (Crossref authorships, H-Net and Reviews in History reviews) and the full first
    name and surname agree. Unique both ways: one individual for the token, and one directory token of that
    name at that employer. `people_by_name`: (first, family) -> {individual: [affiliations]}."""
    hits = {}
    for token, rows in directory_rows.items():
        nm = first_and_family(rows[0]['name']) if rows else None
        if not nm:
            continue
        found = {iid for iid, affs in people_by_name.get(nm, {}).items()
                 for r in rows if r['institution'] for a in affs if org_match(a, r['institution'])}
        if len(found) == 1:
            hits[token] = (next(iter(found)), nm, frozenset(r['institution'] for r in rows))
    same = {}
    for token, (iid, nm, insts) in hits.items():
        same.setdefault((iid,), []).append(token)
    return {t: h[0] for t, h in hits.items() if len(same[(h[0],)]) == 1}
