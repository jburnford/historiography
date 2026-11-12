"""Qualified editor roles in an LC 245 $c statement (ARCHITECTURE.md section 8, class 23; 2026-11-12).

A word before 'editor' that names another job ('Graeme Wynn, cartographic editor', 'picture editor', 'assistant
editor', 'consulting editor') or a part of the book ('maps edited by', 'bibliography edited by', 'series edited by')
means the person did not edit the volume. Shared by scripts/volume_editors.py (printed volume editors) and
scripts/edition_roles.py (the role of an EDITED or AUTHORED credit). No data is read here.
"""
import re

# words before 'editor' that keep the plain editor role (the rest name another job)
# 'chief', 'principal', 'senior', 'special' (a journal issue's guest editors), 'project' (documentary collections),
# 'congress', 'conference', 'proceedings' and 'writer' ('writer-editor') added on 2026-11-12 from the edition_roles.py
# diff and its hand check: the volume's own editors
EDITOR_QUALIFIER_OK = {'co', 'joint', 'volume', 'guest', 'book', 'coordinating', 'director', 'chief', 'principal', 'senior',
                       'special', 'project', 'congress', 'conference', 'proceedings', 'writer', 'y', 'and', 'the', 'others', 'al'}
# series-type qualifiers: scripts/edition_roles.py keeps its 'series-editor' role for these
SERIES_QUALIFIERS = {'consulting', 'general', 'series', 'advisory', 'managing'}
# 'maps edited by', 'series edited by': the verb governs a part of the book, not the volume
NOT_VOLUME_PART = re.compile(r'(?i)\b(series|maps?|cartograph\w*|illustrations?|photographs?|pictures?|plates|music|index|'
                             r'indexes|appendix|appendices|bibliograph\w*|glossary|gazetteer|atlas|charts?|figures)\b')
_STOP = {'and', 'with', 'by', 'of', 'und', 'et', 'y', 'e', '&'}


def tail_qualifiers(before):
    """the lower-case words that end `before` (the text up to a role word): 'Graeme Wynn, cartographic ' ->
    ['cartographic']; 'Jane Roe, co-' -> ['co-']; 'John Smith and Jane Doe, ' -> []"""
    tail = re.search(r'((?:\b[a-z][a-z-]*\s*)+)$', before.rstrip(' ,('))
    return tail.group(1).split() if tail else []


def names_other_job(words):
    """True if a qualifier word before 'editor' names another job (not co-, joint, volume, guest, book, coordinating)"""
    return any(w.strip('-').lower() not in EDITOR_QUALIFIER_OK for w in words)


def words_before(before, n=3):
    """up to n words (any case) directly before a role word with only spaces between, stopping at a conjunction or
    preposition: 'Maps ' -> ['Maps']; 'with maps ' -> ['maps']; 'Mitchell A. McNutt, ' -> []"""
    out = []
    s = before
    while len(out) < n:
        m = re.search(r"([A-Za-z][A-Za-z-]*?)(?:\s+|-)$", s)      # 'Maps ', 'co-'
        if not m or m.group(1).lower() in _STOP:
            break
        out.insert(0, m.group(1))
        s = s[:m.start()]
    return out


def qualified_role(before, role_word):
    """The job a qualified role word gives ('editor' / 'edited' etc. preceded by `before`, the clause text up to it):
    None (plain: the volume's editor), 'series' (consulting, general, series, advisory, managing editor) or 'other'
    (cartographic, picture, assistant, associate, executive, founding ... editor; maps / bibliography / series edited by)."""
    rw = role_word.lower()
    if rw.startswith(('edited', 'compiled')):
        part = NOT_VOLUME_PART.search(' '.join(words_before(before)))
        if not part:
            return None
        return 'series' if part.group(1).lower() == 'series' else 'other'
    q = words_before(before)
    if not names_other_job(q):
        return None
    return 'series' if any(w.lower() in SERIES_QUALIFIERS for w in q) else 'other'
