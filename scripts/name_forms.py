"""Family-name structure and the shorter or longer forms of a name (2026-11-12; ARCHITECTURE.md section 8, class 37).

Pure functions. Nothing here decides identity: a form relation only says that two printed names COULD be one person
under a family-name change (record linkage: name-form compatibility makes a candidate pair; evidence decides, in
scripts/name_form_ties.py).

Classes of change handled:
- two family names, one dropped ('Chust Calero, Manuel' / 'Manuel Chust'; 'Bolufer Peruga, Mónica' / 'Mónica
  Bolufer'; Portuguese order, where the LAST family name is the main one: 'Souza Santos' / 'Santos');
- hyphenated or double-barrelled names where a part is dropped or added ('Smith-Norris, Martha' / 'Martha Smith');
- an earlier family name kept as a middle name ('Labelle, Kathryn Magee' / 'Kathryn Magee'): relation
  'middle-as-family'. Structurally this is the same as the unhyphenated double family read the other way; only a
  stated tie can tell them apart, so callers must not create a candidate from it without one.

Given names compare as in scripts/propose_person_dup_merges.strict_agree (the first written-out given name identical,
every other given name of the shorter list present or an initial of one; no short forms, no nicknames: the owner's
2026-11-12 standard of caution). Folding, particles and readings of a name without a comma are the linkers' own
(scripts/link_cited_work_authors.forms / fam_norm / gwords), so a form produced here lands in the same family index
the linkers use.
"""
import re
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from link_cited_work_authors import LETTERS, fam_norm, forms, gwords, nfold  # noqa: E402

# family-name particles (attach to the following word) and conjunctions between two family names
PARTICLES = {'de', 'del', 'della', 'delle', 'dello', 'da', 'das', 'do', 'dos', 'di', 'du', 'la', 'las', 'los', 'le',
             'les', 'lo', 'van', 'von', 'der', 'den', 'ten', 'ter', 'zu', 'zum', 'zur', "d'", 'dal', 'dei', 'degli'}
JOIN = {'y', 'e', 'i'}          # 'Ortega y Gasset', 'Oliveira e Costa', Catalan 'Puig i Cadafalch'
# generational words printed as the last family word ('Reis Filho', 'Coelho Neto', 'Alambert Junior'): not a family name;
# a name with and without one may be a father and a son, so a pair differing only by it is 'suffix-dropped' and needs
# a stated tie like every other relation
GENERATIONAL = {'filho', 'neto', 'junior', 'jr', 'sobrinho', 'bisneto'}

# naming convention by country (ISO 3166 alpha-2) and by language of works
SPANISH_CC = {'ES', 'MX', 'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'BO', 'PY', 'UY', 'CR', 'PA', 'GT', 'HN', 'SV', 'NI',
              'CU', 'DO', 'PR'}
PORTUGUESE_CC = {'BR', 'PT', 'AO', 'MZ', 'CV', 'GW', 'ST', 'TL'}
SPANISH_LANG = {'es', 'spa', 'ca', 'cat', 'gl', 'glg'}
PORTUGUESE_LANG = {'pt', 'por'}

# relation types
DROPS_SECOND = 'drops-second-family'        # 'Chust Calero' -> 'Chust'
DROPS_FIRST = 'drops-first-family'          # 'Souza Santos' -> 'Santos'
HYPHEN_DROPPED = 'hyphen-part-dropped'      # 'Smith-Norris' -> 'Smith' or 'Norris'
MIDDLE_AS_FAMILY = 'middle-as-family'       # 'Labelle, Kathryn Magee' -> 'Magee, Kathryn' (needs a stated tie)
SUFFIX_DROPPED = 'suffix-dropped'           # 'Reis Filho, Daniel Aarão' -> 'Reis, Daniel Aarão' (father or son?)
FAMILY_SPELLING = 'family-spelling'         # 'Mendelson' / 'Mendelsohn', 'Mc Evoy' / 'McEvoy': not a change of name

Structure = namedtuple('Structure', 'family parts particles kind hyphenated joined given form raw reading suffix')
Form = namedtuple('Form', 'family given label relation kept primary_kept reading')


def _fold_word(w):
    return re.sub(r'[^a-z]', '', nfold((w or '').translate(LETTERS)))


def family_parts(raw_family):
    """(parts, particles, hyphenated, joined) of a printed family name; see _family_parts."""
    return _family_parts(raw_family)[:4]


def _family_parts(raw_family):
    """'Rostworowski de Diez Canseco' -> (['rostworowski', 'diez', 'canseco'], ['', 'de', ''], hyphenated, joined).
    Particles attach to the following word and are not parts themselves; a conjunction between two family names is
    dropped (joined=True); a hyphen splits a token into parts (hyphenated=True). A leading particle ('de la Fuente')
    stays a particle of the first part."""
    raw = (raw_family or '').translate(LETTERS).replace('‐', '-').replace('‑', '-')
    raw = re.sub(r"\b([dD])['’]\s*", r"\1' ", raw)          # d'Alembert -> d' Alembert
    parts, particles, pending = [], [], []
    raws = []
    hyphenated = joined = False
    suffix = ''
    toks = raw.split()
    for i, tok in enumerate(toks):
        sub = [s for s in tok.split('-') if s]
        if len(sub) > 1:
            hyphenated = True
        for s in sub:
            f = _fold_word(s) if not s.endswith("'") else _fold_word(s) + "'"
            if not f:
                continue
            is_last = i == len(toks) - 1 and s is sub[-1]
            if f in PARTICLES and not is_last:
                pending.append(f)
                continue
            if f in JOIN and parts and not is_last and len(sub) == 1 and s[:1].islower():
                joined = True
                continue
            if len(f.rstrip("'")) < 2:           # an initial ('Benjamin V Allison') is not a family name
                continue
            if f in GENERATIONAL and parts:
                suffix = f
                continue
            parts.append(f.rstrip("'"))
            raws.append(s)
            particles.append(' '.join(pending))
            pending = []
    return parts, particles, hyphenated, joined, raws, suffix      # raws: printed spelling of each part


def structure(label):
    """The family-name structure of each reading of a name (a name without a comma has one reading per possible
    family: 'Manuel Chust Calero' reads 'Calero, Manuel Chust' and 'Chust Calero, Manuel'). -> [Structure].
    kind: 'single', 'double' (two or more family names, space or conjunction separated), 'hyphenated' (all parts from
    one hyphenated word) or 'compound' (hyphen and space)."""
    out = []
    plain = ',' not in (label or '')
    for fam, form, given in forms(label or ''):
        raw_fam = form.split(',')[0]
        parts, parts_p, hyph, joined, raw_parts, suffix = _family_parts(raw_fam)
        raw_parts = tuple(raw_parts)
        if not parts:
            continue
        if len(parts) == 1:
            kind = 'single'
        elif hyph and len(raw_fam.split()) == 1:
            kind = 'hyphenated'
        elif hyph:
            kind = 'compound'
        else:
            kind = 'double'
        # 'plain-double': a name printed without a comma read with its last two words as the family ('Manuel Chust
        # Calero' as 'Chust Calero, Manuel'); the same words may be a middle name and a family ('Thomas Richard
        # Davies'), so forms from this reading are ambiguous
        reading = 'comma' if not plain else ('plain-double' if len(raw_fam.split()) >= 2 else 'plain')
        if reading == 'plain-double':
            w0, w1 = raw_fam.split()[0], raw_fam.split()[-1]
            if len(_fold_word(w0)) < 2 or '-' in w1 or '-' in w0:
                continue        # 'Jose A. Canton-Alvarez', 'Thomas Alexander Khan-White': the family is the last word
        out.append(Structure(fam, tuple(parts), tuple(parts_p), kind, hyph, joined, tuple(given), form, raw_parts, reading,
                             suffix))
    return out


def convention(countries=(), languages=()):
    """'spanish', 'portuguese' or None from the countries of a person's PhD and institutions and the languages of
    their works (most frequent wins; a tie or no evidence -> None). Returns (convention, evidence counts)."""
    n_es = sum(1 for c in countries if (c or '').upper() in SPANISH_CC) + \
        sum(1 for x in languages if (x or '').lower() in SPANISH_LANG)
    n_pt = sum(1 for c in countries if (c or '').upper() in PORTUGUESE_CC) + \
        sum(1 for x in languages if (x or '').lower() in PORTUGUESE_LANG)
    if n_es > n_pt:
        return 'spanish', {'es': n_es, 'pt': n_pt}
    if n_pt > n_es:
        return 'portuguese', {'es': n_es, 'pt': n_pt}
    return None, {'es': n_es, 'pt': n_pt}


ES_WORDS = {'el', 'los', 'las', 'del', 'historia', 'una', 'entre', 'siglo', 'y', 'en', 'para', 'por', 'sobre', 'como',
            'españa', 'espana', 'mexico', 'méxico', 'nueva', 'politica', 'política', 'sociedad', 'guerra', 'revolución'}
PT_WORDS = {'os', 'as', 'do', 'dos', 'das', 'da', 'história', 'historia', 'uma', 'no', 'na', 'nos', 'nas', 'e', 'em',
            'brasil', 'século', 'seculo', 'política', 'sociedade', 'não', 'ao', 'aos', 'pelo', 'pela', 'são', 'sao'}
ES_ONLY = {'el', 'los', 'las', 'del', 'y', 'en', 'una', 'españa', 'sociedad', 'nueva', 'siglo', 'revolución'}
PT_ONLY = {'os', 'do', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'em', 'ao', 'aos', 'pelo', 'pela', 'não', 'são',
           'brasil', 'século', 'sociedade', 'uma'}


def title_language(title):
    """'es', 'pt' or None from function words of a title (only the two languages whose naming conventions differ
    here; anything else -> None). Spelling marks decide close cases: 'ção', 'ões', 'ã' Portuguese; 'ñ', 'ción' Spanish."""
    t = (title or '').lower()
    ws = re.findall(r"[a-zà-ÿ]+", t)
    if len(ws) < 3:
        return None
    es = sum(w in ES_ONLY for w in ws) + 2 * bool(re.search(r'ción\b|ciones\b|ñ', t))
    pt = sum(w in PT_ONLY for w in ws) + 2 * bool(re.search(r'ção\b|ções\b|ões\b|ã', t))
    if es >= 2 and es > pt:
        return 'es'
    if pt >= 2 and pt > es:
        return 'pt'
    return None


def primary_part(st, conv):
    """index of the main family name under a convention: Spanish the first, Portuguese the last; None if unknown or
    the name is not a two-family name (a hyphenated English name has no main part)."""
    if st.kind not in ('double', 'compound') or len(st.parts) < 2:
        return None
    if conv == 'spanish':
        return 0
    if conv == 'portuguese':
        return len(st.parts) - 1
    return None


def _label(parts, particles, given_label):
    fam = ' '.join(((p + ' ') if p else '') + w for p, w in zip(particles, parts)).strip()
    return f'{fam}, {given_label}' if given_label else fam


def _given_label(form):
    return form.partition(',')[2].strip()


def shorter_forms(label, conv=None):
    """Forms of the name with one family name dropped -> [Form]. For each reading with two or more family names:
    the first alone (drops-second-family, or hyphen-part-dropped) and the last alone (drops-first-family, or
    hyphen-part-dropped); for three or more, the first two and the last two as well. `primary_kept` says whether the
    kept part is the main family name under `conv` (None when unknown). The family is folded as the linkers fold it
    (fam_norm), so a Form's family is a key into their family index."""
    out, seen = [], set()
    for st in structure(label):
        if st.suffix:
            fam = fam_norm(' '.join(((p + ' ') if p else '') + w for p, w in zip(st.particles, st.parts)))
            if fam and fam != st.family and (fam, st.given) not in seen:
                seen.add((fam, st.given))
                out.append(Form(fam, st.given, _label(st.raw, st.particles, _given_label(st.form)), SUFFIX_DROPPED,
                                ' '.join(st.parts), None, st.reading))
        if len(st.parts) < 2:
            continue
        n = len(st.parts)
        prim = primary_part(st, conv)
        hyph = st.kind == 'hyphenated'
        spans = [((0, 1), DROPS_SECOND), ((n - 1, n), DROPS_FIRST)]
        if n >= 3:
            spans += [((0, 2), DROPS_SECOND), ((n - 2, n), DROPS_FIRST)]
        gl = _given_label(st.form)
        for (i, j), rel in spans:
            parts, pp = st.parts[i:j], st.particles[i:j]
            fam = fam_norm(' '.join(((p + ' ') if p else '') + w for p, w in zip(pp, parts)))
            key = (fam, st.given)
            if not fam or key in seen or fam == st.family:
                continue
            seen.add(key)
            pk = None if prim is None else (i <= prim < j)
            out.append(Form(fam, st.given, _label(st.raw[i:j], pp, gl), HYPHEN_DROPPED if hyph else rel,
                            ' '.join(parts), pk, st.reading))
    return out


def middle_as_family_forms(label):
    """'Labelle, Kathryn Magee' -> Form('magee', ('kathryn',), 'Magee, Kathryn', 'middle-as-family'): the last
    written-out given name read as an earlier family name. Every person with a middle name produces one, so this is
    never a candidate by itself (only with a stated tie: an LC 400, a Wikidata alias, an ORCID other name)."""
    out = []
    for st in structure(label):
        g = st.given
        if len(g) >= 2 and len(g[0]) > 1 and len(g[-1]) > 1:
            out.append(Form(g[-1], g[:-1], f'{g[-1].capitalize()}, {" ".join(w.capitalize() for w in g[:-1])}',
                            MIDDLE_AS_FAMILY, g[-1], None, st.reading))
    return out


def given_agree(ga, gb):
    """Given names agree in full (propose_person_dup_merges.strict_agree): the first written-out given name identical,
    every other given name of the shorter list equal to one of the longer's or an initial of one. No short forms."""
    if not ga or not gb:
        return False
    wa = [w for w in ga if len(w) > 1]
    wb = [w for w in gb if len(w) > 1]
    if not wa or not wb or wa[0] != wb[0]:
        return False
    short, long_ = (list(ga), list(gb)) if len(ga) <= len(gb) else (list(gb), list(ga))
    rest = list(long_)
    for w in short:
        hit = next((t for t in rest if t == w or (len(w) == 1 and t[0] == w) or (len(t) == 1 and w[0] == t)), None)
        if hit is None:
            return False
        rest.remove(hit)
    return True


Relation = namedtuple('Relation', 'relation long short kept primary_kept reading')
SAME_WORDS = 'same-words'       # the same words read as two families ('Díaz del Castillo, Bernal' / 'Bernal Díaz del Castillo')


def words(label):
    """the folded words of a name, particles and dates dropped (for the same-words test)"""
    lab = re.sub(r'\(.*?\)|\b1[0-9]{3}\b.*$|\b20[0-9]{2}\b.*$', ' ', label or '')
    ws = [_fold_word(w) for w in re.split(r"[\s,\-\u2010.]+", lab.translate(LETTERS))]
    return sorted(w for w in ws if len(w) > 1 and w not in PARTICLES and w not in JOIN)


def short_given_ok(short_given, long_given):
    """every written-out given name of the short side is a given name of the long side: an extra written word on the
    short side may be its own first family name ('Francisco Javier Pérez Rodríguez' is not a short form of
    'Rodríguez Méndez, Francisco Javier')"""
    lw = set(long_given)
    return all(w in lw for w in short_given if len(w) > 1)


def relation(a, b, conv=None, middle=False):
    """How two names relate by a family-name change, or [] when they do not (or already share a family name, which
    the ordinary name rules handle). -> [Relation(relation, long label, short label, kept part, primary_kept)].
    Given names must agree in full (given_agree). middle=True also tests 'middle-as-family' (stated ties only)."""
    fa = {(s.family, s.given) for s in structure(a)}
    fb = {(s.family, s.given) for s in structure(b)}
    if {f for f, _ in fa} & {f for f, _ in fb}:
        return []
    wa, wb = words(a), words(b)
    if wa and wa == wb and len(wa) >= 3:
        return [Relation(SAME_WORDS, a, b, '', None, 'same-words')]
    out = []
    for long_, short, fshort in ((a, b, fb), (b, a, fa)):
        cands = shorter_forms(long_, conv) + (middle_as_family_forms(long_) if middle else [])
        for f in cands:
            if any(f.family == fam and given_agree(f.given, g) and short_given_ok(g, f.given) for fam, g in fshort):
                r = Relation(f.relation, long_, short, f.kept, f.primary_kept, f.reading)
                if r not in out:
                    out.append(r)
    return out


def direction(long_years, short_years):
    """For a hyphenated or double name: 'added' when the short form's works end before the long form's begin (a part
    taken later, e.g. at marriage), 'dropped' when the long form's end before the short's begin, else None."""
    ly = [y for y in long_years if y]
    sy = [y for y in short_years if y]
    if not ly or not sy:
        return None
    if max(sy) <= min(ly):
        return 'added'
    if max(ly) <= min(sy):
        return 'dropped'
    return None


def _lev(a, b):
    if abs(len(a) - len(b)) > 2:
        return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def spelling_variant(fam_a, fam_b):
    """Two folded family names that are one name spelled two ways: spacing ('mc evoy' / 'mcevoy', 'de voto' /
    'devoto'), German umlaut transcriptions ('kuehne' / 'kuhne'), or at most two letters apart ('mendelson' /
    'mendelsohn', 'donlon' / 'donlan'). Not a family-name change; outside this module's classes (the general folding
    rules own them)."""
    def sk(f):
        f = re.sub(r'[^a-z]', '', f)
        return re.sub(r'(?<=[aou])e', '', f)
    a, b = sk(fam_a), sk(fam_b)
    return a == b or (min(len(a), len(b)) >= 4 and _lev(a, b) <= 2)


def same_form(a, b):
    """Two printed names are the same form (family identical after folding and given names agree in full)."""
    return any(sa.family == sb.family and given_agree(sa.given, sb.given) for sa in structure(a) for sb in structure(b))
