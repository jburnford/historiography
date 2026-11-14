"""Read the reviewed author and book title a review's own label prints (2026-11-14; ARCHITECTURE.md section 8, class 41).

Forms (after review_books.clean_label strips 'Review of', 'Book Review:', quotes and '[review]' suffixes):
- 'Given Family, Title' / 'Given FAMILY: Title' / 'Given Family. Title'          (name first, given name first)
- 'Family, Given. Title' / 'FAMILY, Given: Title' / 'Family, Given (2014) Title'  (name first, family first)
- 'Title. By Given Family' / 'Title. Edited by Given Family'                   (name after the title)
The title runs to the first publisher, place, year, page or price clause ('Baton Rouge, ... Press, 240 pp.'). A name
needs two to five words, a capitalised family of two letters or more, and at least one written-out given name (initials
alone never). Editors ('(ed.)', '(eds)', 'Edited by') are kept apart (role editor). ISBNs are read whole.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_books import ISBN, NOT_REVIEW, clean_label  # noqa: E402

UP = "A-ZÀ-ÞĀ-ſ"
GIVEN_TOK = rf"(?:[{UP}]\.(?:\s*-?[{UP}]\.)*|[{UP}][a-zß-ÿā-ſ'’]+(?:-[{UP}][a-zß-ÿā-ſ'’]+)?)"
FAM_TOK = rf"(?:(?:de|da|del|della|di|du|dos|das|van|von|der|den|la|le|ten|ter|van der|van den|de la|von der)\s+)?" \
          rf"(?:[{UP}][{UP}'’\-]+|[{UP}][a-zß-ÿā-ſ'’]+(?:-[{UP}][a-zß-ÿā-ſ'’]+)?|Mc[{UP}][a-z]+|Mac[{UP}][a-z]+|O['’][{UP}][a-z]+)"
EDIT = r"\s*(?:\((?:eds?|dir|hrsg|hg|coord|org|comp)s?\.?\)|,?\s+(?:eds?|dir|hrsg|hg)\.)"
# 'Given [Given] Family[, Given Family] (eds.)?' then ',' ':' or '.' and the title
GIVEN_FIRST = re.compile(rf"^((?:{GIVEN_TOK}\s+){{1,3}}{FAM_TOK}(?:\s+{FAM_TOK})?)"
                         rf"((?:\s*(?:,|and|et|und|y|&)\s*(?:{GIVEN_TOK}\s+){{1,3}}{FAM_TOK})*)({EDIT})?\s*[,:.]\s+(.{{6,}})$")
FAMILY_FIRST = re.compile(rf"^({FAM_TOK}(?:\s+{FAM_TOK})?),\s*((?:{GIVEN_TOK}\s*?){{1,3}}?)({EDIT})?\s*(?:\(\d{{4}}\)\s*|[,:]\s+|(?<=\.)\s+|\.\s+)(.{{6,}})$")
BY_AFTER = re.compile(rf"^(.{{8,250}}?)[.,]\s+(?:By|BY|by|Edited by|edited by|Ed\. by|Par|par|Von|von|Por|por|Hg\. von|Hrsg\. von)\s+"
                      rf"((?:{GIVEN_TOK}\s+){{1,3}}{FAM_TOK}|{FAM_TOK},?\s+(?:{GIVEN_TOK}\s*){{1,3}})")
# where the book title ends: a publisher, place, year, pages, price, series or ISBN clause
TAIL = re.compile(r"(?:[,.]?\s*\((?:[^()]*?\d{4}[^()]*)\)|[,.]\s*(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*:\s*[A-Z]|"
                  r"[^,.]*\b(?:Press|Presses|University|Universit[äyé]|Verlag|Editions?|Éditions|Editorial|Editora|Publishers?|"
                  r"Publishing|Publicacions|Publicaciones|Universitat|Books|Routledge|Palgrave|Brill|Springer|Harmattan|Gallimard|Seuil|Fayard|Karthala|Lit|Peter Lang)\b)|"
                  r"[,.]\s*(?:\d{4}\b|\d+\s*(?:pp|p|S|pages|págs?)\b|pp\.|ISBN|xi|xv|xx|[$£€])|\s+ISBN\b|\s*\[[^\]]*\]\s*$|"
                  r"[,.]\s*(?:Baton Rouge|New York|London|Paris|Toronto|Montreal|Montréal|Chicago|Oxford|Cambridge|Berlin|"
                  r"Madrid|Lisboa|Rome|Roma|Milan|Milano|München|Munich|Stuttgart|Frankfurt|Leiden|Boston|Durham|Vancouver|"
                  r"Lincoln|Ithaca|Berkeley|Princeton|New Haven|Philadelphia|Chapel Hill|Edinburgh|Manchester|Basingstoke|"
                  r"Cham|Kingston|Ottawa|Québec|Winnipeg|Athens|Lanham|Westport|Amsterdam|Göttingen|Wien|Bern|Leipzig|"
                  r"Barcelona|México|Mexico|Buenos Aires|São Paulo|Rio de Janeiro|Rennes|Lyon|Bruxelles|Brussels|Genève)\b)")


def cut_title(t):
    t = re.sub(r'\s+', ' ', t).strip(' "“”«»\'')
    m = TAIL.search(t)
    if m and m.start() >= 6:
        t = t[:m.start()]
    return t.strip(' ,.;:"“”«»')


def norm_name(given, fam):
    fam = ' '.join(w if not w.isupper() or len(w) < 2 else w.capitalize() for w in fam.split())
    fam = re.sub(r"-(\w)", lambda m: '-' + m.group(1).upper(), fam)
    return f"{fam}, {' '.join(given.split())}"


def written_given(given):
    return any(len(re.sub(r'[.\-]', '', w)) > 1 for w in given.split())


ARTICLE = re.compile(r"^(?:The|A|An|Le|La|Les|L|Un|Une|El|Los|Las|Lo|Il|Gli|I|Der|Die|Das|Ein|Eine|O|Os|As|De|Het|Een|"
                     r"In|On|Of|For|From|With|Between|Toward|Towards|After|Before|Beyond|Under|Through|Into|Inside|"
                     r"Histoire|History|Geschichte|Historia|Storia|Making|Writing|Reading|Rethinking|Remaking)$")


def given_ok(given):
    ws = given.split()
    return written_given(given) and not any(ARTICLE.match(w.strip('.')) for w in ws)


def parse(label):
    """-> list of readings dict(names=['Family, Given', ...], role='author'|'editor', title, form) and the ISBNs
    printed, or None. A label can read two ways ('Marcelo Casals, Contrarrevolución, ...' given first; 'Figueras
    Vallés, Estrella, Pervirtiendo ...' family first): every reading is returned and the matcher keeps the one whose
    person and title fit."""
    raw = re.sub(r'<[^>]+>', '', label or '')
    if NOT_REVIEW.match(raw):
        return None
    isbns = sorted({re.sub(r'[^0-9Xx]', '', m.group(1)).upper() for m in ISBN.finditer(raw)
                    if len(re.sub(r'[^0-9Xx]', '', m.group(1))) in (10, 13)})
    body, _ = clean_label(raw)
    body = re.sub(r'^(?:Book Reviews?|Review)\s*[:)\]]\s*', '', body, flags=re.I).strip(' "“”«»:')
    reads = []
    m = FAMILY_FIRST.match(body)
    if m and given_ok(m.group(2)) and not ARTICLE.match(m.group(1).split()[0]):
        reads.append(dict(names=[norm_name(m.group(2), m.group(1))], role='editor' if m.group(3) else 'author',
                          title=cut_title(m.group(4)), form='family-first'))
    m = GIVEN_FIRST.match(body)
    if m:
        ws = m.group(1).split()
        for fam_n in ((1, 2) if len(ws) >= 3 and len(ws[-2].strip('.')) > 1 else (1,)):
            given, fam = ' '.join(ws[:-fam_n]), ' '.join(ws[-fam_n:])
            if given_ok(given) and ws[-1] not in ('The', 'A', 'An', 'Le', 'Les', 'El', 'Il'):
                names = [norm_name(given, fam)]
                for g in re.finditer(rf"((?:{GIVEN_TOK}\s+){{1,3}})({FAM_TOK})", m.group(2) or ''):
                    if given_ok(g.group(1)):
                        names.append(norm_name(g.group(1), g.group(2)))
                reads.append(dict(names=names, role='editor' if m.group(3) else 'author', title=cut_title(m.group(4)),
                                  form='given-first'))
    m = BY_AFTER.match(body)
    if m:
        nm = m.group(2).strip()
        if ',' in nm:
            fam, given = [x.strip() for x in nm.split(',', 1)]
        else:
            ws = nm.split()
            given, fam = ' '.join(ws[:-1]), ws[-1]
        if given_ok(given):
            ed = re.search(r'(?i)ed(?:ited|\.) by|hg\.|hrsg\.', body[m.end(1):m.start(2)])
            reads.append(dict(names=[norm_name(given, fam)], role='editor' if ed else 'author',
                              title=cut_title(m.group(1)), form='by-after'))
    reads = [r for r in reads if len(re.findall(r'\w+', r['title'])) >= 2]
    if not reads and not isbns:
        return None
    return dict(reads=reads, isbns=isbns)


if __name__ == '__main__':
    for line in sys.stdin:
        print(parse(line.strip()), '<=', line.strip()[:120])
